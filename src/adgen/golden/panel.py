import json
from pathlib import Path

from adgen.core.briefs import Brief
from adgen.core.checks import LABELLED_CHECKS, Verdict
from adgen.core.config import ROOT
from adgen.core.llm import LiteLLMClient
from adgen.core.prompts import render_prompt
from adgen.golden.items import GOLDEN

PANEL_PATH = GOLDEN / "panel.jsonl"
PANEL_GUIDELINES = ROOT / "docs" / "panel_guidelines.md"


def build_panel_prompt(brief: Brief) -> str:
    check_lines = ",\n".join(f'    "{key}": {{"reason": "...", "verdict": "pass|fail|unsure"}}' for key in LABELLED_CHECKS)
    return render_prompt(
        "panel",
        geo=brief.geo,
        season=brief.season,
        text=brief.text,
        guidelines=PANEL_GUIDELINES.read_text(),
        check_lines=check_lines,
    )


def review(client: LiteLLMClient, model: str, brief: Brief, ad_path: Path) -> tuple[dict, float]:
    return client.chat_json(model, build_panel_prompt(brief), [brief.product.image_path, ad_path])


def merge_verdicts(reviews: list[dict]) -> dict[str, Verdict]:
    merged = {}
    for key in LABELLED_CHECKS:
        verdicts = {review.get("checks", {}).get(key, {}).get("verdict") for review in reviews}
        agreed = verdicts.pop() if len(verdicts) == 1 else None
        merged[key] = Verdict(agreed) if agreed in set(Verdict) else Verdict.UNSURE
    return merged


def load_panel() -> dict[str, list[dict]]:
    if not PANEL_PATH.exists():
        return {}
    reviews: dict[str, list[dict]] = {}
    for line in PANEL_PATH.read_text().splitlines():
        row = json.loads(line)
        if "review" in row:
            reviews.setdefault(row["item_id"], []).append({"model": row["model"], **row["review"]})
    return reviews
