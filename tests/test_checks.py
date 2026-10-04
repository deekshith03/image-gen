from adgen.core.checks import CONTEXT_SUBCHECKS, LABELLED_CHECKS, SCORED_CHECKS, Verdict, combine


def test_combine_fail_dominates():
    assert combine([Verdict.PASS, Verdict.UNSURE, Verdict.FAIL]) == Verdict.FAIL


def test_combine_unsure_beats_pass():
    assert combine([Verdict.PASS, Verdict.UNSURE]) == Verdict.UNSURE


def test_combine_all_pass():
    assert combine(["pass", "pass", "pass"]) == Verdict.PASS


def test_check_registries_are_consistent():
    assert set(CONTEXT_SUBCHECKS) <= set(LABELLED_CHECKS)
    assert set(SCORED_CHECKS) == {"context", *LABELLED_CHECKS}


def test_verdict_serialises_as_plain_string():
    assert f"{Verdict.FAIL}" == "fail" and Verdict("pass") is Verdict.PASS
