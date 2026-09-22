from kaggle_environments.envs.kaggriculture.kaggriculture import (
    market_price, MARKET_I0 as I0, CROPS, ANIMALS,
)

ITEMS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]
VOLUMES = [0, 25, 50, 75, 100, 150, 200, 300]

print(f"{'item':<12}" + "".join(f"{v:>7}" for v in VOLUMES))
print(f"{'':12}" + "".join(f"{'sold':>7}" for _ in VOLUMES))
print("-" * (12 + 7 * len(VOLUMES)))
for item in ITEMS:
    row = "".join(f"{market_price(item, I0 + v):>7}" for v in VOLUMES)
    print(f"{item:<12}{row}")

print(f"{'crop':<12}{'seed':>6}{'units':>7}{'days':>6}{'$/tile/day':>12}")
print("-" * 43)
for name, cd in CROPS.items():
    base = market_price(name, I0)
    days = max(cd["max_yield_day"], 1)
    units = cd["max_yield"]
    print(f"{name:<12}{cd['seed']:>6}{units:>7}{days:>6}{units * base / days:>12.0f}")

print(f"{'animal':<8}{'cost':>6}{'product':>9}{'base':>6}{'every':>7}{'per yield':>11}{'$/day':>8}")
print("-" * 55)
for name, a in ANIMALS.items():
    base = market_price(a["product"], I0)
    iv = a["interval"]
    per_yield = 1 + iv          # base 1, plus one banked CARE point per intervening day
    per_day = per_yield / iv
    print(f"{name:<8}{a['cost']:>6}{a['product']:>9}{base:>6}{iv:>7}{per_yield:>11}{per_day * base:>8.0f}")