# =============================================================================
# File: catalyst_category.py
# Purpose: Defines catalyst categories recognized by the STONKS C.I.A.
#
# Notes:
# - Categories describe the type of event associated with market news.
# - Classification logic is handled by catalyst_classifier.py.
# =============================================================================

from enum import Enum


class CatalystCategory(Enum):
    """Known catalyst categories used by C.I.A."""

    UNKNOWN = "Unknown"

    # positive/general catalysts
    CONTRACT = "Contract / Purchase Order"
    ACQUISITION = "Acquisition"
    MERGER = "Merger"
    EARNINGS = "Earnings"
    REVENUE_GROWTH = "Revenue Growth"
    REGULATORY_APPROVAL = "Regulatory Approval"
    PATENT = "Patent"
    INSTITUTIONAL_INVESTMENT = "Institutional Investment"
    SHORT_INTEREST = "Short Interest"

    # risk/negative catalysts
    REVERSE_SPLIT = "Reverse Stock Split"
    PUBLIC_OFFERING = "Public Offering"
    BANKRUPTCY = "Bankruptcy / Restructuring"
    MANAGEMENT_CHANGE = "Management Change"

    # market commentary/momentum
    ANALYST_REPORT = "Analyst Report"
    MOMENTUM_HYPE = "Momentum / Hype"