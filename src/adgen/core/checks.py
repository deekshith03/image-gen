from enum import StrEnum


class Verdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNSURE = "unsure"


CONTEXT_SUBCHECKS = ("season_fit", "market_fit", "no_cliche")
CULTURAL_CHECKS = ("market_fit", "no_cliche")

LABELLED_CHECKS = {
    "text": "Text",
    "product": "Product",
    "season_fit": "Season fit",
    "market_fit": "Market fit",
    "no_cliche": "No cliché",
}

PIPELINE_GATES = ("size", "text", "product", "context")

SCORED_CHECKS = ("text", "product", "context", *CONTEXT_SUBCHECKS)


def combine(verdicts: list[str]) -> Verdict:
    if Verdict.FAIL in verdicts:
        return Verdict.FAIL
    if Verdict.UNSURE in verdicts:
        return Verdict.UNSURE
    return Verdict.PASS
