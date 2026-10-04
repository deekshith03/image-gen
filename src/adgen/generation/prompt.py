from adgen.core.briefs import Brief
from adgen.core.prompts import render_prompt
from adgen.generation.planner import AdPlan


def build_image_prompt(brief: Brief, plan: AdPlan) -> str:
    return render_prompt(
        "image",
        brand=brief.product.brand,
        name=brief.product.name,
        text=brief.text,
        scene=plan.scene,
        composition=plan.composition,
        headline_typography=plan.headline_typography,
        headline_placement=plan.headline_placement,
        integration=plan.integration,
    )
