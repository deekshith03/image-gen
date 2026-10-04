from adgen.core.checks import Verdict
from adgen.evaluation.scoring import panel_anchored_checks, score
from adgen.golden.ground_truth import Basis, TruthCheck, TruthRow


def row(item_id: str, checks: dict[str, tuple[str, str]], severity: str | None = None) -> TruthRow:
    return TruthRow(item_id, "b02", "dev", "planted" if severity else "d2", severity, {k: TruthCheck(Verdict(v), b) for k, (v, b) in checks.items()})


def judged(**verdicts: str) -> dict:
    return {"checks": {check: {"verdict": verdict, "reason": f"judge on {check}"} for check, verdict in verdicts.items()}}


def test_catch_and_pass_rates_and_misses():
    truth = [row("a", {"text": ("fail", Basis.GOLD)}), row("b", {"text": ("pass", Basis.GOLD)}), row("c", {"text": ("fail", Basis.GOLD)})]
    card = score(truth, {"a": judged(text="fail"), "b": judged(text="fail"), "c": judged(text="pass")}, {}, {"a": "a", "b": "b", "c": "c"})
    assert (card.all["text"].catch.hits, card.all["text"].catch.total) == (1, 2)
    assert (card.all["text"].keep.hits, card.all["text"].keep.total) == (0, 1)
    assert sorted(m.item_id for m in card.misses) == ["b", "c"]


def test_unsure_labels_are_not_scored_and_missing_results_are_reported():
    card = score([row("a", {"text": ("unsure", Basis.GOLD)}), row("b", {"text": ("pass", Basis.GOLD)})], {"a": judged(text="fail")}, {}, {"a": "a", "b": "b"})
    assert card.all["text"].catch.total == 0 and card.unscored == ["b"]


def test_anchored_checks_are_excluded_from_independent_including_inherited():
    truth = [row("d2-b02", {"product": ("pass", Basis.GOLD)}), row("p01", {"product": ("pass", Basis.INHERITED)}, severity="subtle")]
    results = {"d2-b02": judged(product="pass"), "p01": judged(product="pass")}
    card = score(truth, results, {"d2-b02": {"product"}}, {"d2-b02": "d2-b02", "p01": "d2-b02"})
    assert card.all["product"].keep.total == 2 and card.independent["product"].keep.total == 0


def test_severity_counts_only_gold_planted_failures():
    truth = [row("p01", {"text": ("fail", Basis.GOLD), "product": ("fail", Basis.INHERITED)}, severity="subtle")]
    card = score(truth, {"p01": judged(text="fail", product="fail")}, {}, {"p01": "d2-b02"})
    assert (card.severity["subtle"].hits, card.severity["subtle"].total) == (1, 1)


def test_panel_anchoring_marks_kept_prefill():
    labels = {"d2-b02": {"tier": 3, "prefill_shown": True, "checks": {"text": {"verdict": "pass"}, "product": {"verdict": "fail"}}}}
    reviews = [{"checks": {"text": {"verdict": "pass"}, "product": {"verdict": "pass"}}}] * 2
    assert panel_anchored_checks(labels, {"d2-b02": reviews}) == {"d2-b02": {"text"}}


def test_test_split_refuses_changed_judge_prompts(monkeypatch):
    import pytest

    from adgen.evaluation import cache

    monkeypatch.setattr(cache, "PROMPT_VERSION", "deadbeef")
    monkeypatch.delenv(cache.ALLOW_TEST_RERUN, raising=False)
    test_item = next(i for i, item in cache.load_items().items() if item.split == "test")
    with pytest.raises(RuntimeError, match="refusing to judge test item"):
        cache.evaluate_item(test_item)
