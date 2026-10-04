from pathlib import Path

from adgen.core.checks import Verdict
from adgen.golden.ground_truth import Basis, derive
from adgen.golden.items import GoldenItem, Plant, Tier, change_description
from adgen.golden.panel import merge_verdicts
from tests.conftest import make_brief

PASSING = {key: {"verdict": "pass", "note": ""} for key in ("text", "product", "season_fit", "market_fit", "no_cliche")}


def final_item(brief_id: str = "b02") -> GoldenItem:
    return GoldenItem(f"d2-{brief_id}", brief_id, "p", "dev", "d2", Path("x.png"))


def panel_reviews(verdict: str = "pass") -> list[dict]:
    checks = {key: {"verdict": verdict} for key in PASSING}
    return [{"model": "a", "checks": checks}, {"model": "b", "checks": checks}]


def test_tiers_and_base_item():
    planted = GoldenItem("p01", "b02", "p", "dev", "planted", Path("x"), plant=Plant("text", ("text",), "subtle", "Change it. Keep the rest."))
    assert planted.tier == Tier.PLANTED and planted.base_item_id == "d2-b02"
    assert final_item().tier == Tier.FINAL
    assert GoldenItem("v1-b02", "b02", "p", "dev", "v1", Path("x")).tier == Tier.EARLIER


def test_change_description_drops_the_keep_clause():
    assert change_description("Recolour the bottle green. Keep everything else identical.") == "Recolour the bottle green."
    assert change_description("Remove the headline. Change nothing else.") == "Remove the headline."


def test_merge_verdicts_agreement_and_disagreement():
    a = {"checks": {"text": {"verdict": "fail"}, "product": {"verdict": "pass"}}}
    b = {"checks": {"text": {"verdict": "fail"}, "product": {"verdict": "fail"}}}
    merged = merge_verdicts([a, b])
    assert merged["text"] == Verdict.FAIL and merged["product"] == Verdict.UNSURE and merged["season_fit"] == Verdict.UNSURE


def test_merge_verdicts_rejects_invalid_values():
    review = {"checks": {"text": {"verdict": "pass|fail"}}}
    assert merge_verdicts([review, review])["text"] == Verdict.UNSURE


def test_confirmed_panel_cultural_verdict_is_silver_outside_india(product):
    items = {"d2-b02": final_item()}
    labels = {"d2-b02": {"tier": 3, "prefill_shown": True, "checks": PASSING}}
    truth = derive(items, labels, {"d2-b02": panel_reviews()}, {"b02": make_brief(product)})["d2-b02"]["checks"]
    assert truth["no_cliche"]["basis"] == Basis.SILVER and truth["text"]["basis"] == Basis.GOLD
    assert truth["context"] == {"verdict": Verdict.PASS, "basis": Basis.COMBINED}


def test_india_cultural_verdicts_are_always_gold(product):
    items = {"d2-b02": final_item()}
    labels = {"d2-b02": {"tier": 3, "prefill_shown": True, "checks": PASSING}}
    truth = derive(items, labels, {"d2-b02": panel_reviews()}, {"b02": make_brief(product, geo="Mumbai, India")})["d2-b02"]["checks"]
    assert truth["no_cliche"]["basis"] == Basis.GOLD


def test_planted_item_inherits_base_and_overrides_targeted_check(product):
    plant = Plant("context", ("season_fit",), "moderate", "Make it snow.")
    items = {"d2-b02": final_item(), "p19": GoldenItem("p19", "b02", "p", "dev", "planted", Path("x"), plant=plant)}
    labels = {"d2-b02": {"tier": 3, "prefill_shown": False, "checks": PASSING}, "p19": {"tier": 1, "answer": "yes"}}
    truth = derive(items, labels, {}, {"b02": make_brief(product)})["p19"]["checks"]
    assert truth["season_fit"] == {"verdict": Verdict.FAIL, "basis": Basis.GOLD}
    assert truth["text"]["basis"] == Basis.INHERITED
    assert truth["context"]["verdict"] == Verdict.FAIL


def test_earlier_item_only_labels_its_target_checks(product):
    items = {"d2-b02": final_item(), "v1-b02": GoldenItem("v1-b02", "b02", "p", "dev", "v1", Path("x"), target_checks=("no_cliche",))}
    labels = {"d2-b02": {"tier": 3, "prefill_shown": False, "checks": PASSING}, "v1-b02": {"tier": 2, "answer": "unclear"}}
    truth = derive(items, labels, {}, {"b02": make_brief(product)})["v1-b02"]["checks"]
    assert set(truth) == {"no_cliche", "context"} and truth["no_cliche"]["verdict"] == Verdict.UNSURE
