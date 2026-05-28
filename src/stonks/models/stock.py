# =============================================================================
# File: stock.py
# Purpose: Defines the Stock data model used by scanner results.
# =============================================================================

class Stock:
    """Represents a simplified stock quote result."""
    
    def __init__(self, symbol, price, volume, change_percent):
        """Initialize a Stock instance."""

        self.symbol = symbol
        self.price = price
        self.volume = volume
        self.change_percent = change_percent

    def __repr__(self):
        """Return a readable string representation for console output."""

        return (
            f"{self.symbol} | "
            f"Price: ${self.price:.2f} | "
            f"Volume: {self.volume:,} | "
            f"Change: {self.change_percent:.2f}%"
        )
