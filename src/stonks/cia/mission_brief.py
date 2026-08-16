# =============================================================================
# File: mission_brief.py
# Purpose: Formats a human-readable STONKS C.I.A. mission briefing.
#
# Notes:
# - Presentation only.
# - Consumes a completed CatalystReport.
# - Does not perform classification, scoring, freshness, or API logic.
# =============================================================================

from stonks.cia.catalyst_report import CatalystReport


STONKS_BANNER = r"""
=============================================================================
  ███████╗████████╗ ██████╗ ███╗   ██╗██╗  ██╗███████╗
  ██╔════╝╚══██╔══╝██╔═══██╗████╗  ██║██║ ██╔╝██╔════╝
  ███████╗   ██║   ██║   ██║██╔██╗ ██║█████╔╝ ███████╗
  ╚════██║   ██║   ██║   ██║██║╚██╗██║██╔═██╗ ╚════██║
  ███████║   ██║   ╚██████╔╝██║ ╚████║██║  ██╗███████║
  ╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝

                         C.I.A.
               Catalyst Intelligence Analysis
=============================================================================
"""


def get_mission_status(
    report: CatalystReport
) -> str:
    """Return a human-readable mission status."""

    if report.has_breaking_news:
        return "🔥 BREAKING CATALYST DETECTED 🔥"

    if report.categories:
        return "ACTIVE CATALYST DETECTED"

    return "NO ACTIVE CATALYST"


def format_categories(
    categories
) -> str:
    """Format catalyst categories for terminal display."""

    if not categories:
        return "None"

    return "\n".join(
        f"- {category.value}"
        for category in categories
    )


def build_mission_brief(
    report: CatalystReport
) -> str:
    """Build the complete STONKS C.I.A. mission briefing."""

    mission_status = get_mission_status(
        report
    )

    current_intelligence = format_categories(
        report.categories
    )

    historical_context = format_categories(
        report.historical_categories
    )

    return (
        f"{STONKS_BANNER}\n"
        f"TARGET:              {report.ticker}\n"
        f"MISSION STATUS:      {mission_status}\n"
        f"\n"
        f"CATALYST STRENGTH:   {report.catalyst_strength.value}\n"
        f"FRESHNESS:           {report.freshness.value}\n"
        f"SENTIMENT:           "
        f"{report.overall_sentiment} "
        f"({report.average_sentiment:+.2f})\n"
        f"CONFIDENCE:          {report.confidence:.0%}\n"
        f"\n"
        f"-----------------------------------------------------------------------------\n"
        f"CURRENT INTELLIGENCE\n"
        f"-----------------------------------------------------------------------------\n"
        f"\n"
        f"{current_intelligence}\n"
        f"\n"
        f"-----------------------------------------------------------------------------\n"
        f"HISTORICAL CONTEXT\n"
        f"-----------------------------------------------------------------------------\n"
        f"\n"
        f"{historical_context}\n"
        f"\n"
        f"-----------------------------------------------------------------------------\n"
        f"INTELLIGENCE SUMMARY\n"
        f"-----------------------------------------------------------------------------\n"
        f"\n"
        f"{report.summary}\n"
        f"\n"
        f"============================================================================="
    )