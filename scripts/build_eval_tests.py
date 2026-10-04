"""Turn the golden ground truth into promptfoo test cases (evals/tests/{dev,test}.yaml)."""

import yaml

from adgen.core.checks import SCORED_CHECKS
from adgen.core.config import ROOT
from adgen.golden import ground_truth

OUT = ROOT / "evals" / "tests"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = ground_truth.load()
    for split in ("dev", "test"):
        tests = []
        for row in (r for r in rows if r.split == split):
            asserts = [
                {
                    "type": "javascript",
                    "value": f"JSON.parse(output).checks.{check}.verdict === '{truth.verdict}'",
                    "metric": f"{check} · {'catch' if truth.verdict == 'fail' else 'pass'}",
                }
                for check in SCORED_CHECKS
                if (truth := row.scored(check))
            ]
            tests.append(
                {
                    "description": f"{row.item_id} ({row.source})",
                    "vars": {"item_id": row.item_id},
                    "metadata": {"split": split, "source": row.source, "severity": row.severity or ""},
                    "assert": asserts,
                }
            )
        (OUT / f"{split}.yaml").write_text(yaml.safe_dump(tests, sort_keys=False, allow_unicode=True))
        print(f"{split}: {len(tests)} tests, {sum(len(t['assert']) for t in tests)} assertions")


if __name__ == "__main__":
    main()
