from dataclasses import dataclass, replace

from PIL import Image

from adgen.core.briefs import Brief
from adgen.core.config import GENERATOR_MODEL
from adgen.core.llm import LiteLLMClient, fit_to_max_edge
from adgen.generation.planner import AdPlan, plan_ad
from adgen.generation.prompt import build_image_prompt


@dataclass(frozen=True)
class Generation:
    brief_id: str
    image: Image.Image
    prompt: str
    model: str
    cost_usd: float
    latency_s: float
    raw_size: tuple[int, int]
    plan: AdPlan | None = None


def render(client: LiteLLMClient, brief: Brief, prompt: str, model: str = GENERATOR_MODEL) -> Generation:
    response = client.generate_image(model, prompt, [brief.product.image_path])
    return Generation(
        brief_id=brief.id,
        image=fit_to_max_edge(response.image),
        prompt=prompt,
        model=response.model,
        cost_usd=response.cost_usd,
        latency_s=response.latency_s,
        raw_size=response.image.size,
    )


def generate_ad(client: LiteLLMClient, brief: Brief) -> Generation:
    plan = plan_ad(client, brief)
    generation = render(client, brief, build_image_prompt(brief, plan))
    return replace(generation, plan=plan, cost_usd=generation.cost_usd + plan.cost_usd)
