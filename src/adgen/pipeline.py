import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from PIL import Image

from adgen.core.briefs import Brief
from adgen.core.config import DATA, GENERATOR_MODEL
from adgen.core.llm import LiteLLMClient, fit_to_max_edge
from adgen.core.prompts import load_prompt, render_prompt
from adgen.evaluation.judge import Evaluation, evaluate
from adgen.generation.compositor import composite_product, overlay_headline, product_cutout
from adgen.generation.generator import render
from adgen.generation.planner import AdPlan, plan_ad
from adgen.generation.prompt import build_image_prompt

MAX_RETRIES = 2
RUNS = DATA / "runs"
COMPOSITE_HEIGHT = {"jewellery": 0.28, "watch": 0.38, "illusion_mirror": 0.38}
DEFAULT_COMPOSITE_HEIGHT = 0.48


class Fallback(StrEnum):
    OVERLAY = "overlay"
    COMPOSITE = "composite"


class Outcome(StrEnum):
    PASSED = "passed"
    PASSED_AFTER_RETRY = "passed after retry"
    FALLBACK_OVERLAY = "fallback: headline overlaid with a real font"
    FALLBACK_COMPOSITE = "fallback: real product composited + headline overlaid"
    FLAGGED = "flagged: best attempt delivered, context still failing"


@dataclass
class Attempt:
    label: str
    image_path: Path
    evaluation: Evaluation
    cost_usd: float

    @property
    def failures(self) -> list[str]:
        return self.evaluation.failures


@dataclass
class PipelineResult:
    run_id: str
    brief: Brief
    attempts: list[Attempt] = field(default_factory=list)
    final: Attempt | None = None
    outcome: Outcome | None = None

    @property
    def cost_usd(self) -> float:
        return sum(attempt.cost_usd for attempt in self.attempts)

    @property
    def retries(self) -> int:
        return sum(attempt.label.startswith("retry") for attempt in self.attempts)

    @property
    def summary(self) -> str:
        text = str(self.outcome)
        if self.outcome == Outcome.PASSED_AFTER_RETRY:
            text = f"passed after {self.retries} retr{'y' if self.retries == 1 else 'ies'}"
        still_failing = self.final.failures if self.final and self.outcome != Outcome.FLAGGED else []
        return text + (f" — still failing {', '.join(still_failing)} (flagged)" if still_failing else "")


def critique(evaluation: Evaluation) -> str:
    problems = "\n- ".join(f"{name}: {check.reason}" for name, check in evaluation.failed_checks().items())
    return render_prompt("retry_critique", problems=problems)


def best_attempt(attempts: list[Attempt]) -> Attempt:
    return min(attempts, key=lambda a: (len(a.failures), "product" in a.failures, "text" in a.failures))


def choose_fallback(attempt: Attempt) -> Fallback | None:
    if "product" in attempt.failures:
        return Fallback.COMPOSITE
    if "text" in attempt.failures:
        return Fallback.OVERLAY
    return None


class AdPipeline:
    def __init__(self, client: LiteLLMClient, brief: Brief, on_attempt: Callable[[Attempt], None] | None = None):
        self.client = client
        self.brief = brief
        self.on_attempt = on_attempt
        run_id = f"{datetime.now(UTC):%Y%m%d-%H%M%S}-{brief.id}-{uuid.uuid4().hex[:4]}"
        self.result = PipelineResult(run_id, brief)
        self.out = RUNS / run_id
        self.out.mkdir(parents=True, exist_ok=True)
        self.plan: AdPlan | None = None

    def run(self, max_retries: int = MAX_RETRIES) -> PipelineResult:
        if passed := self.generate_with_retries(max_retries):
            self.result.final = passed
            self.result.outcome = Outcome.PASSED if passed.label == "generate" else Outcome.PASSED_AFTER_RETRY
        else:
            self.apply_fallback(choose_fallback(best_attempt(self.result.attempts)))
        return self.finish()

    def generate_with_retries(self, max_retries: int) -> Attempt | None:
        self.plan = plan_ad(self.client, self.brief)
        base_prompt = build_image_prompt(self.brief, self.plan)
        prompt = base_prompt
        for number in range(max_retries + 1):
            generation = render(self.client, self.brief, prompt)
            setup_cost = self.plan.cost_usd if number == 0 else 0.0
            attempt = self.record("generate" if number == 0 else f"retry{number}", generation.image, generation.cost_usd + setup_cost)
            if not attempt.failures:
                return attempt
            prompt = f"{base_prompt}\n\n{critique(attempt.evaluation)}"
        return None

    def apply_fallback(self, fallback: Fallback | None) -> None:
        best = best_attempt(self.result.attempts)
        if fallback == Fallback.COMPOSITE:
            plate = self.client.generate_image(GENERATOR_MODEL, load_prompt("remove_product_edit"), [best.image_path])
            height = COMPOSITE_HEIGHT.get(self.brief.product.category, DEFAULT_COMPOSITE_HEIGHT)
            composed, product_box = composite_product(plate.image, product_cutout(self.brief.product.image_path), height)
            image = overlay_headline(composed, self.brief.text, self.plan.headline_typography, avoid=product_box)
            self.result.final = self.record("fallback_composite", image, plate.cost_usd)
            self.result.outcome = Outcome.FALLBACK_COMPOSITE
        elif fallback == Fallback.OVERLAY:
            clean = self.client.generate_image(GENERATOR_MODEL, load_prompt("remove_text_edit"), [best.image_path])
            image = overlay_headline(clean.image, self.brief.text, self.plan.headline_typography)
            self.result.final = self.record("fallback_overlay", image, clean.cost_usd)
            self.result.outcome = Outcome.FALLBACK_OVERLAY
        else:
            self.result.final = best
            self.result.outcome = Outcome.FLAGGED

    def record(self, label: str, image: Image.Image, generation_cost: float) -> Attempt:
        path = self.out / f"{len(self.result.attempts):02d}_{label}.png"
        fit_to_max_edge(image).save(path)
        evaluation = evaluate(self.client, self.brief, path)
        attempt = Attempt(label, path, evaluation, generation_cost + evaluation.cost_usd)
        self.result.attempts.append(attempt)
        if self.on_attempt:
            self.on_attempt(attempt)
        return attempt

    def finish(self) -> PipelineResult:
        result, brief = self.result, self.brief
        trace = {
            "run_id": result.run_id,
            "brief": {"id": brief.id, "product": brief.product.id, "geo": brief.geo, "season": brief.season, "text": brief.text},
            "outcome": result.summary,
            "final": result.final.image_path.name if result.final else None,
            "cost_usd": round(result.cost_usd, 4),
            "attempts": [
                {"label": a.label, "image": a.image_path.name, "failures": a.failures, "cost_usd": round(a.cost_usd, 4), **a.evaluation.as_dict()}
                for a in result.attempts
            ],
        }
        (self.out / "trace.json").write_text(json.dumps(trace, indent=2, ensure_ascii=False))
        return result


def run_pipeline(client: LiteLLMClient, brief: Brief, on_attempt: Callable[[Attempt], None] | None = None, max_retries: int = MAX_RETRIES) -> PipelineResult:
    return AdPipeline(client, brief, on_attempt).run(max_retries)
