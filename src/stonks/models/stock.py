class Stock:
    def __init__(self, symbol, price, volume):
        self.symbol = symbol
        self.price = price
        self.volume = volume

    def __repr__(self):
        return (
            f"{self.symbol} | "
            f"Price: ${self.price:.2f} | "
            f"Volume: {self.volume}"
        )