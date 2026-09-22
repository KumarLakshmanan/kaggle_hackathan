import math
from kaggle_environments.envs.kaggriculture.kaggriculture import (
    SHOPS, PRODUCTS, TOWN_CENTER_PRODUCTS, TOWN_CENTER_DEMAND_SCHEDULE,
    MARKET_PARAMS, MARKET_I0, market_price, CROPS, ANIMALS,
)

TURNS_PER_DAY, DAYS = 24, 30
SHOP_SELL_INTERVAL   = 4    # every 4 turns  -> 6 ticks/day
CENTER_SELL_INTERVAL = 12   # every 12 turns -> 2 ticks/day

print("Shops in the game:")
for name, prods in SHOPS.items():
    tag = "  (single-product -> consumes 2x)" if len(prods) == 1 else ""
    print(f"  {name:<16} {', '.join(prods)}{tag}")

shop_per_day = {p: 0 for p in PRODUCTS}
for shop, prods in SHOPS.items():
    mult = 2 if len(prods) == 1 else 1
    for p in prods:
        shop_per_day[p] += (TURNS_PER_DAY // SHOP_SELL_INTERVAL) * mult

n_shops_wanting = {p: sum(1 for s in SHOPS.values() if p in s) for p in PRODUCTS}

print(f"{'product':<12} {'shops':>6} {'shop units/day':>15} {'town-centre/day (d0/d10/d20)':>30}")
print("-" * 68)
for p in PRODUCTS:
    if p in TOWN_CENTER_PRODUCTS:
        base = TURNS_PER_DAY // CENTER_SELL_INTERVAL      # 2 ticks/day
        centre = f"{base} / {base*2} / {base*4}"
    else:
        centre = "none - excluded"
    print(f"{p:<12} {n_shops_wanting[p]:>6} {shop_per_day[p]:>15} {centre:>30}")

season_town_demand = {}
for p in PRODUCTS:
    total = 0
    # shops unlock every 3 days; assume the i-th unlock is active from that day onward
    unlock_days = [d for d in range(1, DAYS + 1) if d % 3 == 0]
    shops_sorted = list(SHOPS.items())
    for i, (shop, prods) in enumerate(shops_sorted):
        if i >= len(unlock_days) or p not in prods:
            continue
        mult = 2 if len(prods) == 1 else 1
        active_days = DAYS - unlock_days[i]
        total += active_days * (TURNS_PER_DAY // SHOP_SELL_INTERVAL) * mult
    if p in TOWN_CENTER_PRODUCTS:
        for d in range(DAYS):
            m = next(mm for thr, mm in TOWN_CENTER_DEMAND_SCHEDULE if d >= thr)
            total += (TURNS_PER_DAY // CENTER_SELL_INTERVAL) * m
    season_town_demand[p] = total

print(f"{'product':<12} {'town eats/season':>18} {'price if you sell NOTHING':>27}")
print("-" * 60)
for p in sorted(PRODUCTS, key=lambda x: -season_town_demand[x]):
    px = market_price(p, MARKET_I0 - season_town_demand[p])
    base = MARKET_PARAMS[p]["base"]
    print(f"{p:<12} {season_town_demand[p]:>18} {px:>18} ({px/base:>4.2f}x base)")

def revenue_curve(item, qty):
    """Cumulative revenue from selling `qty` units into your own price impact."""
    inv, total, out = MARKET_I0, 0, []
    for i in range(qty):
        px = market_price(item, inv)
        total += px
        if px > 1:          # sales at the $1 floor do not add to market inventory
            inv += 1
        out.append(total)
    return out

print(f"{'product':<12} " + " ".join(f"{f'Q={q}':>9}" for q in (25, 50, 100, 200, 400)))
print("-" * 62)
for p in ["MELON", "WOOL", "MILK", "STRAWBERRY", "TOMATO", "CARROT", "FERTILIZER", "WHEAT", "EGG"]:
    c = revenue_curve(p, 400)
    print(f"{p:<12} " + " ".join(f"{c[q-1]:>9,}" for q in (25, 50, 100, 200, 400)))
print()
print("Read the rows across: where the number stops growing is where that product dies.")
print("MELON earns ~21.7k on its first 100 units and only ~5k more on the next 100.")
print("EGG is the only product still paying roughly full price at Q=400.")

def sellable_qty(item, market_inventory, have, reserve):
    """Largest n <= have such that all n units still price at >= reserve."""
    lo, hi = 0, have
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if market_price(item, market_inventory + mid - 1) >= reserve:
            lo = mid
        else:
            hi = mid - 1
    return lo

# You are holding 60 wool. How many should you sell right now?
for opp_dumped in (0, 40, 100):
    inv = MARKET_I0 + opp_dumped
    n = sellable_qty("WOOL", inv, 60, reserve=95)
    print(f"opponent already sold {opp_dumped:>3} wool -> price ${market_price('WOOL', inv):>3}"
          f" -> sell {n:>2} of my 60 now, hold the rest")