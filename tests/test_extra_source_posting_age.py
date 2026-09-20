"""Tests for Wellfound/YC posting-age extraction."""
from scrape_extra_sources import extract_posting_age, age_days


def test_posting_age_uses_explicit_posted_label():
    card = "The Product Highway Data & Machine Learning Engineer Posted 1 month ago Responds within a few days"
    assert extract_posting_age(card) == "1 month ago"
    assert age_days(extract_posting_age(card)) == 30


def test_does_not_use_unrelated_today_text():
    card = (
        "The Product Highway Data & Machine Learning Engineer "
        "Posted 1 month ago. The company uses modern tools today."
    )
    assert extract_posting_age(card) == "1 month ago"
    assert age_days(extract_posting_age(card)) > 2


def test_unknown_posting_age_is_rejected():
    assert extract_posting_age("Data & Machine Learning Engineer Apply India") is None
    assert age_days(None) is None
