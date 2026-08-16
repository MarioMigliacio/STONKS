# C.I.A. News Subsystem

[← Back to Main README](../README.md)

## Catalyst Intelligence Analysis

The STONKS C.I.A. subsystem retrieves, normalizes, and presents ticker-specific financial news.

Its purpose is not simply to count headlines. The long-term goal is to help answer a more useful trading question:

> Why is this stock moving?

---

## Current Features

- Retrieve recent news for a ticker
- Filter provider results by ticker symbol
- Normalize provider-specific JSON into `NewsArticle` objects
- Display readable publication dates and times
- Display publisher information
- Display provider-generated sentiment labels and scores
- Keep news parsing separate from provider-specific API fields

---

## Current Data Flow

```text
Ticker Symbol
    ↓
Alpha Vantage NEWS_SENTIMENT
    ↓
Provider JSON Response
    ↓
News Parser
    ↓
NewsArticle Models
    ↓
C.I.A. Command-Line Output
```

The rest of STONKS consumes normalized `NewsArticle` objects rather than raw Alpha Vantage fields.

This allows additional news providers to be introduced later without rewriting the catalyst-analysis logic.

---

## Project Structure

```text
src/
└── stonks/
    ├── api/
    │   └── market_data.py
    │
    ├── models/
    │   └── news_article.py
    │
    ├── news/
    │   └── news_cli.py
    │
    └── scanner/
        └── news_parser.py

scripts/
└── news.ps1
```

---

## Running the News CLI

From the project root:

```powershell
.\scripts\news.ps1
```

Or from the scripts directory:

```powershell
cd scripts
.\news.ps1
```

Enter a ticker when prompted:

```text
Ticker to search for news: DFNS
```

---

## Example Output

```text
=== Recent News for DFNS ===

1. T3 Defense Subsidiary Receives New Purchase Order
   Source: GlobeNewswire
   Published: August 04, 2026 at 10:45 PM
   Sentiment: Bullish (0.402)

2. DFNS Stock Explodes as Momentum Traders Pile In
   Source: StocksToTrade
   Published: August 03, 2026 at 04:40 PM
   Sentiment: Somewhat-Bullish (0.266)
```

The publication timestamp is converted from the compact provider format:

```text
20260804T224528
```

into a human-readable form:

```text
August 04, 2026 at 10:45 PM
```

The provider timestamp currently has no timezone label attached to it. STONKS therefore displays the date and time without claiming that it is Pacific, Eastern, or UTC.

---

## NewsArticle Model

Each provider response is converted into a normalized model containing:

```text
title
source
published_at
summary
url
overall_sentiment_score
overall_sentiment_label
```

Provider-specific field names remain inside the parser layer.

For example, Alpha Vantage supplies:

```text
time_published
overall_sentiment_score
overall_sentiment_label
```

The rest of STONKS accesses:

```python
article.published_at
article.overall_sentiment_score
article.overall_sentiment_label
```

This keeps the application provider-agnostic.

---

## API Usage

One execution for one ticker currently performs one `NEWS_SENTIMENT` API request.

Example:

```text
DFNS
    ↓
One API request
    ↓
Multiple recent articles returned
```

The number of returned articles does not represent the number of API requests.

A focused ticker search is recommended while using a limited free API tier.

---

## Sentiment

Alpha Vantage provides:

- An overall sentiment score
- An overall sentiment label

Example:

```text
Bullish (0.402)
```

Sentiment should be treated as supporting information rather than a trading decision by itself.

A bullish article does not guarantee that:

- The information is materially important
- The article contains a new catalyst
- The stock will continue rising
- The current price offers a good entry

Future C.I.A. analysis should distinguish between article sentiment and catalyst strength.

---

## Planned News Cache

A future cache layer may store news under:

```text
data/
└── cache/
    └── news/
        └── DFNS_news.json
```

The planned workflow is:

```text
Request recent news
    ↓
Normalize articles
    ↓
Compare with cached articles
    ↓
Store new articles
    ↓
Report only newly discovered updates
```

Potential duplicate detection fields include:

- Article URL
- Publication timestamp
- Title
- Provider identifier, when available

Cached news files should remain excluded from Git version control.

---

## Planned C.I.A. Analysis

The long-term Catalyst Intelligence Analysis subsystem may group articles into catalyst categories such as:

- Contract or purchase order
- Acquisition
- Merger
- Earnings
- Revenue growth
- Regulatory approval
- Patent
- Institutional investment
- Reverse stock split
- Public offering
- Bankruptcy or restructuring
- Management change
- Analyst report
- Unconfirmed momentum or hype

Example future output:

```text
=========================================
 STONKS C.I.A.
 Catalyst Intelligence Analysis
=========================================

Ticker: DFNS

Catalyst Strength:
Strong

Recent Catalysts:
- Defense purchase order
- Drone-sector acquisition
- Institutional investment

Risk Events:
- Reverse stock split
- Critical research report

Overall News Sentiment:
Bullish
```

---

## Future AI Summarization

AI may eventually help summarize multiple related articles into a concise catalyst report.

Example:

```text
Catalyst Summary

T3 Defense has received multiple defense-related purchase orders,
reported strong subsidiary performance, expanded into drone and
counter-UAV technology, and attracted institutional investment.
Interest has also been amplified by a recent reverse stock split
that substantially reduced the outstanding share count.
```

The AI layer should operate on normalized and preferably cached article data.

Recommended architecture:

```text
NewsArticle Models
    ↓
Catalyst Summarizer Interface
    ├── Rule-Based Summarizer
    ├── Hosted AI Provider
    └── Local AI Model
    ↓
CatalystSummary Model
```

AI-generated summaries should always remain traceable to the underlying articles. STONKS should preserve article titles, publishers, publication times, and original URLs so the user can verify the summary.

---

## Future Roadmap

- News response caching
- New-article detection
- Duplicate article filtering
- Catalyst category detection
- Catalyst strength scoring
- Positive and negative catalyst separation
- AI-assisted article summarization
- Article age filtering
- Breaking-news alerts
- Scanner integration
- Journal integration
- Multiple news-provider support

---

## Trading Considerations

The C.I.A. subsystem is intended to improve context, not issue automatic trade recommendations.

A stock may have:

- Strong news but weak price action
- High relative volume but no meaningful catalyst
- Many articles repeating the same press release
- Bullish sentiment after most of the move has already occurred

News should be evaluated alongside:

- Gap percentage
- Relative volume
- Current volume
- Price action
- Float
- Liquidity
- Risk level
- Entry and exit plan

---
