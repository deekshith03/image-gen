"""Score cached judge runs against the golden ground truth: catch / pass rates per check, independent subset, severity, misses."""

import argparse

from adgen.core.checks import SCORED_CHECKS
from adgen.core.config import JUDGE_MODEL
from adgen.evaluation.cache import PROMPT_VERSION, load_result
from adgen.evaluation.scoring import SEVERITIES, Rate, panel_anchored_checks, score
from adgen.golden import ground_truth
from adgen.golden.items import load_items
from adgen.golden.labels import load_labels
from adgen.golden.panel import load_panel


def fmt(rate: Rate) -> str:
    return f"{rate.value:5.0%} ({rate.hits}/{rate.total})" if rate.total else "    –      "


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="dev")
    parser.add_argument("--model", default=JUDGE_MODEL)
    parser.add_argument("--show-misses", action="store_true")
    args = parser.parse_args()

    truth = [row for row in ground_truth.load() if row.split == args.split]
    judged = {row.item_id: result for row in truth if (result := load_result(row.item_id, args.model))}
    items = load_items()
    card = score(truth, judged, panel_anchored_checks(load_labels(), load_panel()), {i: item.base_item_id for i, item in items.items()})

    print(f"judge {args.model} · prompts {PROMPT_VERSION} · split {args.split} · {len(judged)} items scored")
    if card.unscored:
        print(f"⚠ no result yet for {len(card.unscored)} items: {card.unscored[:8]}…")
    for name, scores in (("all", card.all), ("independent", card.independent)):
        print(f"\n{name.upper():12}  {'catch rate (true fails flagged)':32} {'pass rate (true passes kept)':28}")
        for check in SCORED_CHECKS:
            print(f"  {check:11} {fmt(scores[check].catch):32} {fmt(scores[check].keep)}")
    print("\nCATCH RATE BY SEVERITY (planted items, targeted check)")
    for severity in SEVERITIES:
        print(f"  {severity:9} {fmt(card.severity[severity])}")
    if args.show_misses:
        print("\nMISSES")
        for miss in sorted(card.misses, key=lambda m: (m.item_id, m.check)):
            print(f"  {miss.item_id:9} {miss.check:11} label={miss.expected:4} judge={miss.judged:4} | {miss.reason[:120]}")


if __name__ == "__main__":
    main()
