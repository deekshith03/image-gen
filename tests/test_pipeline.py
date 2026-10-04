from pathlib import Path

from PIL import Image

import adgen.pipeline as pipeline
from adgen.generation.generator import Generation
from adgen.generation.planner import AdPlan
from adgen.pipeline import AdPipeline, Attempt, Fallback, Outcome, best_attempt, choose_fallback, critique
from tests.conftest import make_evaluation


def attempt(label: str = "generate", **failing: str) -> Attempt:
    return Attempt(label, Path(f"{label}.png"), make_evaluation(failing), 0.1)


def test_critique_lists_every_failed_check():
    text = critique(make_evaluation({"text": 'reads "LAGOS LAGOS MOVES"', "no_cliche": "sepia filter"}))
    assert text.startswith("The previous attempt had these problems")
    assert '- text: reads "LAGOS LAGOS MOVES"' in text and "- no_cliche: sepia filter" in text


def test_choose_fallback_prefers_product_then_text():
    assert choose_fallback(attempt(product="recoloured", text="typo")) == Fallback.COMPOSITE
    assert choose_fallback(attempt(text="typo")) == Fallback.OVERLAY
    assert choose_fallback(attempt(season_fit="snow")) is None


def test_best_attempt_minimises_failures_then_avoids_product():
    product_fail, text_fail, both = attempt("a", product="x"), attempt("b", text="y"), attempt("c", text="y", product="x")
    assert best_attempt([both, product_fail, text_fail]) is text_fail


def test_pipeline_retries_with_critique_until_it_passes(tmp_path, monkeypatch, brief):
    plan = AdPlan("brand", "scene", "composition", "serif", "top left", "lit")
    evaluations = iter([make_evaluation({"text": "typo"}), make_evaluation()])
    prompts = []

    def fake_render(client, brief, prompt):
        prompts.append(prompt)
        return Generation(brief.id, Image.new("RGB", (64, 64)), prompt, "gemini", 0.07, 1.0, (64, 64))

    monkeypatch.setattr(pipeline, "RUNS", tmp_path)
    monkeypatch.setattr(pipeline, "plan_ad", lambda client, brief: plan)
    monkeypatch.setattr(pipeline, "render", fake_render)
    monkeypatch.setattr(pipeline, "evaluate", lambda client, brief, path: next(evaluations))

    result = AdPipeline(client=None, brief=brief).run(max_retries=2)

    assert result.outcome == Outcome.PASSED_AFTER_RETRY and result.summary == "passed after 1 retry"
    assert [a.label for a in result.attempts] == ["generate", "retry1"]
    assert "- text: typo" in prompts[1] and "previous attempt" not in prompts[0]
    assert (tmp_path / result.run_id / "trace.json").exists()


def test_pipeline_flags_when_only_context_keeps_failing(tmp_path, monkeypatch, brief):
    monkeypatch.setattr(pipeline, "RUNS", tmp_path)
    monkeypatch.setattr(pipeline, "plan_ad", lambda client, brief: AdPlan("", "", "", "", "", ""))
    monkeypatch.setattr(pipeline, "render", lambda client, brief, prompt: Generation(brief.id, Image.new("RGB", (8, 8)), prompt, "m", 0.0, 0.0, (8, 8)))
    monkeypatch.setattr(pipeline, "evaluate", lambda client, brief, path: make_evaluation({"season_fit": "snow"}))

    result = AdPipeline(client=None, brief=brief).run(max_retries=1)

    assert result.outcome == Outcome.FLAGGED and len(result.attempts) == 2 and result.final is result.attempts[0]
