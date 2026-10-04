import hashlib
import random
import re
from dataclasses import dataclass
from enum import IntEnum
from functools import cache
from pathlib import Path

import yaml

from adgen.core.config import DATA, LOCKED_STRATEGY, ROOT

GOLDEN = DATA / "golden"
ITEMS_PATH = GOLDEN / "items.yaml"
BLIND_SAMPLE_SIZE = 10
BLIND_SEED = 11


class Tier(IntEnum):
    PLANTED = 1
    EARLIER = 2
    FINAL = 3


@dataclass(frozen=True)
class Plant:
    expect: str
    fails: tuple[str, ...]
    severity: str
    edit: str


@dataclass(frozen=True)
class GoldenItem:
    item_id: str
    brief_id: str
    product: str
    split: str
    source: str
    image: Path
    plant: Plant | None = None
    suspected: str | None = None
    target_checks: tuple[str, ...] = ()
    sha256: str | None = None

    @property
    def tier(self) -> Tier:
        if self.source == "planted":
            return Tier.PLANTED
        if self.source == LOCKED_STRATEGY:
            return Tier.FINAL
        return Tier.EARLIER

    @property
    def base_item_id(self) -> str:
        return final_item_id(self.brief_id) if self.tier == Tier.PLANTED else self.item_id

    @property
    def question(self) -> str:
        if self.plant:
            return f"Did this change actually happen? — {change_description(self.plant.edit)}"
        return f"Is this suspected issue real? — {self.suspected}"


def final_item_id(brief_id: str) -> str:
    return f"{LOCKED_STRATEGY}-{brief_id}"


def change_description(edit: str) -> str:
    return re.split(r" (?=Keep |Change nothing)", edit, maxsplit=1)[0]


@cache
def load_items() -> dict[str, GoldenItem]:
    items = {}
    for row in yaml.safe_load(ITEMS_PATH.read_text())["items"]:
        plant = row.get("plant")
        items[row["item_id"]] = GoldenItem(
            item_id=row["item_id"],
            brief_id=row["brief_id"],
            product=row["product"],
            split=row["split"],
            source=row["source"],
            image=ROOT / row["image"],
            plant=Plant(plant["expect"], tuple(plant["fails"]), plant["severity"], plant["edit"]) if plant else None,
            suspected=row.get("suspected"),
            target_checks=tuple(row.get("target_checks") or ()),
            sha256=row.get("sha256"),
        )
    return items


def blind_item_ids(items: dict[str, GoldenItem]) -> set[str]:
    final = sorted(item_id for item_id, item in items.items() if item.tier == Tier.FINAL)
    return set(random.Random(BLIND_SEED).sample(final, BLIND_SAMPLE_SIZE))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
