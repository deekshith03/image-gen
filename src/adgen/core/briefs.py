from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import yaml

from adgen.core.config import DATA

PRODUCT_IMAGES = DATA / "products" / "images"


@dataclass(frozen=True)
class Product:
    id: str
    brand: str
    name: str
    category: str
    split: str
    risk: str

    @property
    def image_path(self) -> Path:
        return PRODUCT_IMAGES / f"{self.id}.jpg"


@dataclass(frozen=True)
class Brief:
    id: str
    product: Product
    split: str
    geo: str
    season: str
    text: str
    tags: tuple[str, ...] = field(default_factory=tuple)


@cache
def load_products() -> dict[str, Product]:
    rows = yaml.safe_load((DATA / "products" / "manifest.yaml").read_text())["products"]
    return {
        row["id"]: Product(
            id=row["id"],
            brand=row["brand"],
            name=row["name"],
            category=row["category"],
            split=row["split"],
            risk=row["risk"],
        )
        for row in rows
    }


@cache
def load_briefs() -> dict[str, Brief]:
    products = load_products()
    rows = yaml.safe_load((DATA / "briefs.yaml").read_text())["briefs"]
    return {
        row["id"]: Brief(
            id=row["id"],
            product=products[row["product"]],
            split=row["split"],
            geo=row["geo"],
            season=str(row["season"]),
            text=row["text"],
            tags=tuple(row.get("tags", [])),
        )
        for row in rows
    }
