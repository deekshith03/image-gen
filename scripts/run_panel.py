"""Expert panel (Claude Opus + GPT) pre-labels for golden items — used as labelling pre-fill and silver labels."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor

from adgen.core.briefs import load_briefs
from adgen.core.config import LOCKED_STRATEGY, PANEL_MODELS
from adgen.core.llm import LiteLLMClient
from adgen.golden.items import load_items
from adgen.golden.panel import PANEL_PATH, review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", nargs="*", default=[LOCKED_STRATEGY])
    args = parser.parse_args()

    briefs = load_briefs()
    done = set()
    if PANEL_PATH.exists():
        done = {(r["item_id"], r["model"]) for r in map(json.loads, PANEL_PATH.read_text().splitlines()) if "review" in r}
    jobs = [(item, model) for item in load_items().values() if item.source in args.sources for model in PANEL_MODELS if (item.item_id, model) not in done]
    print(f"{len(jobs)} panel reviews to run")

    client = LiteLLMClient()

    def run(job):
        item, model = job
        try:
            data, cost = review(client, model, briefs[item.brief_id], item.image)
            return {"item_id": item.item_id, "model": model, "review": data, "cost_usd": cost}
        except Exception as error:
            return {"item_id": item.item_id, "model": model, "error": str(error)[:300]}

    with ThreadPoolExecutor(max_workers=6) as pool, PANEL_PATH.open("a") as log:
        for result in pool.map(run, jobs):
            log.write(json.dumps(result, ensure_ascii=False) + "\n")
            log.flush()
            print("✓" if "review" in result else "✗", result["item_id"], result["model"])


if __name__ == "__main__":
    main()
