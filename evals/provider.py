import json

from adgen.core.config import JUDGE_MODEL
from adgen.evaluation.cache import evaluate_item


def call_api(prompt, options, context):
    model = (options.get("config") or {}).get("model", JUDGE_MODEL)
    result = evaluate_item(context["vars"]["item_id"], model)
    return {"output": json.dumps(result, ensure_ascii=False), "cost": result.get("cost_usd", 0)}
