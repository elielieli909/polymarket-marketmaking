# Making Markets on Polymarket's Central Limit Order Book

Market making is a market-neutral trading strategy which attempts to profit by providing liquidity (placing orders above and below the market price) to a central limit orderbook marketplace.  

Here is the code for a completely automated market-making bot, which can be used to trade on Polymarket.

## Instructions

To start, edit the bands.json configuration file to suit your needs.  This is what a sample bands.json file looks like:

```json
{
    "buyBands": [
        {
            "minMargin": 0.005,
            "avgMargin": 0.01,
            "maxMargin": 0.02,
            "minAmount": 20.0,
            "avgAmount": 30.0,
            "maxAmount": 40.0
        },
        {
            "minMargin": 0.02,
            "avgMargin": 0.025,
            "maxMargin": 0.05,
            "minAmount": 40.0,
            "avgAmount": 60.0,
            "maxAmount": 80.0
        }
    ],
    "buyLimits": [],
    "sellBands": [
        {
            "minMargin": 0.005,
            "avgMargin": 0.01,
            "maxMargin": 0.02,
            "minAmount": 20.0,
            "avgAmount": 30.0,
            "maxAmount": 40.0
        },
        {
            "minMargin": 0.02,
            "avgMargin": 0.025,
            "maxMargin": 0.05,
            "minAmount": 40.0,
            "avgAmount": 60.0,
            "maxAmount": 80.0
        }
    ],
    "sellLimits": []
}
```

"buyBands" and "sellBands" represent areas in the order book surrounding the current market price where you want to place your resting buy and sell orders respectively.  The bot attempts to maintain at least minAmount (collective size of orders) and at most maxAmount within the specified margins, where margins represent a percent offset from the market price.  For example, if an outcome is trading at 0.50 USDC, for the given configuration file above four bands are created:

1. Average bid size of 30 tokens between prices (0.5 * (1 - 0.005)) = 0.4975 USDC and (0.5 * (1 - 0.02)) = 0.49 USDC
2. Average bid size of 60 tokens between prices (0.5 * (1 - 0.02)) = 0.49 USDC and (0.5 * (1 - .05)) = 0.475 USDC
3. Average offer size of 30 tokens between prices (0.5 * (1 + 0.005)) = 0.5025 USDC and (0.5 * (1 + 0.02)) = 0.51 USDC
4. Average offer size of 60 tokens between prices 0.51 USDC and 0.525 USDC.

Every second the bot reads the market price of the token being traded and decides whether to cancel or place new orders.  For example if the market price moves from 0.5 USDC per token to 0.49 USDC per token, new bands are created with the specified margins about the new 0.49 USDC mid price.  

The process for cancelling orders goes like this:

1. If an order is outside of any bands (either between your inner two bands or outside your two outer bands), cancel it.
2. If there are enough orders within a band such that that band's maxAmount is breached:
    - If the band is an inner band (smallest margins) it will cancel orders closest to the market price until maxAmount is reached
    - If the band is an outer band (largest margins) it will cancel orders furthest from the market price
    - If the band is neither (the second of three bands, for example) it will cancel orders in order of size, smallest to largest

The process for adding new orders goes like this:

For each band,
1. If the sum of order sizes within the band are less than avgAmount, place a new order at avgMargin to either make up the differnece and achieve avgAmount, use your remaining collateral to place the order, or if order limits were specified, use the remaining limit for the specified time frame. 

TODO: explain limits

## Work left to do:
1. Have the user provide his wallet's private key via a command line argument in MM.py
2. Somehow use the user's wallet to sign limit orders to the Polymarket relayer contract
3. Implement a way to get the user's ERC1155 and USDC balance; maintain this as a property of the MM class and pass it to bands.get_new_orders() in synchronize_orders()
4. Figure out how to cancel on-chain orders, implement this in polymarketInterface.cancel_orders()
5. Get the user's currently open orders.  Orders that were posted earlier that have since been filled should not be included, or reflect their new size
5. Testing
6. All the TODO's; these are mostlly for better performance