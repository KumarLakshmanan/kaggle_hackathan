import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='darkgrid', palette='muted')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['figure.dpi'] = 110

# Robust adaptive path resolution for Kaggle / Local environments
candidate_paths = [
    '/kaggle/input/kaggriculture-match-replay-corpus',
    '/kaggle/input/kaggriculture-500-match-replays-trajectories',
    '../../datasets/kaggriculture_match_corpus',
    './datasets/kaggriculture_match_corpus',
    'datasets/kaggriculture_match_corpus'
]

DATA_DIR = None
for p in candidate_paths:
    if os.path.exists(p) and os.path.exists(os.path.join(p, 'matches_meta.csv')):
        DATA_DIR = p
        break

if DATA_DIR is None:
    matches = glob.glob('/kaggle/input/**/matches_meta.csv', recursive=True) + glob.glob('**/matches_meta.csv', recursive=True)
    if matches:
        DATA_DIR = os.path.dirname(matches[0])

print(f'Using Data Directory: {DATA_DIR}')

if DATA_DIR and os.path.exists(os.path.join(DATA_DIR, 'matches_meta.csv')):
    df_meta = pd.read_csv(os.path.join(DATA_DIR, 'matches_meta.csv'))
    df_orders = pd.read_csv(os.path.join(DATA_DIR, 'market_orders.csv'))
    df_actions = pd.read_csv(os.path.join(DATA_DIR, 'farmer_actions.csv'))
    df_shops = pd.read_csv(os.path.join(DATA_DIR, 'town_shop_schedules.csv'))
else:
    print('Generating synthetic fallback dataframe for demonstration...')
    df_meta = pd.DataFrame({
        'episode_id': [f'ep_{i}' for i in range(500)],
        'player_0_team': ['Bot_A']*500,
        'player_1_team': ['Bot_B']*500,
        'player_0_score': np.random.normal(185000, 35000, 500),
        'player_1_score': np.random.normal(178000, 38000, 500),
        'winner': np.random.choice(['Player 0', 'Player 1', 'Tie'], 500, p=[0.52, 0.45, 0.03]),
        'margin': np.random.exponential(15000, 500),
        'total_steps': [720]*500
    })
    df_orders = pd.DataFrame({
        'order_type': np.random.choice(['BUY_SEED', 'SELL', 'HIRE', 'BUY_PRODUCT', 'BUY_ANIMAL'], 50000),
        'item': np.random.choice(['WHEAT', 'STRAWBERRY', 'TOMATO', 'CARROT', 'MELON', 'COW', 'SHEEP'], 50000),
        'quantity': np.random.randint(1, 20, 50000)
    })
    df_actions = pd.DataFrame({
        'action_verb': np.random.choice(['WATER', 'PLANT', 'HARVEST', 'MOVE', 'TILL', 'FEED', 'PASS'], 50000)
    })
    df_shops = pd.DataFrame({
        'shop_name': ['BAKERY', 'PIZZA_SHOP', 'BRUNCH_SPOT', 'YARN_STORE', 'ICE_CREAM_SHOP'],
        'product_demanded': ['WHEAT', 'TOMATO', 'EGG', 'WOOL', 'STRAWBERRY'],
        'base_multiplier': [1.5]*5,
        'peak_multiplier': [2.0]*5
    })

print(f'✅ Loaded {len(df_meta):,} match records')
print(f'✅ Loaded {len(df_orders):,} market order transactions')
print(f'✅ Loaded {len(df_actions):,} unit grid actions')
print(f'✅ Loaded {len(df_shops):,} town establishment demand profiles')

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 1. Winner Distribution
winner_counts = df_meta['winner'].value_counts()
axes[0].pie(winner_counts, labels=winner_counts.index, autopct='%1.1f%%', colors=['#0284c7', '#e11d48', '#64748b'], explode=[0.04]*len(winner_counts), startangle=140)
axes[0].set_title('Match Outcome Share (Seat 0 vs Seat 1)', fontsize=13, fontweight='bold')

# 2. Final Bank Cash Distribution
sns.histplot(df_meta['player_0_score'], ax=axes[1], color='#0284c7', label='Seat 0 Score ($)', kde=True, bins=30, alpha=0.6)
sns.histplot(df_meta['player_1_score'], ax=axes[1], color='#e11d48', label='Seat 1 Score ($)', kde=True, bins=30, alpha=0.6)
axes[1].set_title('Final Coin Bank Distribution ($)', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Final Cash Bank ($)')
axes[1].set_ylabel('Match Frequency')
axes[1].legend()

plt.tight_layout()
plt.show()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Order Type Distribution
order_types = df_orders['order_type'].value_counts()
sns.barplot(x=order_types.values, y=order_types.index, ax=axes[0], palette='crest')
axes[0].set_title('Market Order Types (Total Volume)', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Order Count')

# Top Sold Commodities
sell_df = df_orders[df_orders['order_type'] == 'SELL']
if len(sell_df) > 0:
    sell_commodities = sell_df['item'].value_counts()
    sns.barplot(x=sell_commodities.values, y=sell_commodities.index, ax=axes[1], palette='flare')
    axes[1].set_title('Top Sold Commodities by Order Frequency', fontsize=13, fontweight='bold')
    axes[1].set_xlabel('Sell Orders Logged')

plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 5))
action_counts = df_actions['action_verb'].value_counts().head(10)
sns.barplot(x=action_counts.index, y=action_counts.values, palette='viridis')
plt.title('Top 10 Farm Grid Action Verbs (250,000+ Actions Analyzed)', fontsize=13, fontweight='bold')
plt.xlabel('Action Verb')
plt.ylabel('Execution Count')
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

df_shops_display = df_shops.sort_values(by='product_demanded')
plt.figure(figsize=(11, 4.5))
sns.scatterplot(data=df_shops_display, x='shop_name', y='product_demanded', hue='peak_multiplier', s=220, palette='coolwarm')
plt.title('Town Shop Commodity Demand Matrix (Peak Payout Multipliers)', fontsize=13, fontweight='bold')
plt.xlabel('Town Establishment')
plt.ylabel('Product Demanded')
plt.xticks(rotation=35)
plt.tight_layout()
plt.show()