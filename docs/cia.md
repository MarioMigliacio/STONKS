# C.I.A. — Catalyst Intelligence Analysis

[← Back to Main README](../README.md)

The STONKS C.I.A. subsystem analyzes ticker-specific financial news to help answer:

> Why is this stock moving, and is the catalyst still relevant for day trading?

---

## Current Features

- Retrieves ticker-specific financial news
- Normalizes provider data into `NewsArticle`
- Removes exact duplicate articles
- Classifies articles into catalyst categories
- Separates active catalysts from historical context
- Tracks catalyst freshness
- Detects breaking news
- Calculates average sentiment
- Assigns catalyst strength and confidence
- Produces a human-readable mission brief

---

## Catalyst Freshness

C.I.A. prioritizes recent information for day trading.

```text
0–60 minutes   → Breaking 🔥
1–4 hours      → Fresh
4–24 hours     → Recent
24+ hours      → Stale
```

Only Breaking, Fresh, and Recent catalysts are considered active intelligence.

Older recognized catalysts remain available as historical context.

---

## Catalyst Categories

Current categories include:

- Contract / Purchase Order
- Acquisition
- Merger
- Earnings
- Revenue Growth
- Regulatory Approval
- Patent
- Institutional Investment
- Reverse Stock Split
- Public Offering
- Bankruptcy / Restructuring
- Management Change
- Analyst Report
- Momentum / Hype
- Short Interest

Articles that do not match a known category remain `Unknown`.

---

## C.I.A. Pipeline

```text
News API
    ↓
News Parser
    ↓
NewsArticle[]
    ↓
Duplicate Filter
    ↓
Catalyst Classifier
    ↓
Freshness + Sentiment + Strength
    ↓
CatalystReport
    ↓
Mission Brief
```

---

## Example

```text
TARGET:              DFNS
MISSION STATUS:      NO ACTIVE CATALYST

CATALYST STRENGTH:   Weak
FRESHNESS:           Stale
SENTIMENT:           Neutral (+0.08)
CONFIDENCE:          85%

CURRENT INTELLIGENCE
None

HISTORICAL CONTEXT
- Short Interest
- Reverse Stock Split
- Acquisition
- Contract / Purchase Order
```

When breaking catalyst news is detected:

```text
🔥 BREAKING CATALYST DETECTED 🔥
```

---

## Future Work

- News caching and new-article detection
- Event-level duplicate detection
- Better catalyst weighting
- AI-assisted article summarization
- Scanner integration with 🔥 ticker indicators
- Journal integration
- Additional news providers

---
