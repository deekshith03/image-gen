import pytest
from PIL import Image

from adgen.core.checks import Verdict
from adgen.evaluation.judge import CheckResult, check_size, combine_context, normalise_headline, parse_verdict, text_problems
from tests.conftest import make_evaluation


@pytest.mark.parametrize(
    ("rendered", "expected", "match"),
    [
        ("MERENDA D’AUTUNNO", "MERENDA D'AUTUNNO", True),  # typographic apostrophe is the same mark
        ("48–HOUR HYDRATION", "48-HOUR HYDRATION", True),  # en dash equals hyphen
        ("ランニング セール", "ランニングセール", True),  # spacing ignored
        ("summer glow 25% off", "SUMMER GLOW 25% OFF", True),  # case ignored
        ("SEE THE SUMMER.", "SEE THE SUMMER", False),  # punctuation is strict
        ("HYGGE HOURS 20% 0FF", "HYGGE HOURS 20% OFF", False),  # zero is not the letter O
        ("LAGOS LAGOS MOVES", "LAGOS MOVES", False),  # duplicated word
        ("TIME TO EXPLORE $89", "TIME TO EXPLORE $99", False),
    ],
)
def test_normalise_headline_rulings(rendered, expected, match):
    assert (normalise_headline(rendered) == normalise_headline(expected)) is match


def test_text_problems_collects_every_issue():
    problems = text_problems("BBQ SEASON IS HERE", "BBQ SEASON IS", "FUOROOST", "garbled sign", "illegible")
    assert len(problems) == 4 and 'reads "BBQ SEASON IS"' in problems[0]


def test_text_problems_empty_for_exact_match():
    assert text_problems("STREET CLASSICS", "Street  Classics", "", "", "clear") == []


@pytest.mark.parametrize(
    ("raw", "verdict"), [("fail", Verdict.FAIL), ("FAIL ", Verdict.FAIL), ("pass", Verdict.PASS), ("", Verdict.PASS), ("pass | fail", Verdict.PASS)]
)
def test_parse_verdict(raw, verdict):
    assert parse_verdict({"verdict": raw}) == verdict


def test_combine_context_reports_only_failures():
    result = combine_context({"season_fit": CheckResult(Verdict.FAIL, "snow in summer"), "market_fit": CheckResult(Verdict.PASS, "fine")})
    assert result.verdict == Verdict.FAIL and result.reason == "season_fit: snow in summer"


def test_check_size(tmp_path):
    small, big = tmp_path / "small.png", tmp_path / "big.png"
    Image.new("RGB", (1024, 1024)).save(small)
    Image.new("RGB", (1376, 768)).save(big)
    assert check_size(small).verdict == Verdict.PASS
    assert check_size(big).verdict == Verdict.FAIL


def test_evaluation_failures_and_failed_checks():
    evaluation = make_evaluation({"text": "typo", "market_fit": "Eiffel Tower in Kyoto"})
    assert evaluation.failures == ["text", "context"]
    assert list(evaluation.failed_checks()) == ["text", "market_fit"]
    assert evaluation.as_dict()["passed"] is False
