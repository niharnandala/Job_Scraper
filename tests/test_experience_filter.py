"""Regression tests for the conservative experience policy."""
from scrape_jobs import _experience_is_clearly_required_over_two


def test_zero_to_five_is_kept():
    assert _experience_is_clearly_required_over_two("0-5 years required") is False


def test_two_to_five_is_kept_when_required():
    assert _experience_is_clearly_required_over_two("2-5 years required") is False


def test_three_plus_required_is_rejected():
    assert _experience_is_clearly_required_over_two("3+ years of experience required") is True


def test_high_experience_preferred_is_kept():
    assert _experience_is_clearly_required_over_two("5+ years preferred") is False


def test_high_experience_ambiguous_is_kept():
    assert _experience_is_clearly_required_over_two("3+ years of experience") is False


def test_experience_missing_is_kept():
    assert _experience_is_clearly_required_over_two("experience with Python is a plus") is False
