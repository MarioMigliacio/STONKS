# =============================================================================
# File: stock.py
# Purpose: Defines the Stock data model used by scanner results.
# =============================================================================

class Stock:
    """Represents a simplified stock quote result."""
    
    def __init__(self, symbol, price, volume):
        """Initialize a Stock instance."""
        
        self.symbol = symbol
        self.price = price
        self.volume = volume

    def __repr__(self):
        """Return a readable string representation for console output."""
        
        return (
            f"{self.symbol} | "
            f"Price: ${self.price:.2f} | "
            f"Volume: {self.volume:,}"
        )
