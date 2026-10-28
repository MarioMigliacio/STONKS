# =============================================================================
# File: cia_analysis_result.py
# Purpose: Defines the structured output of a ticker intelligence analysis.
# =============================================================================

from dataclasses import dataclass

from stonks.cia.catalyst_report import CatalystReport
from stonks.models.news_article import NewsArticle


@dataclass
class CiaAnalysisResult:
    """Represents a completed intelligence analysis and its supporting news.

    Attributes:
        report:
            Aggregate catalyst intelligence for the requested ticker.

        articles:
            Deduplicated, ticker-relevant articles supporting the report.
    """

    report: CatalystReport
    articles: list[NewsArticle]
