import json
from datetime import UTC, datetime

from adgen.core.checks import Verdict
from adgen.golden.items import GOLDEN

LABELS_PATH = GOLDEN / "labels.jsonl"
ANSWERS = ("yes", "no", "unclear")
ANSWER_TO_VERDICT = {"yes": Verdict.FAIL, "no": Verdict.PASS, "unclear": Verdict.UNSURE}


def load_labels() -> dict[str, dict]:
    if not LABELS_PATH.exists():
        return {}
    latest: dict[str, dict] = {}
    for line in LABELS_PATH.read_text().splitlines():
        if line.strip():
            label = json.loads(line)
            latest[label["item_id"]] = label
    return latest


def save_label(label: dict) -> None:
    LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamped = {**label, "labelled_at": datetime.now(UTC).isoformat()}
    with LABELS_PATH.open("a") as handle:
        handle.write(json.dumps(stamped, ensure_ascii=False) + "\n")
