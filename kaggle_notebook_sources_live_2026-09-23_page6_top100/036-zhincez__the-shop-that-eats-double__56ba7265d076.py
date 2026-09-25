# base prices and shop lists, taken from the engine's own constants
BASE_PRICE = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250,
              "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100}

SHOPS = {
    "YARN_STORE": ["WOOL"],
    "PET_CAFE": ["CARROT"],
    "BAKERY": ["EGG", "WHEAT"],
    "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
    "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"],
    "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"],
    "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"],
    "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"],
}

TURNS_PER_DAY, SHOP_PERIOD = 24, 4


def drain_per_day(shop):
    """Units and coins a shop removes from the market each day.

    A shop consumes its whole list every SHOP_PERIOD turns, and a shop with exactly
    one item consumes at double weight. The coin column is the one that ranks towns.
    """
    items = SHOPS[shop]
    weight = 2 if len(items) == 1 else 1
    pulls = TURNS_PER_DAY / SHOP_PERIOD
    units = weight * pulls * len(items)
    coins = sum(weight * pulls * BASE_PRICE[i] for i in items)
    return units, coins


rows = sorted(((s,) + drain_per_day(s) for s in SHOPS), key=lambda r: -r[2])
print(f"{'shop':16}{'items':>7}{'units/day':>12}{'coins/day':>12}")
for s, u, c in rows:
    single = " (double)" if len(SHOPS[s]) == 1 else ""
    print(f"{s:16}{len(SHOPS[s]):>7}{u:>12,.0f}{c:>12,.0f}{single}")

top, bottom = rows[0], rows[-1]
print()
print(f"deepest sink : {top[0]} at {top[2]:,.0f} coins/day")
print(f"shallowest   : {bottom[0]} at {bottom[2]:,.0f} coins/day -- and it is a DOUBLE shop")
print(f"ratio        : {top[2] / bottom[2]:.1f}x")