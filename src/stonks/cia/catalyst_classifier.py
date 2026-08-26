# =============================================================================
# File: catalyst_classifier.py
# Purpose: Classifies news articles into C.I.A. catalyst categories.
#
# Notes:
# - Uses simple rule-based keyword matching.
# - Classification is intentionally deterministic and provider-agnostic.
# - Catalyst scoring and strength assessment belong to later C.I.A. layers.
# =============================================================================

from stonks.cia.catalyst_category import CatalystCategory
from stonks.models.news_article import NewsArticle

# =============================================================================
# Catalyst Keyword Rules
# =============================================================================

CATALYST_RULES = {
    CatalystCategory.CONTRACT: [
        "contract",
        "purchase order",
        "awarded contract",
        "contract awarded",
    ],
    CatalystCategory.ACQUISITION: [
        "acquisition",
        "acquires",
        "acquired",
        "acquire",
        "majority stake",
    ],
    CatalystCategory.MERGER: [
        "merger",
        "merging",
        "merges with",
        "merge agreement",
    ],
    CatalystCategory.EARNINGS: [
        "earnings",
        "quarterly results",
        "financial results",
        "net income",
        "eps",
    ],
    CatalystCategory.REVENUE_GROWTH: [
        "revenue growth",
        "record revenue",
        "record sales",
        "revenue increased",
        "sales increased",
    ],
    CatalystCategory.REGULATORY_APPROVAL: [
        "fda approval",
        "fda approved",
        "regulatory approval",
        "approved by the fda",
        "clearance",
    ],
    CatalystCategory.PATENT: [
        "patent",
        "patent granted",
        "patent approval",
    ],
    CatalystCategory.INSTITUTIONAL_INVESTMENT: [
        "institutional investor",
        "institutional investment",
        "strategic investment",
        "acquires stake",
        "acquired stake",
        "takes stake",
        "purchases shares",
    ],
    CatalystCategory.SHORT_INTEREST: [
        "short interest",
        "short float",
        "shorted shares",
    ],
    CatalystCategory.REVERSE_SPLIT: [
        "reverse split",
        "reverse stock split",
    ],
    CatalystCategory.PUBLIC_OFFERING: [
        "public offering",
        "registered offering",
        "direct offering",
        "stock offering",
    ],
    CatalystCategory.BANKRUPTCY: [
        "bankruptcy",
        "chapter 11",
        "restructuring",
    ],
    CatalystCategory.MANAGEMENT_CHANGE: [
        "appoints ceo",
        "new ceo",
        "chief executive officer",
        "resigns",
        "management change",
    ],
    CatalystCategory.ANALYST_REPORT: [
        "analyst upgrade",
        "analyst downgrade",
        "price target",
        "initiates coverage",
    ],
    CatalystCategory.MOMENTUM_HYPE: [
        "stock soars",
        "stock rockets",
        "stock explodes",
        "momentum traders",
        "trading frenzy",
        "breakout",
    ],
}


# =============================================================================
# Classification
# =============================================================================


def find_categories(searchable_text: str) -> list[CatalystCategory]:
    """Find catalyst categories within searchable text."""

    categories = []

    searchable_text = searchable_text.lower()

    for category, keywords in CATALYST_RULES.items():
        for keyword in keywords:
            if keyword in searchable_text:
                categories.append(category)
                break

    return categories


def classify_article(article: NewsArticle) -> list[CatalystCategory]:
    """Classify an article using its title and summary."""

    categories = find_categories(article.title)

    summary_categories = find_categories(article.summary)

    for category in summary_categories:
        if category not in categories:
            categories.append(category)

    if categories:
        return categories

    return [CatalystCategory.UNKNOWN]
