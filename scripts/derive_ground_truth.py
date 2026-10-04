"""Derive per-check ground truth (gold / silver / inherited / combined) from human labels → data/golden/ground_truth.jsonl."""

from collections import Counter

from adgen.core.briefs import load_briefs
from adgen.core.checks import SCORED_CHECKS
from adgen.golden import ground_truth
from adgen.golden.items import load_items
from adgen.golden.labels import load_labels
from adgen.golden.panel import load_panel


def main() -> None:
    items = load_items()
    truth = ground_truth.derive(items, load_labels(), load_panel(), load_briefs())
    ground_truth.write(items, truth)
    print(f"wrote {len(truth)} items → {ground_truth.GROUND_TRUTH_PATH.name}")
    for split in ("dev", "test"):
        print(f"\n{split}:")
        for check in SCORED_CHECKS:
            counts = Counter(row["checks"][check]["verdict"] for item_id, row in truth.items() if items[item_id].split == split and check in row["checks"])
            scored = counts["pass"] + counts["fail"]
            print(f"  {check:11} pass {counts['pass']:3}  fail {counts['fail']:3}  unsure {counts['unsure']:2}  → fail rate {counts['fail'] / scored:.0%}")


if __name__ == "__main__":
    main()
