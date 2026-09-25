from IPython.display import Image, display
display(Image(url="https://api.memegen.link/images/fine/100~p_local_win_rate/LB_score:_876.jpg", width=500))

display(Image(url="https://api.memegen.link/images/astronaut/Wait,_my_agent_was_broken~q/Always_has_been.jpg", width=500))

display(Image(url="https://api.memegen.link/images/gru/Build_agent/Test_locally:_100~p_WR/Submit_to_Kaggle/Score_876.jpg", width=500))

import math
import itertools
from collections import defaultdict
from kaggle_environments import make


def wilson_ci(wins, total, z=1.96):
    """Wilson score 95% confidence interval for win rate."""
    if total == 0:
        return (0.0, 0.0)
    p = wins / total
    denom = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denom
    return (max(0, center - margin), min(1, center + margin))


def run_matchup(agent_a_path, agent_b_path, games_per_seat=25):
    """Run agent A vs B with seat alternation. Returns stats dict.
    Total games = games_per_seat * 2 (half as P0, half as P1)."""
    wins_a, wins_b, ties = 0, 0, 0
    scores_a, scores_b = [], []

    for i in range(games_per_seat * 2):
        if i < games_per_seat:
            p0, p1, a_seat = agent_a_path, agent_b_path, 0
        else:
            p0, p1, a_seat = agent_b_path, agent_a_path, 1
        try:
            env = make("kaggriculture", debug=True)
            result = env.run([p0, p1])
            final = result[-1]
            if final[0]["status"] != "DONE" or final[1]["status"] != "DONE":
                continue
            ra = final[0]["reward"] if a_seat == 0 else final[1]["reward"]
            rb = final[1]["reward"] if a_seat == 0 else final[0]["reward"]
            scores_a.append(ra)
            scores_b.append(rb)
            if ra > rb: wins_a += 1
            elif rb > ra: wins_b += 1
            else: ties += 1
        except Exception:
            continue

    total = wins_a + wins_b + ties
    return {
        "wins_a": wins_a, "wins_b": wins_b, "ties": ties, "total": total,
        "win_rate_a": wins_a / total if total else 0,
        "ci_95": wilson_ci(wins_a, total),
        "margin": (sum(scores_a) - sum(scores_b)) / len(scores_a) if scores_a else 0,
    }


def run_tournament(agents, games_per_seat=25, verbose=True):
    """Full round-robin. agents = {name: path_to_main_py}"""
    names = list(agents.keys())
    pairs = list(itertools.combinations(names, 2))
    results = {}

    for idx, (a, b) in enumerate(pairs, 1):
        if verbose:
            print(f"[{idx}/{len(pairs)}] {a} vs {b}...", end="", flush=True)
        stats = run_matchup(agents[a], agents[b], games_per_seat)
        results[(a, b)] = stats
        if verbose:
            print(f" {stats['wins_a']}W-{stats['wins_b']}L ({stats['win_rate_a']*100:.0f}%)")

    agg = {}
    for name in names:
        w, l, t, g = 0, 0, 0, 0
        for (a, b), s in results.items():
            if a == name:
                w += s["wins_a"]; l += s["wins_b"]; t += s["ties"]; g += s["total"]
            elif b == name:
                w += s["wins_b"]; l += s["wins_a"]; t += s["ties"]; g += s["total"]
        agg[name] = {"wins": w, "losses": l, "ties": t, "games": g,
                     "win_rate": w / g if g else 0}
    return results, agg

print("Framework loaded! Use run_tournament(agents) to start.")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

agents_ranked = [
    ("Agent A", 267, 33, 0, 89.0),
    ("Agent B", 229, 71, 0, 76.3),
    ("Agent C", 223, 77, 0, 74.3),
    ("Agent D", 168, 132, 0, 56.0),
    ("Agent E", 85, 200, 15, 28.3),
    ("Agent F", 60, 225, 15, 20.0),
    ("Agent G", 3, 297, 0, 1.0),
]

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('#0f0f23')
ax.set_facecolor('#0f0f23')

names = [a[0] for a in agents_ranked]
win_rates = [a[4] for a in agents_ranked]
colors = ['#00ff88', '#00cc66', '#00aa55', '#ffd700', '#ff6b6b', '#ff4444', '#cc0000']

bars = ax.barh(range(len(names)), win_rates, color=colors, height=0.6,
               edgecolor='white', linewidth=0.5)

for i, (name, w, l, t, wr) in enumerate(agents_ranked):
    record = f"{w}W-{l}L" + (f"-{t}D" if t > 0 else "")
    ax.text(wr + 1.5, i, f"{wr:.0f}%  ({record})", va='center', fontsize=11,
            color='white', fontweight='bold', fontfamily='monospace')

ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=13, color='white', fontweight='bold', fontfamily='monospace')
ax.set_xlabel('Win Rate (%)', fontsize=13, color='white', fontfamily='monospace')
ax.set_title('Power Rankings — 1,050 Game Local League', fontsize=16,
             color='white', fontweight='bold', fontfamily='monospace', pad=15)
ax.set_xlim(0, 115)
ax.tick_params(colors='white')
for s in ['top', 'right']: ax.spines[s].set_visible(False)
for s in ['bottom', 'left']: ax.spines[s].set_color('white')
ax.invert_yaxis()
plt.tight_layout()
plt.show()

h2h = np.array([
    [50, 94, 74, 76, 96, 96, 98],
    [6,  50, 72, 86, 100, 94, 100],
    [26, 28, 50, 100, 98, 96, 98],
    [24, 14, 0,  50, 100, 100, 98],
    [4,  0,  2,  0,  50,  94, 100],
    [4,  6,  4,  0,  6,   50, 100],
    [2,  0,  2,  2,  0,   0,  50],
])

labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
fig, ax = plt.subplots(figsize=(9, 8))
fig.patch.set_facecolor('#0f0f23')
ax.set_facecolor('#0f0f23')

cmap = LinearSegmentedColormap.from_list('wr',
    ['#cc0000', '#ff4444', '#ff6b6b', '#ffd700', '#88cc44', '#00cc66', '#00ff88'])
im = ax.imshow(h2h, cmap=cmap, vmin=0, vmax=100)

for i in range(7):
    for j in range(7):
        color = 'black' if 30 < h2h[i][j] < 80 else 'white'
        text = f'{h2h[i][j]:.0f}%' if i != j else '—'
        ax.text(j, i, text, ha='center', va='center', fontsize=12,
                color=color, fontweight='bold', fontfamily='monospace')

ax.set_xticks(range(7)); ax.set_yticks(range(7))
ax.set_xticklabels(labels, fontsize=14, color='white', fontfamily='monospace')
ax.set_yticklabels(labels, fontsize=14, color='white', fontfamily='monospace')
ax.set_xlabel('Opponent →', fontsize=13, color='white', fontfamily='monospace')
ax.set_ylabel('← Agent', fontsize=13, color='white', fontfamily='monospace')
ax.set_title('Head-to-Head Win Rates (Row vs Column)', fontsize=14,
             color='white', fontweight='bold', fontfamily='monospace', pad=15)
ax.tick_params(colors='white')
cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label('Win Rate %', fontsize=11, color='white', fontfamily='monospace')
cbar.ax.tick_params(colors='white')
plt.tight_layout()
plt.show()

submissions = [
    ("Broken submit", 876, '#cc0000'),
    ("Bad V1", 1181, '#ff4444'),
    ("Public reactive", 1822, '#ffa500'),
    ("Public base", 1891, '#ffd700'),
    ("Tournament tested", 2560, '#00ff88'),
]

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('#0f0f23')
ax.set_facecolor('#0f0f23')

x = range(len(submissions))
scores = [s[1] for s in submissions]
colors = [s[2] for s in submissions]
bars = ax.bar(x, scores, color=colors, width=0.6, edgecolor='white', linewidth=0.5)

for i, (_, score, _) in enumerate(submissions):
    ax.text(i, score + 60, str(score), ha='center', va='bottom', fontsize=18,
            color='white', fontweight='bold', fontfamily='monospace')

ax.annotate('', xy=(4, 2480), xytext=(0, 960),
            arrowprops=dict(arrowstyle='->', color='#00ff88', lw=3,
                          connectionstyle='arc3,rad=0.3'))
ax.text(2, 1750, '+1684 Elo', ha='center', fontsize=18, color='#00ff88',
        fontweight='bold', fontfamily='monospace')

ax.set_xticks(x)
ax.set_xticklabels([s[0] for s in submissions], fontsize=10, color='white',
                    fontfamily='monospace', ha='center')
ax.set_ylabel('LB Score (Elo)', fontsize=13, color='white', fontfamily='monospace')
ax.set_title('876 → 2600+', fontsize=20,
             color='white', fontweight='bold', fontfamily='monospace', pad=15)
ax.set_ylim(0, 3100)
ax.tick_params(colors='white')
for s in ['top', 'right']: ax.spines[s].set_visible(False)
for s in ['bottom', 'left']: ax.spines[s].set_color('white')

ax.axhline(y=2400, color='#cd7f32', linestyle='--', linewidth=2, alpha=0.8)
ax.text(4.55, 2430, '← Bronze', fontsize=12, color='#cd7f32',
        fontfamily='monospace', fontweight='bold')
plt.tight_layout()
plt.show()

display(Image(url="https://api.memegen.link/images/drake/Submit_based_on_vibes/1050_game_tournament.jpg", width=500))