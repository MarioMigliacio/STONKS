# =============================================================================
# File: news_cli.py
# Purpose: Tests ticker-specific news retrieval and normalization.
# =============================================================================

from stonks.api.market_data import get_news_sentiment
from stonks.scanner.news_parser import parse_news_articles

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

    articles = parse_news_articles(data)

    print("")
    print(f"=== Recent News for {symbol} ===")
    print("")

    if not articles:
        print("No news articles were returned.")
        return

    for index, article in enumerate(
        articles,
        start=1
    ):
        print(
            f"{index}. {article.title}\n"
            f"   Source: {article.source}\n"
            f"   Published: {article.published_at}\n"
            f"   Sentiment: "
            f"{article.overall_sentiment_label} "
            f"({article.overall_sentiment_score:.3f})\n"
        )


if __name__ == "__main__":
    main()