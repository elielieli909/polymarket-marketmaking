import argparse
import sys
import json
import logging
import time

from market_maker.Bands import Bands
from market_maker.polymarketInterface import PolymarketInterface, Order
from market_maker.limits import OrderHistory

class MM:
    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='polymarket-market-maker')
        # Read args
        parser.add_argument("--config", type=str, required=True, 
                            help="Configuration file specifying Band details")

        parser.add_argument("--market", type=str, required=True,
                            help="The FPMM address of the desired market")

        parser.add_argument("--tokenID", type=str, required=True,
                            help="The tokenID specifying which conditional token markets will be made for")

        self.arguments = parser.parse_args(args)

        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(message)s',
                        level=(logging.DEBUG if self.arguments.debug else logging.INFO))

        # Load the config file using simple JSON -> dict; TODO: later on maybe we should implement the ReloadableConfig
        try:
            with open(self.arguments.config) as config_file:
                self.config_details = json.load(config_file)
        except Exception as e:
            logging.getLogger().error('Error opening config file: aborting')
            exit(-1)

        # Grab market we want to trade on
        self.market_interface = PolymarketInterface(self.arguments.market, self.arguments.tokenID, self.arguments.orders_refresh_frequency)
        if self.market_interface.get_market() is None:
            logging.getLogger().error('Couldn\'t find a market with id: %s', self.arguments.market)
            exit(-1)


    def main(self):
        # Every second, synchronize_orders()
        # On shutdown (InterruptHandler?) cancel all orders
        while True:
            # TODO: Probably make this a thread + figure out how to catch Interrupts
            self.synchronize_orders()
            time.sleep(1)


    def synchronize_orders(self):
        orders = []
        order_hist = OrderHistory()
        for o in orders: order_hist.add_order({'timestamp': o['timestamp'], 'size': o['size']})
        # Get Bands details
        bands = Bands.read(self.config_details, order_hist)
        # get Orderbook state and current price
        users_orders = self.market_interface.get_orders() # list of Orders
        price = self.market_interface.get_price()

        # Ask the bands what orders we want to cancel given current price and our open orders
        cancellable_orders = bands.get_cancellable_orders(users_orders, price) # returns list of Orders
        # Cancel them
        self.market_interface.cancel_orders([o.id for o in cancellable_orders]) # takes order_ids
        # Don't place new ones if the orderbook interface is busy (? I guess in case a cancel fails)
        # TODO: Figure this out

        # Ask the bands what new orders we want to place, given our open orders, our available balance, and our rate limits (defined in config)
        buy_balance = PolymarketInterface.get_buy_balance()
        sell_balance = PolymarketInterface.get_sell_balance()
        orders_to_place = bands.get_new_orders(users_orders, price, buy_balance, sell_balance)
        # Place them
        self.market_interface.place_orders(orders_to_place)


if __name__ == "__main__":
    MM(sys.argv[1:]).main()