import string

import pytest

from adgen.core.config import PROMPTS
from adgen.core.prompts import load_prompt, render_prompt
from adgen.generation.planner import AdPlan
from adgen.generation.prompt import build_image_prompt

EXPECTED_PLACEHOLDERS = {
    "judge_text": set(),
    "judge_product": {"brand", "name"},
    "judge_context": {"geo", "season"},
    "planner": {"geo", "season", "text"},
    "panel": {"geo", "season", "text", "guidelines", "check_lines"},
    "image": {"brand", "name", "text", "scene", "composition", "headline_typography", "headline_placement", "integration"},
    "plant_edit": {"edit"},
    "retry_critique": {"problems"},
    "remove_text_edit": set(),
    "remove_product_edit": set(),
}


def placeholders(template: str) -> set[str]:
    return {field for _, field, _, _ in string.Formatter().parse(template) if field}


def test_every_prompt_file_is_registered():
    assert {path.stem for path in PROMPTS.glob("*.md")} == set(EXPECTED_PLACEHOLDERS)


@pytest.mark.parametrize("name", EXPECTED_PLACEHOLDERS)
def test_prompt_placeholders(name):
    assert placeholders(load_prompt(name)) == EXPECTED_PLACEHOLDERS[name]


def test_render_prompt_accepts_a_name_placeholder():
    rendered = render_prompt("judge_product", brand="Kiehl's", name="Ultra Facial Cream")
    assert "Kiehl's Ultra Facial Cream" in rendered


def test_image_prompt_carries_exact_headline_and_no_faces_rule(brief):
    plan = AdPlan("brand", "a sunlit sandstone ledge", "low angle", "serif caps", "top left", "lit by the scene")
    prompt = build_image_prompt(brief, plan)
    assert f'"{brief.text}"' in prompt
    assert "faces are not visible" in prompt
    assert "{" not in prompt
