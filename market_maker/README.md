# Source Code Walkthrough

## PolymarketInterface

This file is responsible for handling all interactions with the LOB:
* Placing / cancelling orders
    - Placing an order requires specification of the price and size, and returns an order_id.
    - Cancelling an order requires specifying the order_id of the order to be cancelled.

* Check if a market exists
    - Provide a "pair name", should return some details about the market if it exists and None otherwise

* Get the current spread/market price of a particular market

* Get the user's current open orders
    - returns a list of order_ids

## MM

This file is responsible for the main logic of the strategy; it interacts with the PolymarketInterface to connect to the desired market, get price data, and place/cancel orders.  It also interacts with Bands, which tells it which orders should be cancelled to maintain the user's band requirements as well as what new orders to place.

## Bands

This file is responsible for the Bands logic of the strategy;  it reads the user's config file and helps MM figure out what orders to cancel/place given the user's current open orders, the current market price (congruently, the current bands), the user's token balances, and the user's time-enforced limits (specified in bands.json)