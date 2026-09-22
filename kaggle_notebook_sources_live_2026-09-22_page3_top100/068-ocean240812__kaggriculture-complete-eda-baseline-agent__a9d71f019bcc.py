import pandas as pd
import numpy as np

crops = [
    # name, seed_cost, base_price, first_yield, max_yield, yield_type, subsequent_interval
    ('Wheat',       10,  25,  2, 6, 'one-time', None),
    ('Carrot',      20,  35,  2, 4, 'one-time', None),
    ('Tomato',      50,  60,  8, 4, 'ongoing', 1),  # daily
    ('Strawberry', 100, 120, 10, 4, 'ongoing', 2),  # every 2 days
    ('Melon',       80, 250, 10, 6, 'one-time', None),
]
df_crops = pd.DataFrame(crops, columns=[
    'Crop', 'SeedCost', 'BasePrice', 'FirstYieldDay', 'MaxYield', 'Type', 'SubseqInterval'
])

# Compute economics assuming 24-day horizon (typical season)
HORIZON = 24

def total_yield(row):
    if row.Type == 'one-time':
        return row.MaxYield  # one harvest
    else:
        # ongoing: yield per interval, capped at MaxYield cumulative
        days_of_yield = max(0, HORIZON - row.FirstYieldDay)
        n_yields = days_of_yield // row.SubseqInterval
        return min(n_yields * 1, row.MaxYield)  # base 1 per yield, capped

def gross_revenue(row):
    return total_yield(row) * row.BasePrice

def net_profit(row):
    return gross_revenue(row) - row.SeedCost

def roi(row):
    return net_profit(row) / row.SeedCost * 100

def yield_per_tile_per_day(row):
    return total_yield(row) / HORIZON

df_crops['TotalYield_24d'] = df_crops.apply(total_yield, axis=1)
df_crops['GrossRev'] = df_crops.apply(gross_revenue, axis=1)
df_crops['NetProfit'] = df_crops.apply(net_profit, axis=1)
df_crops['ROI_%'] = df_crops.apply(roi, axis=1)
df_crops['YieldPerTilePerDay'] = df_crops.apply(yield_per_tile_per_day, axis=1)

df_crops.style.background_gradient(cmap='YlGn', subset=['ROI_%','NetProfit','YieldPerTilePerDay'])

import matplotlib.pyplot as plt
import numpy as np

# Per-resource market parameters (from README)
market_params = {
    'Wheat':       {'base': 25,  'T': 400, 'below_func': 'sqrt', 'below_target': 0.80, 'above_func': 'log',  'above_target': 0.20},
    'Carrot':      {'base': 35,  'T': 450, 'below_func': 'log',  'below_target': 0.20, 'above_func': 'sqrt', 'above_target': 0.70},
    'Tomato':      {'base': 60,  'T': 200, 'below_func': 'linear','below_target': 0.40, 'above_func': 'sqrt', 'above_target': 0.60},
    'Strawberry': {'base': 120, 'T': 100, 'below_func': 'sqrt', 'below_target': 0.70, 'above_func': 'linear','above_target': 1.60},
    'Melon':       {'base': 250, 'T': 300, 'below_func': 'log',  'below_target': 0.20, 'above_func': 'sq',   'above_target': 3.60},
    'Egg':         {'base': 50,  'T': 332, 'below_func': 'linear','below_target': 0.40, 'above_func': 'log',  'above_target': 0.20},
    'Milk':        {'base': 160, 'T': 122, 'below_func': 'sqrt', 'below_target': 0.60, 'above_func': 'linear','above_target': 1.60},
    'Wool':        {'base': 200, 'T': 105, 'below_func': 'log',  'below_target': 0.20, 'above_func': 'sq',   'above_target': 3.20},
    'Fertilizer': {'base': 100, 'T': 200, 'below_func': 'linear','below_target': 0.40, 'above_func': 'linear','above_target': 0.40},
}

def shape_fn(name, x):
    x = max(x, 0)
    if name == 'linear': return x
    if name == 'sqrt':   return np.sqrt(x)
    if name == 'sq':     return x * x
    if name == 'log':    return np.log(1 + x)
    if name == 'log10':  return np.log10(1 + x)
    return x

def price_curve(base, T, below_func, below_target, above_func, above_target, inv):
    I0 = 10000
    diff = inv - I0
    if diff < 0:
        # scarcity
        amp = below_target * base / shape_fn(below_func, T)
        return max(1, round(base + amp * shape_fn(below_func, -diff)))
    else:
        # glut
        amp = above_target * base / shape_fn(above_func, T)
        return max(1, round(base - amp * shape_fn(above_func, diff)))

# Plot price curves for the 4 most important products
fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
key_resources = ['Wheat', 'Strawberry', 'Melon', 'Milk']

for ax, res in zip(axes.flat, key_resources):
    p = market_params[res]
    inv_range = np.linspace(9500, 10500, 200)  # I0 ± 500
    prices = [price_curve(p['base'], p['T'], p['below_func'], p['below_target'],
                          p['above_func'], p['above_target'], i) for i in inv_range]
    ax.plot(inv_range - 10000, prices, linewidth=2.5, color='#2E8B57')
    ax.axvline(0, color='gray', linestyle='--', alpha=0.5, label='I0 (equilibrium)')
    ax.axhline(p['base'], color='orange', linestyle=':', alpha=0.7, label=f"base=${p['base']}")
    ax.axhline(1, color='red', linestyle=':', alpha=0.5, label='$1 floor')
    ax.set_xlabel('Inventory − I0 (negative = scarcity)')
    ax.set_ylabel('Sell Price ($)')
    ax.set_title(f"{res} — base ${p['base']}, glut_func={p['above_func']}, glut_target={p['above_target']}", fontweight='bold')
    ax.grid(alpha=0.3)
    ax.legend(loc='upper right', fontsize=9)

plt.suptitle('Market Price Curves — Asymmetric Scarcity vs Glut', fontsize=14, fontweight='bold')
plt.savefig('/kaggle/working/market_price_curves.png', dpi=120, bbox_inches='tight')
plt.show()
print("✓ Saved market_price_curves.png")

# Farm hand cost analysis
# Cost is farmHandCostMult * fib(n) where n = hires_today
# Default farmHandCostMult = 1, fib sequence: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55

fib_seq = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
hires = list(range(1, 13))
costs = fib_seq[:12]
cumulative = np.cumsum(costs)

print("Hire # | Cost today | Cumulative cost | Actions gained (24/day each)")
print("-" * 70)
for i, (h, c, cum) in enumerate(zip(hires, costs, cumulative)):
    print(f"  {h:>3}  |   ${c:>4}     |     ${cum:>5}        |   {h*24} extra turns/day")

print(f"\nAnalysis:")
print(f"- 1st hire: $1 (almost free) — almost always worth it")
print(f"- 2nd hire: $1 (also free) — almost always worth it")
print(f"- 3rd hire: $2 — pays for itself with 1 watering action")
print(f"- 4th hire: $3 — still cheap if you have ≥10 tiles needing care")
print(f"- 5th hire: $5 — borderline, only if late game with many animals")
print(f"- 6th+ hire: $8+ — rarely worth it; shed overflow + farm clutter")
print(f"\nOptimal: 2-3 hands/day = $4 total, +48-72 turns/day = enough to manage 25-tile farm")

shops = [
    ('Bakery',         ['Eggs', 'Wheat'],              False),
    ('Pizza Shop',     ['Milk', 'Tomatoes', 'Wheat'],  False),
    ('Brunch Spot',    ['Eggs', 'Wheat', 'Strawberry'], False),
    ('Yarn Store',     ['Wool'],                       True),   # 2x
    ('Ice Cream Shop', ['Strawberry', 'Milk', 'Wheat'], False),
    ('Pet Cafe',       ['Carrots'],                    True),   # 2x
    ('Smoothie Shop',  ['Strawberry', 'Milk'],         False),
    ('Farmers Market', ['Wheat', 'Carrots', 'Tomatoes', 'Strawberry'], False),
]

shop_df = pd.DataFrame(shops, columns=['Shop', 'Demands', 'Is2x'])
shop_df['DailyDrain'] = shop_df.apply(
    lambda r: len(r.Demands) * (2 if r.Is2x else 1) * (24/4),  # 24 turns/day, 1 per 4 turns, 2x if single-product
    axis=1
)
shop_df['PerProductDrain'] = shop_df.apply(
    lambda r: (2 if r.Is2x else 1) * (24/4),
    axis=1
)

# Town center always-on drain
print("=== Town Center (always active) ===")
print(f"  Day 1-9:  1 unit of every product / 12 turns = 2 units/day per product")
print(f"  Day 10-19: 2 units = 4 units/day per product")
print(f"  Day 20-30: 4 units = 8 units/day per product")
print()
print("=== Shop Unlock Schedule (every 3 days, 10 shops max) ===")
print(shop_df[['Shop', 'Demands', 'Is2x', 'PerProductDrain']].to_string(index=False))

# Aggregate demand by product over a 30-day season
demand_by_product = {p: 0 for p in ['Wheat','Carrots','Tomatoes','Strawberry','Eggs','Milk','Wool']}
# Town center
for day in range(30):
    rate = 1 if day < 10 else (2 if day < 20 else 4)
    for p in demand_by_product:
        if p != 'Fertilizer':
            demand_by_product[p] += rate * 2  # 24 turns/12 = 2 per day
# Shops (assume all 10 unlock over 30 days, 3-day interval)
for shop, demands, is2x in shops:
    rate = 2 if is2x else 1
    for p in demands:
        demand_by_product[p] += rate * 6 * 10  # 6/day × ~10 days active on average

print("\n=== Total Town Demand per Product (30-day season, all shops) ===")
demand_df = pd.DataFrame(list(demand_by_product.items()), columns=['Product','TownDrain_Units'])
demand_df = demand_df.sort_values('TownDrain_Units', ascending=False)
print(demand_df.to_string(index=False))

def wheat_loop_agent(obs):
    """
    Baseline Kaggriculture agent.
    Strategy: Plant wheat in NW quadrant, water daily, harvest at maturity, sell.
    """
    player = obs['player']
    me = obs['farms'][player]
    private = obs['private']
    fx, fy = me['farmer']
    tile = me['tiles'][fy][fx]
    day = obs['day']
    money = me['money']
    
    # === Market orders ===
    market = []
    
    # Buy wheat seed if we have none and can afford it
    wheat_seeds = private['seeds'].get('WHEAT', 0)
    if wheat_seeds == 0 and money >= 10:
        market.append(['BUY_SEED', 'WHEAT', 5])  # Buy 5 seeds at a time
    
    # Sell any wheat in shed
    wheat_in_shed = private['shed'].get('WHEAT', 0)
    if wheat_in_shed > 0:
        # Sell in batches of 10 to avoid flooding
        sell_qty = min(wheat_in_shed, 10)
        market.append(['SELL', 'WHEAT', sell_qty])
    
    # === Farmer action ===
    # If standing on empty unlocked tile and have seeds → plant
    if tile is None and wheat_seeds > 0:
        return {'farmer': ['PLANT', 'WHEAT'], 'hands': [], 'market': market}
    
    # If standing on a plant
    if isinstance(tile, dict) and tile.get('kind') == 'PLANT':
        crop = tile.get('crop')
        if crop == 'WHEAT':
            crop_age = day - tile['planted_day']
            # Wheat: first_yield_day = 2, max_yield_day = 4
            if crop_age >= 4:
                # Max yield — harvest now
                return {'farmer': ['HARVEST'], 'hands': [], 'market': market}
            elif crop_age >= 2 and tile.get('yield_units', 0) > 0:
                # Has some yield — harvest
                return {'farmer': ['HARVEST'], 'hands': [], 'market': market}
            elif not tile.get('watered_today'):
                # Water during the bonus window (days 2-4)
                if crop_age >= 1:
                    return {'farmer': ['WATER'], 'hands': [], 'market': market}
    
    # If standing on a weed, dig it
    if isinstance(tile, dict) and tile.get('kind') == 'WEED':
        return {'farmer': ['DIG'], 'hands': [], 'market': market}
    
    # Move toward nearest empty tile (simple North-South sweep)
    # Find empty tile
    for y in range(len(me['tiles'])):
        for x in range(len(me['tiles'][y])):
            t = me['tiles'][y][x]
            if t is None and (x, y) != (fx, fy):
                # Move toward it
                if x < fx: return {'farmer': ['WEST'], 'hands': [], 'market': market}
                if x > fx: return {'farmer': ['EAST'], 'hands': [], 'market': market}
                if y < fy: return {'farmer': ['NORTH'], 'hands': [], 'market': market}
                if y > fy: return {'farmer': ['SOUTH'], 'hands': [], 'market': market}
    
    # Default: pass
    return {'farmer': ['PASS'], 'hands': [], 'market': market}


# === Test it locally ===
# To run a quick sanity check, uncomment the following:
# from kaggle_environments import make
# env = make('kaggriculture', configuration={'episodeSteps': 100})
# env.run([wheat_loop_agent, 'random'])
# env.render(mode='ipython', width=800, height=800)

print("✓ Wheat Loop agent defined")
print("Strategy summary:")
print("  - Buy 5 wheat seeds when out of stock")
print("  - Plant on any empty tile")
print("  - Water during days 1-4 (bonus window)")
print("  - Harvest at day 2+ if yield available, or day 4 (max yield)")
print("  - Sell wheat in batches of 10")
print("  - Dig weeds when encountered")
print("  - Move toward nearest empty tile")
print()
print("Expected performance:")
print("  - Plants ~5-10 wheat tiles per cycle")
print("  - Harvests every 4 days, ~6 yield per tile = ~30-60 wheat per cycle")
print("  - Sells at ~$22-25/unit (gentle glut from log curve)")
print("  - Revenue: ~$660-1500 per 4-day cycle = ~$5,000-11,000 per season")