# =============================================================================
# File: news_cli.py
# Purpose: Tests ticker-specific news retrieval and normalization.
# =============================================================================

from datetime import datetime

from stonks.api.market_data import get_news_sentiment
from stonks.cia.catalyst_classifier import classify_article
from stonks.cia.duplicate_filter import filter_duplicate_articles
from stonks.scanner.news_parser import parse_news_articles
from stonks.cia.catalyst_freshness import CatalystFreshness
from stonks.cia.catalyst_freshness import calculate_freshness
from stonks.cia.catalyst_freshness import calculate_news_age_minutes
from stonks.cia.catalyst_freshness import find_newest_catalyst_article


def main():
    """Run the STONKS news-provider test CLI."""

    symbol = input(
        "Ticker to search for news: "
    ).strip().upper()

    if not symbol:
        print("Ticker cannot be empty.")
        return

    data = get_news_sentiment(
        symbol=symbol,
        limit=5
    )

    articles = parse_news_articles(
        data
    )

    unique_articles = filter_duplicate_articles(
        articles
    )

    duplicate_count = (
        len(articles) - len(unique_articles)
    )

    newest_catalyst = find_newest_catalyst_article(
        unique_articles
    )
    
    if newest_catalyst:
        current_time = datetime.now()

        news_age_minutes = calculate_news_age_minutes(
            newest_catalyst.published_at,
            current_time
        )

        freshness = calculate_freshness(
            news_age_minutes
        )

        print(
            f"Newest Catalyst: {newest_catalyst.title}\n"
            f"Published: "
            f"{newest_catalyst.published_at.strftime('%b %d, %Y at %I:%M %p')}\n"
            f"Age: {news_age_minutes} minutes\n"
            f"Freshness: {freshness.value}\n"
        )
    else:
        print(
            f"Newest Catalyst: None\n"
            f"Freshness: {CatalystFreshness.UNKNOWN.value}\n"
        )

    print("")
    print(f"=== Recent News for {symbol} ===")
    print("")

    if not articles:
        print("No news articles were returned.")
        return
    
    print(
        f"Articles: {len(articles)} | "
        f"Unique: {len(unique_articles)} | "
        f"Duplicates Removed: {duplicate_count}"
    )

    for index, article in enumerate(
        unique_articles,
        start=1
    ):

        categories = classify_article(
            article
        )

        category_text = ", ".join(
            category.value
            for category in categories
        )
        
        print(
            f"{index}. {article.title}\n"
            f"   Source: {article.source}\n"
            f"   Published: "
            f"{article.published_at.strftime('%b %d, %Y at %I:%M %p')}\n"
            f"   Sentiment: "
            f"{article.overall_sentiment_label} "
            f"({article.overall_sentiment_score:.3f})\n"
            f"   C.I.A.: {category_text}\n"
        )


if __name__ == "__main__":
    main()