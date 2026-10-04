import pytest

from adgen.core.briefs import Brief, Product
from adgen.core.checks import Verdict
from adgen.evaluation.judge import CheckResult, Evaluation


@pytest.fixture
def product() -> Product:
    return Product(id="kiehls_ultra_facial_cream", brand="Kiehl's", name="Ultra Facial Cream", category="label_text", split="dev", risk="")


def make_brief(product: Product, geo: str = "Sydney, Australia", text: str = "SUMMER GLOW 25% OFF") -> Brief:
    return Brief(id="b02", product=product, split="dev", geo=geo, season="summer", text=text)


@pytest.fixture
def brief(product: Product) -> Brief:
    return make_brief(product)


def check(verdict: Verdict = Verdict.PASS, reason: str = "ok") -> CheckResult:
    return CheckResult(verdict, reason)


def make_evaluation(failing: dict[str, str] | None = None) -> Evaluation:
    failing = failing or {}
    result = {name: check(Verdict.FAIL, failing[name]) if name in failing else check() for name in ("text", "product", "season_fit", "market_fit", "no_cliche")}
    subchecks = {name: result[name] for name in ("season_fit", "market_fit", "no_cliche")}
    context_failed = any(c.failed for c in subchecks.values())
    return Evaluation(
        size=check(),
        text=result["text"],
        product=result["product"],
        context=check(Verdict.FAIL if context_failed else Verdict.PASS),
        subchecks=subchecks,
        cost_usd=0.01,
    )
