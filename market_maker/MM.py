import argparse
import sys
import json
import logging
import time

from market_maker.myBands import Bands
from market_maker.polymarketInterface import PolymarketInterface, Order

class MM:
    def __init__(self, args: list):
        parser = argparse.ArgumentParser(prog='polymarket-market-maker')
        # Read args
        parser.add_argument("--config", type=str, required=True, 
                            help="Configuration file specifying Band details")

        parser.add_argument("--market", type=str, required=True,
                            help="The id (?) of the market you want to make markets on")

        parser.add_argument("--orders-refresh-frequency", type=int, default=3,
                            help="The number of seconds to wait before querying order and balance details")

        parser.add_argument("--debug", dest='debug', action='store_true',
                            help="Enable debug output")

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
        self.market_interface = PolymarketInterface(self.arguments.market, self.arguments.orders_refresh_frequency)
        if self.market_interface.get_market() is None:
            logging.getLogger().error('Couldn\'t find a market with id: %s', self.arguments.market)
            exit(-1)

        # Connect to exchange api TODO: need details from Liam
        # Figure out if we have any open orders already, cancel them I believe TODO: needs API details
        # Set up price/spread/control(can_buy/sell?) TODO: maybe initiate a ws for price feeds or set up background polling
        pass


    def main(self):
        # wait 10 seconds to let the websockets get set up
        # Every second, synchronize_orders()
        # On shutdown (InterruptHandler?) cancel all orders
        while True:
            # TODO: Probably make this a thread + figure out how to catch Interrupts
            self.synchronize_orders()
            time.sleep(1)
            self.market_interface.printOB()
        # print(type(self.config_details['buyBands']))


    def synchronize_orders(self):
        # Get Bands details
        bands = Bands.read(self.config_details)
        # get Orderbook state and current price
        users_orders = self.market_interface.get_orders() # list of Orders
        spread, price = self.market_interface.get_spread()

        # Ask the bands what orders we want to cancel given current price and our open orders
        cancellable_orders = bands.get_cancellable_orders(users_orders, price) # returns list of Orders
        # Cancel them
        self.market_interface.cancel_orders([o.id for o in cancellable_orders]) # takes order_ids
        # Don't place new ones if the orderbook interface is busy (? I guess in case a cancel fails)
        # TODO: Figure this out

        # Ask the bands what new orders we want to place, given our open orders, our available balance, and our rate limits (defined in config)
        orders_to_place = bands.get_new_orders(users_orders, price, 1000, 1000)
        # Place them
        self.market_interface.place_orders(orders_to_place)


if __name__ == "__main__":
    MM(sys.argv[1:]).main()