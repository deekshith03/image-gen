"""Create planted single-change failures by editing locked D2 ads (specs: data/golden/plant_specs.yaml)."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor

import yaml

from adgen.core.config import DATA, GENERATOR_MODEL, LOCKED_STRATEGY
from adgen.core.llm import LiteLLMClient, fit_to_max_edge
from adgen.core.prompts import render_prompt
from adgen.golden.items import GOLDEN

SPECS = GOLDEN / "plant_specs.yaml"
BASE = DATA / "ads" / "natural" / LOCKED_STRATEGY
OUT = DATA / "ads" / "planted"


def plant(client: LiteLLMClient, spec: dict) -> dict:
    try:
        response = client.generate_image(GENERATOR_MODEL, render_prompt("plant_edit", edit=spec["edit"]), [BASE / f"{spec['base']}.png"])
    except Exception as error:
        print(f"✗ {spec['id']}: {error}")
        return {**spec, "error": str(error)}
    fit_to_max_edge(response.image).save(OUT / f"{spec['id']}.png")
    print(f"✓ {spec['id']} ({spec['expect']}/{spec['severity']}) ${response.cost_usd:.4f}")
    return {**spec, "model": response.model, "cost_usd": response.cost_usd}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    specs = [s for s in yaml.safe_load(SPECS.read_text())["plants"] if not args.only or s["id"] in args.only]
    todo = [s for s in specs if args.force or not (OUT / f"{s['id']}.png").exists()]
    client = LiteLLMClient()
    with ThreadPoolExecutor(max_workers=4) as pool, (OUT / "plants.jsonl").open("a") as log:
        for result in pool.map(lambda spec: plant(client, spec), todo):
            log.write(json.dumps(result) + "\n")


if __name__ == "__main__":
    main()
