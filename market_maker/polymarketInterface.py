"""
Interfaces with Polymarket's orderbooks.  Analogous to Maker's orderbook_manager
TODO: Could make this hold it's own state like Maker's in order to rely less on an external get_orders API from polymarket
"""

import threading
from concurrent.futures import ThreadPoolExecutor

from market_maker.testOrderbook import TestOrderbook

class Order:
    def __init__(self, size: int, price: float, is_buy: bool) -> None:
        self.size = size
        self.price = price
        self.is_buy = is_buy
        self.id = None


class PolymarketInterface:
    def __init__(self, market_id: str, refresh_frequency: int, max_workers: int = 5) -> None:
        """Initializes an interface object with the book corresponding to market_id"""
        assert(isinstance(market_id, str))
        assert(isinstance(refresh_frequency, int))

        self.refresh_frequency = refresh_frequency
        self.market_id = market_id

        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        # TODO: Connect to trading API or something

        self.exchange = TestOrderbook()
        # TODO: this assumes the book will give us orderIDs.  Not sure how this will play IRL
        self.open_orders = {}   # maintain a map of order_id's corresponding to open orders (to cancel later)


    def cancel_orders(self, order_ids: list):
        """Takes a list of order id's and cancels them from the corresponding orderbook."""
        assert(isinstance(order_ids, list))

        # TODO: Cancel via API
        for id in order_ids:
            # TODO: Use self._executor to cancel an order
            #self._cancel_order(id, self.market_id)
            self.exchange.cancel(id)


    def place_orders(self, new_orders: list):
        """Takes a list of Order obj's and places them on the corresponding book."""
        assert(isinstance(new_orders, list))

        # TODO: Place via API
        for order in new_orders:
            # TODO: Use self._executor to place an order asynchronously
            #self._place_order(order, self.market_id)
            if order.is_buy:
                id = self.exchange.limit_buy(order.size, order.price)
            else:
                id = self.exchange.limit_sell(order.size, order.price)

            order.id = id
            self.open_orders[id] = order


    def get_orders(self) -> list:
        """Gets a list of the user's current open orders"""
        # TODO: Ask via API, in the future maybe maintain own list
        # Use self._executor to get orders
        open_ids = self.exchange.get_open_orders()  # gets order_ids
        orders = []
        for id in open_ids:
            orders.append(self.open_orders[id])
        return orders


    def get_spread(self) -> list:
        """Gets the best bid and ask and best price from this interface's orderbook"""
        # TODO: Query the book for all outcomes
        # TODO: Decide if this should be for only one outcome or not
        # Use self._executor to get spreads

        return [.51, .49], .5


    def get_market(self):
        """Returns some details about this market.  Will be used to check if this market actually exists"""
        # TODO: query for market details, should return None or something if doesn't exist
        # Use self._executor to query api

        return {"question": "What's .2+.3?"}
        # return None TODO: this is caught, maybe add as a unit test?

    def printOB(self):
        """TODO: TEMPORARY, just for testing"""
        self.exchange.printBAs(4)
        

    # TODO: use this to fetch the orderbook in the background with self.start()
    # def _get_account_details_thread(self):
    #     while True:
    #         try:

