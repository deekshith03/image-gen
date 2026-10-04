"""Assemble the golden item list (data/golden/items.yaml) from final ads, earlier-strategy failures and planted edits."""

from collections import Counter
from pathlib import Path

import yaml

from adgen.core.briefs import Brief, load_briefs
from adgen.core.config import DATA, LOCKED_STRATEGY, ROOT
from adgen.golden.items import GOLDEN, ITEMS_PATH, file_sha256, final_item_id

ADS = DATA / "ads"


def item_row(item_id: str, brief: Brief, source: str, image: Path, **extra) -> dict:
    return {
        "item_id": item_id,
        "brief_id": brief.id,
        "product": brief.product.id,
        "split": brief.split,
        "source": source,
        "image": str(image.relative_to(ROOT)),
        "sha256": file_sha256(image) if image.exists() else None,
        **extra,
    }


def main() -> None:
    briefs = load_briefs()
    rows = [item_row(final_item_id(b.id), b, LOCKED_STRATEGY, ADS / "natural" / LOCKED_STRATEGY / f"{b.id}.png") for b in briefs.values()]

    for row in yaml.safe_load((GOLDEN / "earlier_failures.yaml").read_text())["earlier"]:
        image = ADS / "natural" / row["strategy"] / f"{row['brief']}.png"
        rows.append(
            item_row(f"{row['strategy']}-{row['brief']}", briefs[row["brief"]], row["strategy"], image, suspected=row["suspected"], target_checks=row["checks"])
        )

    for spec in yaml.safe_load((GOLDEN / "plant_specs.yaml").read_text())["plants"]:
        image = ADS / "planted" / f"{spec['id']}.png"
        if not image.exists():
            print(f"skipping {spec['id']}: not generated")
            continue
        rows.append(item_row(spec["id"], briefs[spec["base"]], "planted", image, plant={k: spec[k] for k in ("expect", "fails", "severity", "edit")}))

    if missing := [r["item_id"] for r in rows if not (ROOT / r["image"]).exists()]:
        raise SystemExit(f"missing images: {missing}")

    ITEMS_PATH.write_text(yaml.safe_dump({"items": rows}, sort_keys=False, allow_unicode=True, width=200))
    print(f"{len(rows)} items →", dict(Counter(r["source"] for r in rows)))
    print("split:", dict(Counter(r["split"] for r in rows)))


if __name__ == "__main__":
    main()
