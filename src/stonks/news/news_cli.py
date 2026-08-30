# =============================================================================
# File: news_cli.py
# Purpose: Tests ticker-specific news retrieval and C.I.A. analysis.
# =============================================================================

from datetime import datetime, timezone

from stonks.api.market_data import get_news_sentiment
from stonks.cia.catalyst_classifier import classify_article
from stonks.cia.cia_engine import build_catalyst_report
from stonks.cia.duplicate_filter import filter_duplicate_articles
from stonks.cia.mission_brief import build_mission_brief
from stonks.log_manager import configure_logging
from stonks.scanner.news_parser import parse_news_articles


def main() -> None:
    """Run the STONKS news and C.I.A. command-line interface."""

    configure_logging()

    symbol = input("Ticker to search for news: ").strip().upper()

    if not symbol:
        print("Ticker cannot be empty.")
        return

    data = get_news_sentiment(symbol=symbol, limit=50)

    articles = parse_news_articles(data, symbol)

    if not articles:
        print("")
        print(f"No news articles were returned for {symbol}.")
        return

    unique_articles = filter_duplicate_articles(articles)

    report = build_catalyst_report(
        ticker=symbol,
        articles=unique_articles,
        original_article_count=len(articles),
        current_time=datetime.now(timezone.utc),
    )

    print("")
    print(build_mission_brief(report))

    # =========================================================================
    # Raw News Output
    # =========================================================================

    print("")
    print(f"=== Recent News for {symbol} ===")
    print("")

    print(
        f"Articles: {report.original_article_count} | "
        f"Unique: {report.unique_article_count} | "
        f"Duplicates Removed: "
        f"{report.duplicate_articles_removed}"
    )

    for index, article in enumerate(unique_articles, start=1):
        categories = classify_article(article)

        category_text = ", ".join(category.value for category in categories)

        print(
            f"{index}. {article.title}\n"
            f"   Source: {article.source}\n"
            f"   Published: "
            f"{article.published_at.strftime('%b %d, %Y at %I:%M %p UTC')}\n"
            f"   Sentiment: "
            f"{article.sentiment_label} "
            f"({article.sentiment_score:.3f})\n"
            f"   C.I.A.: {category_text}\n"
        )


if __name__ == "__main__":
    main()
