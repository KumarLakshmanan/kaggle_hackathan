# Read the SHIPPED version WITHOUT importing the package, then upgrade before any import.
# (Upgrading in-process and calling importlib.reload on kaggle_environments does not work:
#  it has many submodules and the reload raises ImportError partway through. Ask me how I
#  know -- that was version 2 of this notebook.)
import importlib.metadata as md_
shipped = md_.version("kaggle-environments")
print("kaggle-environments as shipped by this image:", shipped)

!pip install -q -U kaggle-environments 2>/dev/null | tail -1

from kaggle_environments.envs.kaggriculture import kaggriculture as K

now = md_.version("kaggle-environments")
old = hasattr(K, "TOWN_CENTER_DEMAND_SCHEDULE")   # removed in 1.32.6
new = hasattr(K, "MAX_SHOP_INSTANCES")            # added in 1.32.6

print(f"shipped: {shipped}     after upgrade: {now}")
print(f"TOWN_CENTER_DEMAND_SCHEDULE present : {old}   (removed in 1.32.6)")
print(f"MAX_SHOP_INSTANCES present          : {new}   (added in 1.32.6)")
print()
print("VERDICT:", "STALE - pre-rebalance engine" if old else "CURRENT - post-rebalance engine")
if shipped != now:
    print(f"NOTE: this image shipped {shipped}. If you had not upgraded, every number")
    print("      below would describe the pre-rebalance economy.")

TURNS_PER_DAY, DAYS = 24, 30

# --- the OLD (1.32.5) values, recorded here for comparison. Not importable any more. ---
OLD_CENTER_INTERVAL = 12                      # -> 2 ticks/day
OLD_CENTER_SCHEDULE = [(20, 4), (10, 2), (0, 1)]

old_centre_season = sum(
    (TURNS_PER_DAY // OLD_CENTER_INTERVAL) * next(m for thr, m in OLD_CENTER_SCHEDULE if d >= thr)
    for d in range(DAYS)
)

# --- the CURRENT values, read from your installed engine ---
new_centre_per_day = TURNS_PER_DAY // 24      # townCenterSellInterval default is now 24
new_centre_season  = new_centre_per_day * DAYS

print(f"town centre, per product, per SEASON:  {old_centre_season}  ->  {new_centre_season}"
      f"   ({new_centre_season/old_centre_season - 1:+.0%})")

SHOP_SELL_INTERVAL = 4                        # 6 ticks/day
ticks_per_day = TURNS_PER_DAY // SHOP_SELL_INTERVAL
n_shops = len(K.SHOPS)

old_shop, new_shop = {}, {}
for p in K.PRODUCTS:
    old_shop[p] = sum(ticks_per_day * (2 if len(pr) == 1 else 1)
                      for pr in K.SHOPS.values() if p in pr)
    # with replacement: each of MAX_SHOP_INSTANCES draws is this shop with prob 1/n_shops
    max_inst = getattr(K, "MAX_SHOP_INSTANCES", n_shops)
    new_shop[p] = sum(max_inst * (1 / n_shops) * ticks_per_day * (2 if len(pr) == 1 else 1)
                      for pr in K.SHOPS.values() if p in pr)

old_centre_day = 2 * 4                        # late-season worst case under the old 4x
rows = []
for p in K.PRODUCTS:
    if p not in K.TOWN_CENTER_PRODUCTS and new_shop[p] == 0:
        old_t, new_t = old_shop[p], new_shop[p]           # fertilizer: no demand either way
    else:
        old_t = old_shop[p] + (old_centre_day if p in K.TOWN_CENTER_PRODUCTS else 0)
        new_t = new_shop[p] + (1 if p in K.TOWN_CENTER_PRODUCTS else 0)
    rows.append((p, old_t, new_t))

print(f"{'product':<12}{'old sink/day':>14}{'new sink/day':>14}{'change':>10}")
print("-" * 50)
for p, o, n in sorted(rows, key=lambda r: (r[2] - r[1]) / max(r[1], 1)):
    ch = f"{n/o - 1:+.0%}" if o else "  n/a"
    print(f"{p:<12}{o:>14.0f}{n:>14.1f}{ch:>10}")

# How far can you sell each product before the price collapses? (unchanged by the
# rebalance -- the CURVE is the same; what changed is how fast the town drains it back)
def avg_realised(item, qty):
    inv, total = K.MARKET_I0, 0
    for _ in range(qty):
        px = K.market_price(item, inv)
        total += px
        if px > 1:                 # sales at the $1 floor do not add to inventory
            inv += 1
    return total / qty

print(f"{'product':<12}" + "".join(f"{f'Q={q}':>9}" for q in (25, 50, 100, 200, 400)))
print("-" * 58)
for p in ["MELON", "WOOL", "MILK", "STRAWBERRY", "TOMATO", "CARROT", "WHEAT", "EGG"]:
    print(f"{p:<12}" + "".join(f"{avg_realised(p, q):>9.0f}" for q in (25, 50, 100, 200, 400)))
print()
print("Average $/unit realised when YOU sell Q units into your own price impact.")
print("Pair this with the sink table above: the sink is how fast the town undoes it.")