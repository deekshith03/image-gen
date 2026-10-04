import hashlib
import json
import os
from pathlib import Path

from adgen.core.briefs import load_briefs
from adgen.core.config import DATA, JUDGE_MODEL
from adgen.core.llm import LiteLLMClient
from adgen.core.prompts import load_prompt
from adgen.evaluation.judge import evaluate
from adgen.golden.items import load_items

RUNS = DATA / "evals" / "runs"
FROZEN_JUDGE_PROMPT_VERSION = "f5089f81"
ALLOW_TEST_RERUN = "ALLOW_TEST_RERUN"
JUDGE_PROMPTS = ("judge_text", "judge_product", "judge_context")
PROMPT_VERSION = hashlib.sha256("".join(load_prompt(name) for name in JUDGE_PROMPTS).encode()).hexdigest()[:8]


def run_dir(model: str = JUDGE_MODEL, prompt_version: str | None = None) -> Path:
    return RUNS / model.replace("/", "_") / (prompt_version or PROMPT_VERSION)


def load_result(item_id: str, model: str = JUDGE_MODEL) -> dict | None:
    path = run_dir(model) / f"{item_id}.json"
    return json.loads(path.read_text()) if path.exists() else None


def evaluate_item(item_id: str, model: str = JUDGE_MODEL) -> dict:
    if cached := load_result(item_id, model):
        return cached
    item = load_items()[item_id]
    if item.split == "test" and PROMPT_VERSION != FROZEN_JUDGE_PROMPT_VERSION and not os.environ.get(ALLOW_TEST_RERUN):
        raise RuntimeError(
            f"refusing to judge test item {item_id} with changed judge prompts ({PROMPT_VERSION}); the test split was scored once "
            f"with {FROZEN_JUDGE_PROMPT_VERSION}. Tune on dev, or set {ALLOW_TEST_RERUN}=1 and report the rerun separately."
        )
    brief = load_briefs()[item.brief_id]
    result = {"item_id": item_id, "model": model, "prompt_version": PROMPT_VERSION, **evaluate(LiteLLMClient(), brief, item.image, model).as_dict()}
    path = run_dir(model) / f"{item_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return result
