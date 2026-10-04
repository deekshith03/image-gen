from dataclasses import dataclass

from adgen.core.briefs import Brief
from adgen.core.config import PLANNER_MODEL
from adgen.core.llm import LiteLLMClient
from adgen.core.prompts import render_prompt


@dataclass(frozen=True)
class AdPlan:
    brand_read: str
    scene: str
    composition: str
    headline_typography: str
    headline_placement: str
    integration: str
    cost_usd: float = 0.0

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "cost_usd"}

    @classmethod
    def from_dict(cls, data: dict, cost_usd: float = 0.0) -> "AdPlan":
        fields = cls.__dataclass_fields__.keys() - {"cost_usd"}
        return cls(**{k: str(data.get(k, "")) for k in fields}, cost_usd=cost_usd)


def plan_ad(client: LiteLLMClient, brief: Brief, model: str = PLANNER_MODEL) -> AdPlan:
    prompt = render_prompt("planner", geo=brief.geo, season=brief.season, text=brief.text)
    data, cost = client.chat_json(model, prompt, [brief.product.image_path])
    return AdPlan.from_dict(data, cost)
