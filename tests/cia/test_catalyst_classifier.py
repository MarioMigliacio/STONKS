# =============================================================================
# File: test_catalyst_classifier.py
# Purpose: Pytest file for catalyst_classifier.py.
# =============================================================================

from stonks.cia.catalyst_category import CatalystCategory
from stonks.cia.catalyst_classifier import find_categories


def test_find_categories_detects_merger() -> None:
    """Detect a legitimate merger catalyst."""

    categories = find_categories(
        "Company announces merger agreement with a strategic partner."
    )

    assert CatalystCategory.MERGER in categories


def test_find_categories_does_not_match_merger_from_emergency() -> None:
    """Do not classify unrelated words containing merger-like substrings."""

    categories = find_categories(
        "Tesla issues emergency recall notice for affected vehicles."
    )

    assert CatalystCategory.MERGER not in categories


def test_find_categories_detects_institutional_investment() -> None:
    """Detect a legitimate institutional investment catalyst."""

    categories = find_categories(
        "BlackRock makes a strategic investment in XYZ Corporation."
    )

    assert CatalystCategory.INSTITUTIONAL_INVESTMENT in categories


def test_find_categories_does_not_match_internal_investments() -> None:
    """Do not classify company spending as institutional investment."""

    categories = find_categories(
        "Tesla increases investments in AI, robotics, and manufacturing."
    )

    assert CatalystCategory.INSTITUTIONAL_INVESTMENT not in categories


def test_find_categories_detects_contract() -> None:
    """Detect a legitimate contract catalyst."""

    categories = find_categories(
        "Company awarded contract for new government infrastructure project."
    )

    assert CatalystCategory.CONTRACT in categories


def test_find_categories_does_not_match_generic_order_language() -> None:
    """Do not classify generic order language as a contract catalyst."""

    categories = find_categories(
        "Court issues emergency order affecting vehicle registrations."
    )

    assert CatalystCategory.CONTRACT not in categories


def test_find_categories_detects_multiple_categories() -> None:
    """Detect multiple catalyst categories in the same text."""

    categories = find_categories(
        "Company reports record revenue and receives FDA approval."
    )

    assert CatalystCategory.REVENUE_GROWTH in categories
    assert CatalystCategory.REGULATORY_APPROVAL in categories