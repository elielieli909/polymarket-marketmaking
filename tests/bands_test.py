from configure_bands import SampleBands
from market_maker.myBands import Bands
from market_maker.polymarketInterface import Order

def creates_basic_bands():
    # given 
    config_details = SampleBands.basic_config()

    # when
    bands = Bands.read(config_details)
    price = .5
    orders = bands.get_new_orders([], price, 1000, 1000)

    # assert
    assert(len(orders) == 2)
    assert(orders[0].size == 30)
    assert(orders[0].price == .495)
    assert(orders[0].is_buy == True)
    assert(orders[1].size == 30)
    assert(orders[1].price == .505)
    assert(orders[1].is_buy == False)

def no_cancels_if_no_orders():
    # given
    config_details = SampleBands.basic_config()

    # when 
    bands = Bands.read(config_details)
    price = 0.5
    cancels = bands.get_cancellable_orders([], price)

    # assert
    assert(cancels == [])

def cancels_correct_orders():
    # given
    config_details = SampleBands.basic_config()

    # when (orders outside bands)
    bands = Bands.read(config_details)
    price = 0.5
    orders = bands.get_new_orders([], price, 1000, 1000)
    orders[0].price = 0.2 # outside
    # Give ID's (normally given by polymarketInterface on an order confirmation)
    orders[0].id = 0
    orders[1].id = 1
    cancels = bands.get_cancellable_orders(orders, price)
    
    #assert
    assert(len(cancels) == 1)
    assert(cancels[0].id == 0)

    # when (too many orders in band)
    bands = Bands.read(config_details)
    price = 0.5
    orders = bands.get_new_orders([], price, 1000, 1000)
    orders.append(Order(100, .495, True))
    # Give ID's (normally given by polymarketInterface on an order confirmation)
    orders[0].id = 0
    orders[1].id = 1
    orders[2].id = 2
    cancels = bands.get_cancellable_orders(orders, price)
    
    #assert
    assert(len(cancels) == 1)
    assert(cancels[0].id == 2)


if __name__ == '__main__':
    creates_basic_bands()
    no_cancels_if_no_orders()
    cancels_correct_orders()