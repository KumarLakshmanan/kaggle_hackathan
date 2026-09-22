import subprocess, sys
print(subprocess.run([sys.executable,"-m","pip","show","kaggle-environments"],
                     capture_output=True,text=True).stdout.split("Location")[0].strip())

from kaggle_environments.envs.kaggriculture.kaggriculture import (
    SHOPS, PRODUCTS, MARKET_I0, market_price,
)
try:
    from kaggle_environments.envs.kaggriculture.kaggriculture import MAX_SHOP_INSTANCES
    NEW = True
except ImportError:
    MAX_SHOP_INSTANCES, NEW = None, False
print("running on the NEW (1.32.6+) engine" if NEW else "running on an OLD (<=1.32.5) engine")
print("MAX_SHOP_INSTANCES =", MAX_SHOP_INSTANCES)

TURNS_PER_DAY, DAYS = 24, 30
SHOP_TICKS_PER_DAY = TURNS_PER_DAY // 4          # shops consume every 4 turns

exp_shop = {p: 0.0 for p in PRODUCTS}
for shop, prods in SHOPS.items():
    mult = 2 if len(prods) == 1 else 1
    for p in prods:
        exp_shop[p] += (MAX_SHOP_INSTANCES or 8) * (1/len(SHOPS)) * SHOP_TICKS_PER_DAY * mult

# town centre: OLD = 2 ticks/day x {1,2,4} by day; NEW = 1 tick/day x 1
old_centre_season = sum(2 * (4 if d>=20 else 2 if d>=10 else 1) for d in range(DAYS))
new_centre_season = DAYS * 1

print(f"town-centre consumption per product, whole season:")
print(f"   1.32.5 : {old_centre_season} units")
print(f"   1.32.6 : {new_centre_season} units      ({new_centre_season/old_centre_season-1:+.0%})")
print()
print(f"{'product':<12}{'shops/day':>10}{'centre/day OLD':>16}{'centre/day NEW':>16}"
      f"{'sink OLD':>10}{'sink NEW':>10}{'change':>9}")
for p in ["WHEAT","STRAWBERRY","MILK","CARROT","WOOL","EGG","TOMATO","MELON"]:
    old_c, new_c = 8, 1          # late-season town-centre rate, old vs new
    o, n = exp_shop[p] + old_c, exp_shop[p] + new_c
    print(f"{p:<12}{exp_shop[p]:>10.0f}{old_c:>16}{new_c:>16}{o:>10.0f}{n:>10.0f}{n/o-1:>8.0%}")

def realised(item, qty, drain_per_day, days=DAYS):
    """Sell `qty` units evenly across the season while the town drains `drain_per_day`."""
    inv, total, per_day = MARKET_I0, 0, qty/days
    carry = 0.0
    for d in range(days):
        carry += per_day
        while carry >= 1:
            total += market_price(item, int(inv)); inv += 1; carry -= 1
        inv -= drain_per_day                        # town eats
    return total/qty if qty else 0

print("avg $/unit realised, selling QTY evenly across the season   (OLD -> NEW, % change)\n")
print(f"{'product':<12}" + "".join(f"{f'Q={q}':>22}" for q in (100, 300, 600)))
for p in ["MELON","WOOL","STRAWBERRY","MILK","WHEAT"]:
    cells = []
    for q in (100, 300, 600):
        o = realised(p, q, exp_shop[p] + 4)   # old: centre averaged ~4-5/day over the season
        n = realised(p, q, exp_shop[p] + 1)
        cells.append(f"{o:>7.0f} ->{n:>6.0f} ({n/o-1:>+4.0%})")
    print(f"{p:<12}" + "".join(f"{c:>22}" for c in cells))