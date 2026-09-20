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


def test_structured_date_posted_is_used_as_fallback():
    from scrape_extra_sources import extract_structured_posting_date
    html = '<script type="application/ld+json">{"@type":"JobPosting","datePosted":"2026-09-20T08:00:00Z"}</script>'
    assert extract_structured_posting_date(html) == "2026-09-20T08:00:00Z"


def test_unknown_without_structured_date_stays_unknown():
    from scrape_extra_sources import extract_structured_posting_date
    assert extract_structured_posting_date("<html><body>Apply India</body></html>") is None
