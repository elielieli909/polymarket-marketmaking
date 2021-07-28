from market_maker.polymarketInterface import Order
import time

class OrderHistory:
    def __init__(self) -> None:
        """Keeps track of all the orders executed by a set of bands"""
        self.orders = []
        # TODO: use a lock (for when threading is implemented)

    def add_order(self, order: dict):
        """Take a dict of form {"timestamp", "size"} to keep track of"""
        assert('timestamp' in order)
        assert('size' in order)

        self.orders.append(order)

    def get_history(self):
        return self.orders


class OrderLimit:
    def __init__(self, limit: dict) -> None:
        self.amount = float(limit['amount'])
        self.period = int(limit['period'])
    
    def remaining_size(self, time: int, order_hist: OrderHistory):
        assert(isinstance(order_hist, OrderHistory))

        used_amount = sum([o['size'] for o in order_hist.get_history() if time - self.period <= o['timestamp'] <= time])
        return max(self.amount - used_amount, 0)
        

class OrderLimits:
    def __init__(self, limits: dict, order_history: OrderHistory) -> None:
        """Creates a list of OrderLimit objects, given a list of limit objects {'period': numSeconds, 'amount': limitAmount}"""
        self.limits = list(map(OrderLimit, limits))
        self.order_history = order_history

    def get_remaining_size(self, time: int):
        """Return the amount of units able to be bought/sold according to bands.json's buyLimits/sellLimits"""
        if len(self.limits) != 0:
            return min(*map(lambda r: r.remaining_size(time, self.order_history), self.limits))
        else:
            return (2**256 - 1)

    def use_limit(self, timestamp: int, size: float):
        self.order_history.add_order({'timestamp': timestamp, 'size': size})
        