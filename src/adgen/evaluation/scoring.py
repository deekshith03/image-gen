from collections import defaultdict
from dataclasses import dataclass, field

from adgen.core.checks import CONTEXT_SUBCHECKS, SCORED_CHECKS, Verdict
from adgen.golden.ground_truth import Basis, TruthRow
from adgen.golden.panel import merge_verdicts

SEVERITIES = ("blatant", "moderate", "subtle")


@dataclass
class Rate:
    hits: int = 0
    total: int = 0

    def add(self, hit: bool) -> None:
        self.hits += hit
        self.total += 1

    @property
    def value(self) -> float | None:
        return self.hits / self.total if self.total else None


@dataclass
class CheckScore:
    catch: Rate = field(default_factory=Rate)
    keep: Rate = field(default_factory=Rate)

    def add(self, expected: Verdict, judged: str) -> None:
        (self.catch if expected == Verdict.FAIL else self.keep).add(judged == expected)


@dataclass(frozen=True)
class Miss:
    item_id: str
    check: str
    expected: Verdict
    judged: str
    reason: str


@dataclass
class Scorecard:
    all: dict[str, CheckScore] = field(default_factory=lambda: defaultdict(CheckScore))
    independent: dict[str, CheckScore] = field(default_factory=lambda: defaultdict(CheckScore))
    severity: dict[str, Rate] = field(default_factory=lambda: defaultdict(Rate))
    misses: list[Miss] = field(default_factory=list)
    unscored: list[str] = field(default_factory=list)


def panel_anchored_checks(labels: dict[str, dict], panel: dict[str, list[dict]]) -> dict[str, set[str]]:
    """Checks where the human kept the expert panel's pre-filled verdict — possibly anchored, so excluded from 'independent'."""
    anchored = {}
    for item_id, label in labels.items():
        if label.get("tier") != 3 or not label.get("prefill_shown"):
            continue
        panel_verdicts = merge_verdicts(panel.get(item_id, []))
        kept = {key for key, check in label["checks"].items() if check["verdict"] == panel_verdicts.get(key)}
        if set(CONTEXT_SUBCHECKS) <= kept:
            kept.add("context")
        anchored[item_id] = kept
    return anchored


def score(truth: list[TruthRow], judged: dict[str, dict], anchored: dict[str, set[str]], base_item_of: dict[str, str]) -> Scorecard:
    card = Scorecard()
    for row in truth:
        result = judged.get(row.item_id)
        if result is None:
            card.unscored.append(row.item_id)
            continue
        for check in SCORED_CHECKS:
            expected = row.scored(check)
            if expected is None:
                continue
            verdict = result["checks"][check]["verdict"]
            source_item = base_item_of[row.item_id] if expected.basis == Basis.INHERITED else row.item_id
            card.all[check].add(expected.verdict, verdict)
            if check not in anchored.get(source_item, set()):
                card.independent[check].add(expected.verdict, verdict)
            if expected.verdict == Verdict.FAIL and row.severity and expected.basis == Basis.GOLD and check != "context":
                card.severity[row.severity].add(verdict == expected.verdict)
            if verdict != expected.verdict:
                card.misses.append(Miss(row.item_id, check, expected.verdict, verdict, result["checks"][check]["reason"]))
    return card
