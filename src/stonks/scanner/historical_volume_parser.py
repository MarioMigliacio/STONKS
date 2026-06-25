# =============================================================================
# File: historical_volume_parser.py
# Purpose: Parses cached historical market data into volume records.
# =============================================================================

from stonks.models.historical_volume_data import HistoricalVolumeData

def parse_historical_volumes(data) -> list[HistoricalVolumeData]:
    """
    Parse Alpha Vantage daily time series data into historical volume records.
    """

    if not data:
        return []

    time_series = data.get("Time Series (Daily)")

    if not time_series:
        return []

    historical_volumes = []

    for trade_date, daily_data in time_series.items():
        volume = int(daily_data["5. volume"])

        historical_volumes.append(
            HistoricalVolumeData(
                trade_date=trade_date,
                volume=volume
            )
        )

    return historical_volumes