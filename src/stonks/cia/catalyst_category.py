# =============================================================================
# File: catalyst_category.py
# Purpose: Defines catalyst categories recognized by the STONKS C.I.A.
#
# Notes:
# - Categories describe the type of event associated with market news.
# - Classification logic will be implemented in a later feature branch.
# =============================================================================

from enum import Enum

class CatalystCategory(Enum):
    """Known catalyst categories used by C.I.A."""

    UNKNOWN = "Unknown"

    CONTRACT = "Contract / Purchase Order"
    ACQUISITION = "Acquisition"
    MERGER = "Merger"
    EARNINGS = "Earnings"
    REVENUE_GROWTH = "Revenue Growth"
    REGULATORY_APPROVAL = "Regulatory Approval"
    PATENT = "Patent"
    INSTITUTIONAL_INVESTMENT = "Institutional Investment"

    REVERSE_SPLIT = "Reverse Stock Split"
    PUBLIC_OFFERING = "Public Offering"
    BANKRUPTCY = "Bankruptcy / Restructuring"
    MANAGEMENT_CHANGE = "Management Change"

    ANALYST_REPORT = "Analyst Report"
    MOMENTUM_HYPE = "Momentum / Hype"