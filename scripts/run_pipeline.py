"""Run the generate → judge → retry → fallback pipeline on one or more briefs."""

import argparse

from adgen.core.briefs import load_briefs
from adgen.core.llm import LiteLLMClient
from adgen.pipeline import MAX_RETRIES, AdPipeline, Fallback


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("briefs", nargs="+", help="brief ids, e.g. b16 b44")
    parser.add_argument("--max-retries", type=int, default=MAX_RETRIES)
    parser.add_argument("--force-fallback", choices=list(Fallback), help="skip the pass check and exercise a fallback path")
    args = parser.parse_args()

    briefs = load_briefs()
    client = LiteLLMClient()
    for brief_id in args.briefs:
        pipeline = AdPipeline(client, briefs[brief_id], on_attempt=lambda a: print(f"  {a.label:20} fails={a.failures or '-'}"))
        if args.force_fallback:
            pipeline.generate_with_retries(args.max_retries)
            pipeline.apply_fallback(Fallback(args.force_fallback))
            result = pipeline.finish()
        else:
            result = pipeline.run(args.max_retries)
        print(f"{brief_id}: {result.summary}  (${result.cost_usd:.3f}, {len(result.attempts)} attempts) → data/runs/{result.run_id}")


if __name__ == "__main__":
    main()
