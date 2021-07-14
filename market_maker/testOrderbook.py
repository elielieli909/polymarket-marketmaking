class TestOrderbook:
    def __init__(self):
        self.ticks = [round(i*.001, 3) for i in range(0,1000)]
        self.bids = []
        self.asks = []
        for tick in self.ticks[:500]:
            self.bids.append([tick, 10])
        for tick in self.ticks[:500:-1]:
            self.asks.append([tick, 10])

        self.price = .5
        self.cur_id = 0

        self.open_orders = {} # mapping order_id to [limit, size]


    def limit_buy(self, size: int, limit: float):
        found = False
        for bid in self.bids:
            if limit == bid[0]:
                bid[1] += size
                found = True
        if not found and limit < self.asks[-1][0]:
            self.bids.append([limit, size])

        self.cur_id += 1
        self.open_orders[self.cur_id] = [limit, size]
        return self.cur_id

    def limit_sell(self, size: int, limit: float):
        found = False
        for ask in self.asks:
            if limit == ask[0]:
                ask[1] += size
                found = True
        if not found and limit > self.bids[-1][0]:
            self.bids.append([limit, size])
            
        self.cur_id += 1
        self.open_orders[self.cur_id] = [limit, size]
        return self.cur_id

    def market_buy(self, size: int):
        """Returns amount bought"""
        order_size = size
        while size > 0:
            ask = self.asks.pop()
            temp_ask = max(0, ask[1] - size)
            size -= ask[1] - temp_ask
            ask[1] = temp_ask
            if ask[1] != 0:
                self.asks.append(ask)
                self.price = ask[0]
            else:
                # Remove eaten limit from open_orders
                for id in self.open_orders:
                    if self.open_orders[id][0] == ask[0]:
                        del self.open_orders[id]
                        break

        return order_size - size

    def market_sell(self, size: int):
        """Returns amount sold"""
        order_size = size
        while size > 0:
            bid = self.bids.pop()
            temp_bid = max(0, bid[1] - size)
            size -= bid[1] - temp_bid
            bid[1] = temp_bid
            if bid[1] != 0:
                self.bids.append(bid)
                self.price = bid[0]
            else:
                # Remove eaten limit from open_orders
                for id in self.open_orders:
                    if self.open_orders[id][0] == bid[0]:
                        del self.open_orders[id]
                        break

        return order_size - size

    def cancel(self, id):
        if id in self.open_orders:
            limit_size = self.open_orders[id]
        else: return
        
        for b in self.bids:
            if b[0] == limit_size[0]:
                b[1] -= limit_size[1]
                return
        for a in self.asks:
            if a[0] == limit_size[0]:
                a[1] -= limit_size[1]
                return

    def get_open_orders(self):
        """returns a list of order_ids"""
        return self.open_orders.keys()

    def printBAs(self, depth: int):
        print(self.bids[len(self.bids) - depth:])
        print(self.asks[len(self.asks) - depth:])
        print(self.price)
        print(self.open_orders)
        return self.price


if __name__ == "__main__":
    ob = TestOrderbook()
    ob.limit_buy(100, .499)
    ob.limit_buy(75, .498)
    ob.limit_buy(50, .496)

    ob.limit_sell(100, .501)
    ob.limit_sell(75, .503)
    ob.limit_sell(50, .499)

    ob.market_buy(111)

    ob.limit_buy(2500, .502)
    ob.limit_sell(300, .502)

    ob.printBAs(4)