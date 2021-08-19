"""
Interfaces with Polymarket's orderbooks.  Analogous to Maker's orderbook_manager
TODO: Could make this hold it's own state like Maker's in order to rely less on an external get_orders API from polymarket
"""

import logging
import threading
import requests
import utils
from concurrent.futures import ThreadPoolExecutor

from market_maker.testOrderbook import TestOrderbook

class Order:
    def __init__(self, size: int, price: float, is_buy: bool) -> None:
        self.size = size
        self.price = price
        self.is_buy = is_buy
        self.id = None


class PolymarketInterface:
    def __init__(self, fpmm_address: str, asset_id: str, refresh_frequency: int, max_workers: int = 5) -> None:
        """Initializes an interface object with the book corresponding to market_id"""
        assert(isinstance(fpmm_address, str))
        assert(isinstance(asset_id, str))
        assert(isinstance(refresh_frequency, int))

        self.refresh_frequency = refresh_frequency
        self.asset_id = asset_id
        self.fpmm_address = fpmm_address

        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()

        self.open_orders = {}   # maintain a map of order_id's corresponding to open orders (to cancel later)


    def cancel_orders(self, order_ids: list):
        """Takes a list of order id's and cancels them from the corresponding orderbook."""
        assert(isinstance(order_ids, list))

        # TODO: Cancel via API
        for id in order_ids:
            # TODO: Use self._executor to cancel an order
            #self._cancel_order(id, self.market_id)
            pass


    def place_orders(self, new_orders: list):
        """Takes a list of Order obj's and places them on the corresponding book."""
        assert(isinstance(new_orders, list))

        for order in new_orders:
            # TODO: Use self._executor to place an order asynchronously
            id = self._place_order(order.price, order.size, order.is_buy, self.market_id)

            order.id = id
            self.open_orders[id] = order


    def get_orders(self) -> list:
        """Gets a list of the user's current open orders"""
        # TODO: Ask via API, in the future maybe maintain own list
        # Use self._executor to get orders
        # open_ids = self.exchange.get_open_orders()  # gets order_ids
        orders = []
        for id in []:
            orders.append(self.open_orders[id])
        return orders


    def get_price(self) -> float:
        """Gets the best bid and ask and best price from this interface's orderbook"""
        # Use self._executor to get spreads
        res = requests.get(utils.TRACKER_URL + '/midpoint', params={"market": self.fpmm_address, "tokenID": self.asset_id})

        return res.json()['mid']


    def get_market(self):
        """Check if this market actually exists"""
        # TODO: query for market details, should return None or something if doesn't exist
        # Use self._executor to query api

        res = requests.get(utils.TRACKER_URL + '/markets')  # This currently (8/18) returns a list of fpmmaddresses
        markets = res.json()

        if self.fpmm_address not in markets:
            return None

        return True
        # return None TODO: this is caught, maybe add as a unit test?

    def _place_order(self, price, size, is_bid, takerAssetID) -> int:
        """Places an order via relay contract.  Returns the order ID of the newly placed order"""
        makerAmount = size
        if is_bid:
            takerAmount = size / price
            body = {
                "maker": "",
                "makerAssetType": "erc20",
                "makerAmount": makerAmount,
                "takerAssetType": "erc1155", 
                "takerAmount": takerAmount,
                "takerAssetID": takerAssetID,
            }
        else:
            takerAmount = size * price
            body = {
                "maker": "",
                "makerAssetType": "erc1155",
                "makerAmount": makerAmount,
                "takerAssetType": "erc20", 
                "takerAmount": takerAmount,
                "takerAssetID": -1,
            }

        # Post the order to the relay contract via the dclob server; TODO: update to whatever method we use to post
        res = requests.post(utils.ONCHAIN_ORDER_POST_URL, data=body)

        if res.status_code != 200:
            logging.getLogger().log(logging.WARNING, "Order could not be posted")
            return -1

        return res.json()['orderId']

