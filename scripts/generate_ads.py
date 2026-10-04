"""Generate one natural ad per brief with the locked D2 strategy."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

from adgen.core.briefs import load_briefs
from adgen.core.config import DATA, LOCKED_STRATEGY
from adgen.core.llm import LiteLLMClient
from adgen.generation.generator import generate_ad

OUT = DATA / "ads" / "natural" / LOCKED_STRATEGY


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="*", help="brief ids to generate (default: all)")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--force", action="store_true", help="regenerate existing ads")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    briefs = [b for b in load_briefs().values() if not args.only or b.id in args.only]
    todo = [b for b in briefs if args.force or not (OUT / f"{b.id}.png").exists()]
    print(f"{len(todo)} to generate ({len(briefs) - len(todo)} already exist)")

    client = LiteLLMClient()
    total_cost = 0.0
    with ThreadPoolExecutor(max_workers=args.workers) as pool, (OUT / "generations.jsonl").open("a") as log:
        futures = {pool.submit(generate_ad, client, brief): brief for brief in todo}
        for future in as_completed(futures):
            brief = futures[future]
            try:
                gen = future.result()
            except Exception as error:
                print(f"✗ {brief.id}: {error}")
                log.write(json.dumps({"brief_id": brief.id, "error": str(error)}) + "\n")
                continue
            gen.image.save(OUT / f"{brief.id}.png")
            total_cost += gen.cost_usd
            log.write(
                json.dumps(
                    {
                        "brief_id": gen.brief_id,
                        "prompt_version": LOCKED_STRATEGY,
                        "model": gen.model,
                        "cost_usd": gen.cost_usd,
                        "latency_s": gen.latency_s,
                        "raw_size": gen.raw_size,
                        "saved_size": gen.image.size,
                        "prompt": gen.prompt,
                        "plan": gen.plan.as_dict(),
                        "created_at": datetime.now(UTC).isoformat(),
                    }
                )
                + "\n"
            )
            log.flush()
            print(f"✓ {brief.id} {gen.image.size} {gen.latency_s}s ${gen.cost_usd:.4f}")
    print(f"total cost ${total_cost:.3f}")


if __name__ == "__main__":
    main()
