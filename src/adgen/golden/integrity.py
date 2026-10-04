import json
from collections import defaultdict
from dataclasses import dataclass, field

from adgen.core.briefs import load_briefs
from adgen.core.checks import LABELLED_CHECKS
from adgen.evaluation.cache import FROZEN_JUDGE_PROMPT_VERSION, PROMPT_VERSION, load_result
from adgen.golden import ground_truth
from adgen.golden.items import file_sha256, load_items
from adgen.golden.labels import load_labels
from adgen.golden.panel import load_panel


@dataclass
class Report:
    defects: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def check(self, ok: bool, defect: str) -> None:
        if not ok:
            self.defects.append(defect)


def verify() -> Report:
    report = Report()
    items, briefs, labels = load_items(), load_briefs(), load_labels()

    unlabelled = [i for i in items if i not in labels]
    report.check(not unlabelled, f"{len(unlabelled)} items have no label: {unlabelled[:5]}")

    splits_per_product = defaultdict(set)
    for brief in briefs.values():
        splits_per_product[brief.product.id].add(brief.split)
        report.check(brief.split == brief.product.split, f"brief {brief.id} split {brief.split} ≠ product split {brief.product.split}")
    leaked = [p for p, splits in splits_per_product.items() if len(splits) > 1]
    report.check(not leaked, f"products in both dev and test: {leaked}")
    report.check(all(item.split == briefs[item.brief_id].split for item in items.values()), "an item's split differs from its brief's split")

    for item in items.values():
        if item.plant:
            report.check(set(item.plant.fails) <= set(LABELLED_CHECKS), f"{item.item_id}: unknown planted check {item.plant.fails}")
        report.check(bool(item.sha256), f"{item.item_id}: no sha256 recorded")

    present = [item for item in items.values() if item.image.exists()]
    mismatched = [item.item_id for item in present if file_sha256(item.image) != item.sha256]
    report.check(not mismatched, f"images differ from their recorded sha256: {mismatched}")
    report.notes.append(
        f"images present and hash-verified: {len(present) - len(mismatched)}/{len(items)} (the rest are not redistributed — docs/data_sources.md)"
    )

    if not unlabelled:
        derived = ground_truth.derive(items, labels, load_panel(), briefs)
        rows = [json.loads(line) for line in ground_truth.GROUND_TRUTH_PATH.read_text().splitlines()]
        committed = {row["item_id"]: row for row in rows}
        drift = [i for i in items if committed.get(i, {}).get("checks") != json.loads(json.dumps(derived[i]["checks"]))]
        report.check(not drift, f"ground_truth.jsonl does not re-derive from the labels for {len(drift)} items: {drift[:5]}")

    report.check(
        PROMPT_VERSION == FROZEN_JUDGE_PROMPT_VERSION,
        f"judge prompts changed: version {PROMPT_VERSION}, results were produced with {FROZEN_JUDGE_PROMPT_VERSION}",
    )
    missing_results = [i for i in items if load_result(i) is None]
    report.check(not missing_results, f"{len(missing_results)} items have no committed judge result: {missing_results[:5]}")
    report.notes.append(f"judge results for prompt version {PROMPT_VERSION}: {len(items) - len(missing_results)}/{len(items)}")
    return report
