"""Small installed-engine checks for market commutation and funding dependency."""

from copy import deepcopy

from kaggle_environments.envs.kaggriculture import kaggriculture as engine


def settle(orders, start_money=3000):
    market = engine._new_market()
    farm = engine._new_farm(10, start_money)
    private = engine._new_private()
    private["shed"]["WOOL"] = 3
    private["shed"]["FERTILIZER"] = 2
    successes = []
    for op, item, quantity in orders:
        filled = 0
        for _ in range(quantity):
            stock = market["inventory"][item]
            quote_at = stock - 1 if op == "BUY_PRODUCT" else stock
            price = (engine.CROPS[item]["seed"] if op == "BUY_SEED"
                     else engine.market_price(item, quote_at))
            if not engine._commit_unit(op, item, price, farm, private, market):
                break
            filled += 1
        successes.append(filled)
    return farm["money"], deepcopy(private), deepcopy(market["inventory"]), successes


def main():
    sales = [("SELL", "WOOL", 3), ("SELL", "FERTILIZER", 2)]
    forward = settle(sales)
    reverse = settle(list(reversed(sales)))
    assert forward[:3] == reverse[:3], (forward, reverse)
    buy_first = settle([("BUY_SEED", "STRAWBERRY", 1), ("SELL", "WOOL", 3)], 0)
    sell_first = settle([("SELL", "WOOL", 3), ("BUY_SEED", "STRAWBERRY", 1)], 0)
    assert buy_first[3] == [0, 3], buy_first
    assert sell_first[3] == [3, 1], sell_first
    print("Independent WOOL/FERTILIZER sales commute:", forward[0])
    print("Funding order changes filled strawberry seed purchase:",
          buy_first[3], "vs", sell_first[3])


if __name__ == "__main__":
    main()
