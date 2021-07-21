class OrderLimit:
    def __init__(self, limit: dict) -> None:
        self.amount = float(limit['amount'])
        self.period = int(limit['period'])
    
    def remaining_size(self, time: int, order_hist: list):
        """Return the amount of units able to be bought/sold according to bands.json's buyLimits/sellLimits"""
        