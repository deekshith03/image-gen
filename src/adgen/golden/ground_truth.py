import json
from dataclasses import dataclass

from adgen.core.briefs import Brief
from adgen.core.checks import CONTEXT_SUBCHECKS, CULTURAL_CHECKS, LABELLED_CHECKS, Verdict, combine
from adgen.golden.items import GOLDEN, GoldenItem, Tier
from adgen.golden.labels import ANSWER_TO_VERDICT
from adgen.golden.panel import merge_verdicts

GROUND_TRUTH_PATH = GOLDEN / "ground_truth.jsonl"
INDIA_GEO_MARKER = "India"


class Basis:
    GOLD = "gold"
    SILVER = "silver"
    INHERITED = "inherited"
    COMBINED = "combined"


@dataclass(frozen=True)
class TruthCheck:
    verdict: Verdict
    basis: str


@dataclass(frozen=True)
class TruthRow:
    item_id: str
    brief_id: str
    split: str
    source: str
    severity: str | None
    checks: dict[str, TruthCheck]

    def scored(self, check: str) -> TruthCheck | None:
        truth = self.checks.get(check)
        return truth if truth and truth.verdict in (Verdict.PASS, Verdict.FAIL) else None


def is_india(brief: Brief) -> bool:
    return INDIA_GEO_MARKER in brief.geo


def final_ad_checks(label: dict, panel_reviews: list[dict], brief: Brief) -> dict[str, dict]:
    panel_verdicts = merge_verdicts(panel_reviews)
    checks = {}
    for key in LABELLED_CHECKS:
        verdict = label["checks"][key]["verdict"]
        confirmed_panel = key in CULTURAL_CHECKS and not is_india(brief) and label.get("prefill_shown") and verdict == panel_verdicts[key]
        checks[key] = {"verdict": verdict, "basis": Basis.SILVER if confirmed_panel else Basis.GOLD}
    return checks


def derive(items: dict[str, GoldenItem], labels: dict[str, dict], panel: dict[str, list[dict]], briefs: dict[str, Brief]) -> dict[str, dict]:
    truth: dict[str, dict] = {}
    for item_id, item in items.items():
        if item.tier == Tier.FINAL:
            label = labels[item_id]
            truth[item_id] = {
                "checks": final_ad_checks(label, panel.get(item_id, []), briefs[item.brief_id]),
                "visual_integrity": label.get("visual_integrity"),
                "appeal": label.get("appeal"),
            }

    for item_id, item in items.items():
        if item.tier == Tier.FINAL:
            continue
        verdict = ANSWER_TO_VERDICT[labels[item_id]["answer"]]
        if item.tier == Tier.PLANTED:
            checks = {key: {**check, "basis": Basis.INHERITED} for key, check in truth[item.base_item_id]["checks"].items()}
            checks |= {key: {"verdict": verdict, "basis": Basis.GOLD} for key in item.plant.fails}
        else:
            checks = {key: {"verdict": verdict, "basis": Basis.GOLD} for key in item.target_checks}
        truth[item_id] = {"checks": checks}

    for row in truth.values():
        subchecks = [row["checks"][key]["verdict"] for key in CONTEXT_SUBCHECKS if key in row["checks"]]
        if subchecks:
            row["checks"]["context"] = {"verdict": combine(subchecks), "basis": Basis.COMBINED}
    return truth


def write(items: dict[str, GoldenItem], truth: dict[str, dict]) -> None:
    with GROUND_TRUTH_PATH.open("w") as handle:
        for item_id, item in items.items():
            row = {
                "item_id": item_id,
                "brief_id": item.brief_id,
                "split": item.split,
                "source": item.source,
                "severity": item.plant.severity if item.plant else None,
                **truth[item_id],
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load(path=GROUND_TRUTH_PATH) -> list[TruthRow]:
    rows = []
    for line in path.read_text().splitlines():
        data = json.loads(line)
        rows.append(
            TruthRow(
                item_id=data["item_id"],
                brief_id=data["brief_id"],
                split=data["split"],
                source=data["source"],
                severity=data["severity"],
                checks={key: TruthCheck(Verdict(check["verdict"]), check["basis"]) for key, check in data["checks"].items()},
            )
        )
    return rows
