"""Download the reference product photos listed in data/products/manifest.yaml (brand-copyrighted, git-ignored)."""

import httpx
import yaml

from adgen.core.briefs import PRODUCT_IMAGES
from adgen.core.config import DATA

MANIFEST = DATA / "products" / "manifest.yaml"


def main() -> None:
    PRODUCT_IMAGES.mkdir(parents=True, exist_ok=True)
    products = yaml.safe_load(MANIFEST.read_text())["products"]
    with httpx.Client(timeout=60, follow_redirects=True, headers={"User-Agent": "adgen-research/0.1"}) as client:
        for product in products:
            destination = PRODUCT_IMAGES / f"{product['id']}.jpg"
            if destination.exists():
                continue
            response = client.get(product["url"])
            response.raise_for_status()
            destination.write_bytes(response.content)
            print(f"fetched {product['id']}")
    print(f"{len(products)} products in {PRODUCT_IMAGES.relative_to(DATA.parent)}")


if __name__ == "__main__":
    main()
