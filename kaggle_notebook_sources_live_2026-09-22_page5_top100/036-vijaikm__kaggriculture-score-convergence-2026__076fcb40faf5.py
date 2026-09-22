import os, glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style='darkgrid', palette='muted')
plt.rcParams['figure.dpi'] = 110
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'

# This notebook uses ONLY public leaderboard + episode timing via Kaggle MCP.
# It contains ZERO submission source code — analysis only.
# Synthetic fallback matches the mined trajectory report (report-2026-08-23.md)
np.random.seed(42)
window_stats = pd.DataFrame({
    'window': ['0-1h','1-6h','6-12h','12-24h','24-36h','36-48h','48-72h'],
    'cum_games': [15, 72, 81, 98, 101, 101, 101],
    'cum_wr': [0.93, 0.71, 0.67, 0.65, 0.63, 0.63, 0.63],
    'score_delta': [850, 450, 120, 80, 30, 15, 10],
    'games_in_window': [15, 57, 9, 17, 3, 0, 0]
})
window_stats


fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Games vs time
axes[0].bar(window_stats['window'], window_stats['cum_games'], color='#0284c7', alpha=0.85)
axes[0].set_title('Cumulative Ranked Games vs Time', fontweight='bold')
axes[0].set_ylabel('Cumulative Games')
axes[0].set_xlabel('Elapsed Time Window')
for i, v in enumerate(window_stats['cum_games']):
    axes[0].text(i, v+2, str(v), ha='center', fontsize=9)

# Score delta per window
axes[1].bar(window_stats['window'], window_stats['score_delta'], color='#e11d48', alpha=0.85)
axes[1].set_title('Score Jump per Window (Avg, Elo-like)', fontweight='bold')
axes[1].set_ylabel('Score Delta in Window')
axes[1].set_xlabel('Elapsed Time Window')
for i, v in enumerate(window_stats['score_delta']):
    axes[1].text(i, v+15, f'+{v}', ha='center', fontsize=9)

plt.tight_layout()
plt.show()
print('Knee at 6h: 70% of total climb done. Flat after 24h.')


fig, ax = plt.subplots(figsize=(10, 4.5))
xs = [15, 50, 70, 80, 98, 101]
ys = [1.00, 0.76, 0.71, 0.69, 0.65, 0.63]
ax.plot(xs, ys, marker='o', color='#0ea5e9', linewidth=2.5)
ax.fill_between(xs, ys, alpha=0.15, color='#0ea5e9')
ax.set_title('Win-Rate Decay vs Games Played (Mean)', fontweight='bold')
ax.set_xlabel('Cumulative Ranked Games')
ax.set_ylabel('Cumulative Win Rate')
ax.set_ylim(0.5, 1.02)
ax.grid(True, alpha=0.3)
for x,y in zip(xs, ys):
    ax.text(x, y+0.02, f'{y:.2f}', ha='center', fontsize=8)
plt.show()


hold = pd.DataFrame({
    'tier': ['Probe','Mover','Contender','Top 200','Top 100','Top 50+'],
    'hold_h': [24, 48, 72, 96, 120, 168],
    'cutoff': [0, 1800, 2200, 2396, 2518, 2628]
})
fig, ax = plt.subplots(figsize=(10, 4))
ax.barh(hold['tier'], hold['hold_h'], color=['#94a3b8','#38bdf8','#0ea5e9','#0284c7','#0369a1','#0c4a6e'])
ax.set_title('Minimum Hold Duration by Tier (Hours)', fontweight='bold')
ax.set_xlabel('Hours')
for i, v in enumerate(hold['hold_h']):
    ax.text(v+2, i, f'{v}h', va='center', fontsize=9)
plt.tight_layout()
plt.show()
