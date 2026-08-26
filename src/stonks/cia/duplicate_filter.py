# =============================================================================
# File: duplicate_filter.py
# Purpose: Filters duplicate news articles before C.I.A. analysis.
#
# Notes:
# - Duplicate detection currently uses normalized article titles and URLs.
# - More advanced event similarity detection may be added later.
# - This layer should remain independent of catalyst classification.
# =============================================================================

from stonks.models.news_article import NewsArticle


def normalize_title(title: str) -> str:
    """Normalize an article title for duplicate comparison."""

    return title.strip().lower()


def filter_duplicate_articles(articles: list[NewsArticle]) -> list[NewsArticle]:
    """Return news articles with duplicate titles or URLs removed."""

    unique_articles: list[NewsArticle] = []

    seen_titles: set[str] = set()
    seen_urls: set[str] = set()

    for article in articles:
        normalized_title = normalize_title(article.title)

        if normalized_title in seen_titles:
            continue

        if article.url and article.url in seen_urls:
            continue

        unique_articles.append(article)

        seen_titles.add(normalized_title)

        if article.url:
            seen_urls.add(article.url)

    return unique_articles
