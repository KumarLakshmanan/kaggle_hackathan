import math
import sys
from collections import Counter, defaultdict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import kaggle_environments
from kaggle_environments import make

# Reproducibility seed
SEED = 42
np.random.seed(SEED)

# Styling configuration for publication-ready visual charts
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    'axes.labelsize': 11,
    'figure.titlesize': 14,
    'figure.titleweight': 'bold',
    'figure.dpi': 120,
    'axes.edgecolor': '#94a3b8',
    'grid.color': '#e2e8f0',
    'grid.linestyle': '--',
    'grid.alpha': 0.7,
})

print(f'✅ Simulation Engine: kaggle-environments v{kaggle_environments.__version__}')
print(f'✅ Python Version: {sys.version.split()[0]} | Seed: {SEED}')

# Market parameters: (BasePrice, Equilibrium_I0, Scale_T, Shape_Below, Beta_Below, Shape_Above, Beta_Above)
MARKET_PARAMS = {
    'WHEAT': (25, 10000, 400, 'sqrt', 0.8, 'log', 0.2),
    'CARROT': (35, 10000, 450, 'log', 0.2, 'sqrt', 0.7),
    'TOMATO': (60, 10000, 200, 'linear', 0.4, 'sqrt', 0.6),
    'STRAWBERRY': (120, 10000, 100, 'sqrt', 0.7, 'linear', 1.6),
    'MELON': (250, 10000, 300, 'log', 0.2, 'sq', 3.6),
    'EGG': (50, 10000, 332, 'linear', 0.4, 'log', 0.2),
    'MILK': (160, 10000, 122, 'sqrt', 0.6, 'linear', 1.6),
    'WOOL': (200, 10000, 105, 'log', 0.2, 'sq', 3.2),
    'FERTILIZER': (100, 10000, 200, 'linear', 0.4, 'linear', 0.4),
}

def shape_func(name: str, value: float) -> float:
    v = max(0.0, float(value))
    if name == 'sqrt':
        return math.sqrt(v)
    if name == 'log':
        return math.log1p(v)
    if name == 'linear':
        return v
    if name == 'sq':
        return (v * v) / 100.0
    raise ValueError(f'Unknown shape function: {name}')

def compute_market_price(item: str, inventory: int) -> float:
    base, eq, scale, bf, bt, af, at = MARKET_PARAMS[item]
    if inventory < eq:
        amp = bt * base / shape_func(bf, scale)
        return max(1.0, base + amp * shape_func(bf, eq - inventory))
    amp = at * base / shape_func(af, scale)
    return max(1.0, base - amp * shape_func(af, inventory - eq))

# Generate price elasticity comparison dataframe
elasticity_data = []
for item, (base, eq, scale, *_) in MARKET_PARAMS.items():
    p_eq = compute_market_price(item, 10000)
    p_oversupply_1t = compute_market_price(item, 10000 + scale)
    p_oversupply_2t = compute_market_price(item, 10000 + 2 * scale)
    pct_drop_2t = 100.0 * (p_eq - p_oversupply_2t) / p_eq
    elasticity_data.append({
        'Commodity': item,
        'Base Price ($)': base,
        'Scale (T)': scale,
        'Price @ I0': round(p_eq, 1),
        'Price @ I0+T': round(p_oversupply_1t, 1),
        'Price @ I0+2T': round(p_oversupply_2t, 1),
        'Max Price Drop (%)': f'{pct_drop_2t:.1f}%',
        'Elasticity Archetype': 'Glut-Absorber' if pct_drop_2t < 35 else ('Moderate' if pct_drop_2t < 75 else 'Crash-Vulnerable')
    })

df_elasticity = pd.DataFrame(elasticity_data)
display(df_elasticity)

fig, axes = plt.subplots(3, 3, figsize=(16, 12))
inv_range = np.linspace(8000, 13000, 200)
palette = sns.color_palette('tab10', len(MARKET_PARAMS))

for idx, (item, params) in enumerate(MARKET_PARAMS.items()):
    ax = axes[idx // 3, idx % 3]
    prices = [compute_market_price(item, int(i)) for i in inv_range]
    
    ax.plot(inv_range, prices, color=palette[idx], linewidth=2.2, label=f'{item} P(I)')
    ax.axvline(10000, color='#64748b', linestyle='--', alpha=0.8, label='Equilibrium (I0=10k)')
    ax.axhline(1.0, color='#ef4444', linestyle=':', alpha=0.7, label='Price Floor ($1)')
    
    ax.set_title(f'{item} (Base: ${params[0]}, T={params[2]})')
    ax.set_xlabel('Market Inventory Index (I)')
    ax.set_ylabel('Unit Price ($)')
    ax.set_xlim(8000, 13000)
    ax.grid(True, alpha=0.4)
    if idx == 0:
        ax.legend(loc='upper right', fontsize=8)

fig.suptitle('Market Price Decay Curves: Commodity Sensitivity to Inventory Gluts', fontsize=15, y=0.99)
plt.tight_layout()
plt.show()

print('📊 Analytical Insight: Wheat and Carrot serve as reliable volume backbones due to logarithmic/sqrt decay,')
print('   whereas Melon, Strawberry, Milk, and Wool require carefully timed liquidation to avoid the $1 price floor.')

CROPS_SPEC = {
    'CARROT': {'seed_cost': 20, 'grow_days': 3, 'yield_units': 3, 'ongoing': False, 'max_yields': 1},
    'WHEAT': {'seed_cost': 10, 'grow_days': 4, 'yield_units': 4, 'ongoing': False, 'max_yields': 1},
    'STRAWBERRY': {'seed_cost': 100, 'grow_days': 10, 'yield_units': 4, 'ongoing': True, 'max_yields': 4},
    'TOMATO': {'seed_cost': 50, 'grow_days': 8, 'yield_units': 4, 'ongoing': True, 'max_yields': 4},
    'MELON': {'seed_cost': 80, 'grow_days': 10, 'yield_units': 6, 'ongoing': False, 'max_yields': 1},
}

crop_rows = []
for crop, spec in CROPS_SPEC.items():
    base_p = MARKET_PARAMS[crop][0]
    total_units = spec['yield_units'] * spec['max_yields']
    total_gross = total_units * base_p
    total_net = total_gross - spec['seed_cost']
    cycle_days = spec['grow_days'] + (spec['max_yields'] - 1) * 2 if spec['ongoing'] else spec['grow_days']
    daily_roi = total_net / cycle_days
    
    crop_rows.append({
        'Crop': crop,
        'Seed Cost ($)': spec['seed_cost'],
        'Growth (Days)': spec['grow_days'],
        'Yield / Harvest': spec['yield_units'],
        'Max Harvests': spec['max_yields'],
        'Base Price ($)': base_p,
        'Total Gross ($)': total_gross,
        'Total Net ($)': total_net,
        'Daily ROI ($/Day)': round(daily_roi, 2),
        'Margin (%)': f'{(total_net / total_gross) * 100:.1f}%'
    })

df_crops = pd.DataFrame(crop_rows).sort_values('Daily ROI ($/Day)', ascending=False)
display(df_crops)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Daily ROI per Crop
sns.barplot(data=df_crops, x='Crop', y='Daily ROI ($/Day)', ax=axes[0], palette='crest')
axes[0].set_title('Theoretical Daily Net ROI ($ / Tile-Day at Equilibrium)')
axes[0].set_ylabel('Net Profit ($/day)')
for p in axes[0].patches:
    axes[0].annotate(f'${p.get_height():.1f}', (p.get_x() + p.get_width() / 2., p.get_height() + 1),
                     ha='center', va='bottom', fontsize=9, weight='bold')

# Plot 2: Growth Duration vs Total Net Return
sns.scatterplot(data=df_crops, x='Growth (Days)', y='Total Net ($)', hue='Crop', s=250, ax=axes[1], palette='tab10')
axes[1].set_title('Growth Duration vs Total Net Return per Seed')
axes[1].set_xlabel('Initial Growth Days')
axes[1].set_ylabel('Total Net Return ($)')
for idx, row in df_crops.iterrows():
    axes[1].annotate(f"{row['Crop']} (${row['Total Net ($)']})", 
                     (row['Growth (Days)'] + 0.2, row['Total Net ($)'] - 5), fontsize=9)

plt.tight_layout()
plt.show()

print('📊 Conclusion: While Melon offers high gross return ($1,420 net), its 10-day lockup makes cash flow illiquid.')
print('   Carrot and Wheat provide essential early-game working capital velocity to fund land and worker expansion.')

ANIMALS_SPEC = {
    'GOOSE': {'purchase_cost': 300, 'product': 'EGG', 'product_base': 50, 'prod_interval_days': 1},
    'COW': {'purchase_cost': 400, 'product': 'MILK', 'product_base': 160, 'prod_interval_days': 2},
    'SHEEP': {'purchase_cost': 500, 'product': 'WOOL', 'product_base': 200, 'prod_interval_days': 3},
}

# Simulate cumulative profit over 30 days assuming wheat cost = $25/unit
days = np.arange(1, 31)
wheat_feed_cost = 25

plt.figure(figsize=(10, 5))
for animal, spec in ANIMALS_SPEC.items():
    cum_cash = []
    balance = -spec['purchase_cost']
    for d in days:
        # Daily feed cost
        balance -= wheat_feed_cost
        # Product payout
        if d % spec['prod_interval_days'] == 0:
            balance += spec['product_base']
        cum_cash.append(balance)
    
    plt.plot(days, cum_cash, label=f"{animal} (Cost: ${spec['purchase_cost']}, Payback: Day {next((i for i, v in enumerate(cum_cash) if v >= 0), None) + 1 if any(v >= 0 for v in cum_cash) else 'N/A'})")

plt.axhline(0, color='gray', linestyle='--', alpha=0.6)
plt.title('Cumulative Net Cash Flow per Livestock Unit (30-Day Season)')
plt.xlabel('Day of Season')
plt.ylabel('Cumulative Profit / Loss ($)')
plt.legend()
plt.grid(True, alpha=0.4)
plt.show()

print('📊 Conclusion: Cow achieves the fastest payback period (~Day 8-10) and highest compounding daily return.')

fib_costs = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
hands = list(range(1, len(fib_costs) + 1))
cum_costs = np.cumsum(fib_costs)

df_labor = pd.DataFrame({
    'Hands Hired': hands,
    'Marginal Cost ($)': fib_costs,
    'Total Daily Cost ($)': cum_costs,
    'Extra Actions / Day': [h * 24 for h in hands],
    'Cost per Action ($)': [cum_costs[i] / ((i + 1) * 24) for i in range(len(hands))]
})

fig, ax1 = plt.subplots(figsize=(10, 5))
ax1.bar(df_labor['Hands Hired'] - 0.2, df_labor['Marginal Cost ($)'], width=0.4, label='Marginal Hand Cost ($)', color='#3b82f6')
ax1.bar(df_labor['Hands Hired'] + 0.2, df_labor['Total Daily Cost ($)'], width=0.4, label='Cumulative Daily Cost ($)', color='#10b981')
ax1.set_xlabel('Number of Hired Hands')
ax1.set_ylabel('Cost in Dollars ($)')
ax1.set_title('Labor Hiring Cost Scaling (Fibonacci Growth)')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)
plt.show()

print('📊 Conclusion: Hiring 1-5 hands is exceptionally cost-effective (total daily cost <= $12 for 120 actions).')
print('   Hiring beyond 8 hands incurs exponential cost ($143+ daily) and is only viable with multi-quadrant mature farms.')

grid = np.zeros((10, 10))
# Quadrant costs
grid[0:5, 0:5] = 0       # NW: Free
grid[0:5, 5:10] = 1000   # NE: $1,000
grid[5:10, 0:5] = 2000   # SW: $2,000
grid[5:10, 5:10] = 4000  # SE: $4,000

plt.figure(figsize=(7, 6))
sns.heatmap(grid, annot=True, fmt='.0f', cmap='YlGnBu', cbar_kws={'label': 'Unlock Cost ($)'})
plt.title('10x10 Farm Topography & Quadrant Unlock Costs')
plt.xlabel('Grid X Coordinate')
plt.ylabel('Grid Y Coordinate')
plt.text(2.5, 2.5, 'NW Quadrant\n(FREE / Active)', color='white', ha='center', va='center', weight='bold')
plt.text(7.5, 2.5, 'NE Quadrant\n($1,000)', color='black', ha='center', va='center', weight='bold')
plt.text(2.5, 7.5, 'SW Quadrant\n($2,000)', color='black', ha='center', va='center', weight='bold')
plt.text(7.5, 7.5, 'SE Quadrant\n($4,000)', color='black', ha='center', va='center', weight='bold')
plt.show()

class SimulationReplayAnalyzer:
    """Parses and analyzes full 720-step Kaggriculture match trajectories."""
    def __init__(self, steps):
        self.steps = steps
        
    def extract_metrics(self):
        p0_bank = [s[0].observation['farms'][0]['money'] for s in self.steps]
        p1_bank = [s[0].observation['farms'][1]['money'] for s in self.steps]
        days = [int(s[0].observation.get('day', 0)) for s in self.steps]
        
        p0_sales = defaultdict(int)
        p0_actions = Counter()
        
        for s in self.steps:
            act = s[0].action or {}
            for m in act.get('market', []):
                if m and m[0] == 'SELL':
                    p0_sales[str(m[1])] += int(m[2])
            farmer_act = (act.get('farmer') or ['PASS'])[0]
            p0_actions[farmer_act] += 1
            
        return {
            'days': days,
            'p0_bank': p0_bank,
            'p1_bank': p1_bank,
            'p0_sales': dict(p0_sales),
            'p0_actions': p0_actions,
            'final_p0': p0_bank[-1],
            'final_p1': p1_bank[-1]
        }

# Run a live match between the official Starter Bot and Random Bot
env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': SEED})
env.run(['starter', 'random'])

analyzer = SimulationReplayAnalyzer(env.steps)
metrics = analyzer.extract_metrics()

fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

# 1. Bank Trajectory
axes[0].plot(metrics['days'], metrics['p0_bank'], label='Starter Bot', color='#2563eb', linewidth=2)
axes[0].plot(metrics['days'], metrics['p1_bank'], label='Random Bot', color='#dc2626', linewidth=1.5, linestyle='--')
axes[0].set_title('Bank Growth Over 30-Day Season')
axes[0].set_xlabel('Day')
axes[0].set_ylabel('Bank Balance ($)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# 2. Starter Bot Sales Distribution
if metrics['p0_sales']:
    items = list(metrics['p0_sales'].keys())
    vols = list(metrics['p0_sales'].values())
    axes[1].bar(items, vols, color='#059669')
    axes[1].set_title('Total Units Sold by Item')
    axes[1].set_ylabel('Units Sold')
    axes[1].tick_params(axis='x', rotation=30)
else:
    axes[1].text(0.5, 0.5, 'No Sales Recorded', ha='center')

# 3. Farmer Action Breakdown
top_acts = metrics['p0_actions'].most_common(7)
act_names = [a[0] for a in top_acts]
act_counts = [a[1] for a in top_acts]
axes[2].bar(act_names, act_counts, color='#7c3aed')
axes[2].set_title('Farmer Action Frequencies')
axes[2].set_ylabel('Turn Count')
axes[2].tick_params(axis='x', rotation=30)

plt.tight_layout()
plt.show()

print(f"🎯 Match Result: Starter Bot (${metrics['final_p0']:.0f}) vs Random Bot (${metrics['final_p1']:.0f})")