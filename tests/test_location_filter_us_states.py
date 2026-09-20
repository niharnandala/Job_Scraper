"""Regression tests for the India-focused location filter."""
import pytest
from scrape_jobs import is_target_location


INDIA_LOCATIONS = [
    "India",
    "Bengaluru, Karnataka, India",
    "Hyderabad, Telangana, India",
    "Mumbai, Maharashtra, India",
    "Pune, Maharashtra, India",
    "Chennai, Tamil Nadu, India",
    "Delhi, India",
    "Remote, India",
]


@pytest.mark.parametrize("location", INDIA_LOCATIONS)
def test_india_locations_accepted(location):
    assert is_target_location(location) is True, (
        f'"{location}" was rejected — India location filter bug'
    )


@pytest.mark.parametrize("location", [
    "San Francisco, California, United States",
    "Austin, Texas, United States",
    "London, United Kingdom",
    "Toronto, Canada",
    "Sydney, Australia",
    "Singapore",
])
def test_non_india_locations_rejected(location):
    assert is_target_location(location) is False, (
        f'"{location}" was accepted — should be rejected'
    )


def test_empty():
    assert is_target_location("") is False


def test_none():
    assert is_target_location(None) is False  # type: ignore[arg-type]
