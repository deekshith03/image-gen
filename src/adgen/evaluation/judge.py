import re
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from adgen.core.briefs import Brief
from adgen.core.checks import CONTEXT_SUBCHECKS, PIPELINE_GATES, Verdict
from adgen.core.config import JUDGE_MODEL, MAX_EDGE
from adgen.core.llm import LiteLLMClient
from adgen.core.prompts import render_prompt

TYPOGRAPHIC_EQUIVALENTS = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "＄": "$", "％": "%"})


@dataclass(frozen=True)
class CheckResult:
    verdict: Verdict
    reason: str
    details: dict = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        return self.verdict == Verdict.FAIL

    def as_dict(self) -> dict:
        return {"verdict": str(self.verdict), "reason": self.reason, **({"details": self.details} if self.details else {})}


@dataclass(frozen=True)
class Evaluation:
    size: CheckResult
    text: CheckResult
    product: CheckResult
    context: CheckResult
    subchecks: dict[str, CheckResult]
    cost_usd: float

    @property
    def failures(self) -> list[str]:
        return [gate for gate in PIPELINE_GATES if getattr(self, gate).failed]

    @property
    def passed(self) -> bool:
        return not self.failures

    def failed_checks(self) -> dict[str, CheckResult]:
        checks = {"text": self.text, "product": self.product, **self.subchecks}
        return {name: check for name, check in checks.items() if check.failed}

    def as_dict(self) -> dict:
        checks = {gate: getattr(self, gate) for gate in PIPELINE_GATES} | self.subchecks
        return {
            "passed": self.passed,
            "checks": {name: check.as_dict() for name, check in checks.items()},
            "cost_usd": round(self.cost_usd, 5),
        }


def normalise_headline(text: str) -> str:
    return re.sub(r"\s+", "", text.translate(TYPOGRAPHIC_EQUIVALENTS)).upper()


def parse_verdict(data: dict) -> Verdict:
    return Verdict.FAIL if str(data.get("verdict", "")).strip().lower().startswith("fail") else Verdict.PASS


def check_size(ad_path: Path) -> CheckResult:
    width, height = Image.open(ad_path).size
    within = max(width, height) <= MAX_EDGE
    return CheckResult(Verdict.PASS if within else Verdict.FAIL, f"{width}×{height}, long edge {'≤' if within else '>'} {MAX_EDGE}px")


def text_problems(expected: str, transcription: str, garbled_near: str, garbled_scene: str, legibility: str) -> list[str]:
    return [
        *([] if normalise_headline(transcription) == normalise_headline(expected) else [f'reads "{transcription}" instead of "{expected}"']),
        *([f'garbled text near headline: "{garbled_near}"'] if garbled_near else []),
        *([f'prominent garbled scene text: "{garbled_scene}"'] if garbled_scene else []),
        *(["headline illegible"] if legibility == "illegible" else []),
    ]


def check_text(client: LiteLLMClient, brief: Brief, ad_path: Path, model: str = JUDGE_MODEL) -> tuple[CheckResult, float]:
    data, cost = client.chat_json(model, render_prompt("judge_text"), [ad_path])
    transcription = data.get("headline_transcription", "")
    garbled_scene = data.get("prominent_garbled_scene_text", "").strip()
    legibility = data.get("legibility", "clear")
    problems = text_problems(brief.text, transcription, data.get("garbled_text_near_headline", "").strip(), garbled_scene, legibility)
    details = {"transcription": transcription, "legibility": legibility, "scene_garble": garbled_scene, "judge_reason": data.get("reason", "")}
    if problems:
        return CheckResult(Verdict.FAIL, "; ".join(problems), details), cost
    return CheckResult(Verdict.PASS, f'reads exactly "{transcription}"', details), cost


def check_product(client: LiteLLMClient, brief: Brief, ad_path: Path, model: str = JUDGE_MODEL) -> tuple[CheckResult, float]:
    prompt = render_prompt("judge_product", brand=brief.product.brand, name=brief.product.name)
    data, cost = client.chat_json(model, prompt, [brief.product.image_path, ad_path])
    return CheckResult(parse_verdict(data), data.get("reason", ""), {"observations": data.get("observations", {})}), cost


def check_context(client: LiteLLMClient, brief: Brief, ad_path: Path, model: str = JUDGE_MODEL) -> tuple[dict[str, CheckResult], float]:
    data, cost = client.chat_json(model, render_prompt("judge_context", geo=brief.geo, season=brief.season), [ad_path])
    return {name: CheckResult(parse_verdict(data.get(name, {})), data.get(name, {}).get("reason", "")) for name in CONTEXT_SUBCHECKS}, cost


def combine_context(subchecks: dict[str, CheckResult]) -> CheckResult:
    failed = {name: check for name, check in subchecks.items() if check.failed}
    if failed:
        return CheckResult(Verdict.FAIL, "; ".join(f"{name}: {check.reason}" for name, check in failed.items()))
    return CheckResult(Verdict.PASS, "all context checks pass")


def evaluate(client: LiteLLMClient, brief: Brief, ad_path: Path, model: str = JUDGE_MODEL) -> Evaluation:
    text, text_cost = check_text(client, brief, ad_path, model)
    product, product_cost = check_product(client, brief, ad_path, model)
    subchecks, context_cost = check_context(client, brief, ad_path, model)
    return Evaluation(check_size(ad_path), text, product, combine_context(subchecks), subchecks, text_cost + product_cost + context_cost)
