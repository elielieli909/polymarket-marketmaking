import logging
import itertools
import time
from market_maker.polymarketInterface import Order
from market_maker.limits import OrderLimits, OrderHistory

class Band:
    def __init__(self,
                min_margin: float,
                avg_margin: float,
                max_margin: float,
                min_amount: float,
                avg_amount: float,
                max_amount: float,):
        
        assert(isinstance(min_margin, float))
        assert(isinstance(avg_margin, float))
        assert(isinstance(max_margin, float))
        assert(isinstance(min_amount, float))
        assert(isinstance(avg_amount, float))
        assert(isinstance(max_amount, float))

        self.min_margin = min_margin
        self.avg_margin = avg_margin
        self.max_margin = max_margin
        self.min_amount = min_amount
        self.avg_amount = avg_amount
        self.max_amount = max_amount

        assert(self.min_amount >= 0)
        assert(self.avg_amount >= 0)
        assert(self.max_amount >= 0)
        assert(self.min_amount <= self.avg_amount)
        assert(self.avg_amount <= self.max_amount)

        assert(self.min_margin <= self.avg_margin)
        assert(self.avg_margin <= self.max_margin)
        assert(self.min_margin < self.max_margin)

    def includes(self, order: Order, current_price: float) -> bool:
        raise NotImplemented()

    def get_excessive_orders(self, orders: list, cur_price: float, is_inner_band: bool, is_outer_band: bool):
        """Return the orders which should be cancelled to bring this band's total order size below maxAmount"""
        orders_in_band = [order for order in orders if self.includes(order, cur_price)]
        size_in_band = sum(order.size for order in orders_in_band)
        
        if is_inner_band:
            sorting = lambda order: abs(order.price - cur_price)
            reverse = True

        elif is_outer_band:
            sorting = lambda order: abs(order.price - cur_price)
            reverse = False

        else:
            sorting = lambda order: order.size
            reverse = True

        orders_to_leave = sorted(orders_in_band, key=sorting, reverse=reverse)
        while sum(order.size for order in orders_to_leave) > self.max_amount:
            orders_to_leave.pop()

        result = set(orders_in_band) - set(orders_to_leave)

        return result


class BuyBand(Band):
    def __init__(self, dictionary: dict):
        super().__init__(min_margin=float(dictionary['minMargin']), 
                         avg_margin=float(dictionary['avgMargin']), 
                         max_margin=float(dictionary['maxMargin']), 
                         min_amount=float(dictionary['minAmount']), 
                         avg_amount=float(dictionary['avgAmount']), 
                         max_amount=float(dictionary['maxAmount']))

    def includes(self, order: Order, current_price: float) -> bool:
        price_min = current_price * (1 - self.min_margin)
        price_max = current_price * (1 - self.max_margin)
        return (order.price > price_max) and (order.price <= price_min)


class SellBand(Band):
    def __init__(self, dictionary: dict):
        super().__init__(min_margin=float(dictionary['minMargin']), 
                         avg_margin=float(dictionary['avgMargin']), 
                         max_margin=float(dictionary['maxMargin']), 
                         min_amount=float(dictionary['minAmount']), 
                         avg_amount=float(dictionary['avgAmount']), 
                         max_amount=float(dictionary['maxAmount']))

    def includes(self, order: Order, current_price: float) -> bool:
        price_min = current_price * (1 + self.min_margin)
        price_max = current_price * (1 + self.max_margin)
        return (order.price > price_min) and (order.price <= price_max)


class Bands:
    def read(config: dict, order_history: OrderHistory):
        """Pass a config dict (after being json parsed) to contruct a new Bands object"""
        assert(isinstance(config, dict))
        # Try to get the config
        try:
            buy_bands = list(map(BuyBand, config['buyBands']))
            sell_bands = list(map(SellBand, config['sellBands']))
            buy_limits = config['buyLimits'] if 'buyLimits' in config else []
            sell_limits = config['sellLimits'] if 'sellLimits' in config else []
        except Exception as e:
            logging.getLogger().exception(f'Invalid config file: ({e}).  Can\'t make any bands.')
            buy_bands = []
            sell_bands = []
            buy_limits = []
            sell_limits = []
            
        return Bands(buy_bands, sell_bands, buy_limits, sell_limits, order_history)


    def __init__(self, buy_bands: list, sell_bands: list, buy_limits: list, sell_limits: list, order_history: OrderHistory) -> None:
        self.buy_bands = buy_bands
        self.sell_bands = sell_bands
        self.buy_limits = OrderLimits(buy_limits, order_history)
        self.sell_limits = OrderLimits(sell_limits, order_history)

        if self._bands_overlap(buy_bands) or self._bands_overlap(sell_bands):
            logging.getLogger().warning('Bands in the config file overlap, so we aren\'t using any bands.')
            self.buy_bands = []
            self.sell_bands = []
        pass


    def _get_excessive_bids(self, my_bids, current_price) -> list:
        assert(isinstance(my_bids, list))
        assert(isinstance(current_price, float))

        bands = self.buy_bands

        for band in bands:
            for order in band.get_excessive_orders(my_bids, current_price, band==bands[0], band==bands[-1]):
                yield order

    def _get_excessive_asks(self, my_asks, current_price) -> list:
        assert(isinstance(my_asks, list))
        assert(isinstance(current_price, float))

        bands = self.sell_bands

        for band in bands:
            for order in band.get_excessive_orders(my_asks, current_price, band==bands[0], band==bands[-1]):
                yield order

    def _outside_any_band_orders(self, orders: list, bands: list, target_price: float):
        """Return buy or sell orders which need to be cancelled as they do not fall into any buy or sell band."""
        assert(isinstance(orders, list))
        assert(isinstance(bands, list))
        assert(isinstance(target_price, float))

        for order in orders:
            if not any(band.includes(order, target_price) for band in bands):
                yield order


    def get_cancellable_orders(self, my_orders, current_price) -> list:
        # 1. Cancel orders outside of any band
        # 2. For each band, cancel orders that exceed maxAmount
            # For inner band, cancel orders closest to current_price
            # For outer band, cancel orders farthest from current_price
            # For middle bands, cancel smallest sized orders

        my_bids = [order for order in my_orders if order.is_buy]
        my_asks = [order for order in my_orders if not order.is_buy]

        cancellable_bids = list(itertools.chain(self._get_excessive_bids(my_bids, current_price),
                                           self._outside_any_band_orders(my_bids, self.buy_bands, current_price)))
        cancellable_asks = list(itertools.chain(self._get_excessive_asks(my_asks, current_price),
                                           self._outside_any_band_orders(my_asks, self.sell_bands, current_price)))

        return cancellable_bids + cancellable_asks


    def _get_new_bids(self, my_bids, current_price, buy_balance):
        bands = self.buy_bands
        bid_limit = self.buy_limits.get_remaining_size(time.time())
        new_bids = []

        for band in bands:
            orders_in_band = [order for order in my_bids if band.includes(order, current_price)]
            cumulative_size = sum(order.size for order in orders_in_band)
            if cumulative_size < band.min_amount:
                price = current_price * (1 - band.avg_margin)
                size = min(band.avg_amount - cumulative_size, buy_balance, bid_limit)

                logging.getLogger().info(f'Attempting to place a new bid with price: {price}, size: {size}')
                new_bids.append(Order(size, price, is_buy=True))
        
        return new_bids

    
    def _get_new_asks(self, my_asks, current_price, sell_balance):
        bands = self.sell_bands
        ask_limit = self.sell_limits.get_remaining_size(time.time())
        new_asks = []

        for band in bands:
            orders_in_band = [order for order in my_asks if band.includes(order, current_price)]
            cumulative_size = sum(order.size for order in orders_in_band)
            if cumulative_size < band.min_amount:
                price = current_price * (1 + band.avg_margin)
                size = min(band.avg_amount - cumulative_size, sell_balance, ask_limit)

                logging.getLogger().info(f'Attempting to place a new ask with price: {price}, size: {size}')
                new_asks.append(Order(size, price, is_buy=False))

        return new_asks


    def get_new_orders(self, my_orders, current_price, buy_balance, sell_balance) -> list:
        # For each band:
            # If current value of orders there are less than avgAmount, place a new one of size /
            # min(avgAmount - cur_value, remaining_limit, remaining_balance) at avgMargin

        my_bids = [order for order in my_orders if order.is_buy]
        my_asks = [order for order in my_orders if not order.is_buy]

        return self._get_new_bids(my_bids, current_price, buy_balance) + self._get_new_asks(my_asks, current_price, sell_balance)

    @staticmethod
    def _bands_overlap(bands: list) -> bool:
        def two_bands_overlap(band1, band2):
            return band1.min_margin < band2.max_margin and band2.min_margin < band1.max_margin

        for band1 in bands:
            if len(list(filter(lambda band2: two_bands_overlap(band1, band2), bands))) > 1:
                return True

        return False