# =============================================================================
# File: news_cli.py
# Purpose: Tests ticker-specific news retrieval and C.I.A. analysis.
# =============================================================================

from datetime import datetime

from stonks.api.market_data import get_news_sentiment
from stonks.cia.catalyst_classifier import classify_article
from stonks.cia.cia_engine import build_catalyst_report
from stonks.cia.duplicate_filter import filter_duplicate_articles
from stonks.scanner.news_parser import parse_news_articles


def main():
    """Run the STONKS news and C.I.A. command-line interface."""

    symbol = input(
        "Ticker to search for news: "
    ).strip().upper()

    if not symbol:
        print("Ticker cannot be empty.")
        return

    data = get_news_sentiment(
        symbol=symbol,
        limit=50
    )

    articles = parse_news_articles(
        data
    )

    if not articles:
        print("")
        print(f"No news articles were returned for {symbol}.")
        return

    unique_articles = filter_duplicate_articles(
        articles
    )

    report = build_catalyst_report(
        ticker=symbol,
        articles=unique_articles,
        original_article_count=len(articles),
        current_time=datetime.now()
    )

    print("")
    print("=== C.I.A. Report ===")
    print("")
    print(f"Ticker: {report.ticker}")
    print(f"Strength: {report.catalyst_strength.value}")
    print(f"Freshness: {report.freshness.value}")
    print(f"Breaking News: {report.has_breaking_news}")
    print(f"Sentiment: {report.overall_sentiment}")
    print(f"Confidence: {report.confidence:.0%}")

    if report.categories:
        category_text = ", ".join(
            category.value
            for category in report.categories
        )
    else:
        category_text = "None"

    print(f"Categories: {category_text}")
    print(f"Summary: {report.summary}")

    print("")
    print(f"=== Recent News for {symbol} ===")
    print("")

    print(
        f"Articles: {len(articles)} | "
        f"Unique: {len(unique_articles)} | "
        f"Duplicates Removed: "
        f"{len(articles) - len(unique_articles)}"
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