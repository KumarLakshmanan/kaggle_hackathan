import json, random
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams.update({
    'figure.dpi': 130,
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'figure.facecolor': 'white',
})
random.seed(42)
np.random.seed(42)

# Load replays from the attached dataset
# On Kaggle: /kaggle/input/datasets/nathanjacob/kaggriculture-replay-actions/
# Locally: point to your own replay directory
KAGGLE_PATH = Path("/kaggle/input/datasets/nathanjacob/kaggriculture-replay-actions/")
REPLAY_DIR = KAGGLE_PATH if KAGGLE_PATH.exists() else Path("../replays/")

replay_files = sorted(REPLAY_DIR.glob("*.json"))
print(f"Found {len(replay_files)} replays")

def action_to_fingerprint(action):
    """Convert one turn's actions into a structural fingerprint.

    Keeps action types and item types, strips quantities.
    'BUY_SEED WHEAT 3' and 'BUY_SEED WHEAT 5' both become 'BUY_SEED|WHEAT'.
    """
    parts = []
    # Farmer
    farmer = action.get('farmer', ['PASS'])
    parts.append('F:' + (farmer[0] if farmer else 'PASS'))
    # Market — type + item, no quantity
    for m in action.get('market', []):
        if not m:
            continue
        if len(m) >= 2:
            parts.append('M:' + str(m[0]) + '|' + str(m[1]))
        else:
            parts.append('M:' + str(m[0]))
    # Farmhands — action + target
    for h in action.get('hands', []):
        if isinstance(h, list) and len(h) >= 1:
            parts.append('H:' + '|'.join(str(x) for x in h[:2]))
        elif isinstance(h, str):
            parts.append('H:' + h)
    return ';'.join(parts)


def extract_fingerprints(replay_path, n_turns=144):
    """Extract fingerprint sequences for both players."""
    with open(replay_path) as f:
        data = json.load(f)
    teams = data['info']['TeamNames']
    results = []
    for pidx in range(2):
        fp_seq = []
        for s in range(min(n_turns, len(data['steps']))):
            action = data['steps'][s][pidx]['action']
            fp_seq.append(action_to_fingerprint(action))
        results.append({
            'team': teams[pidx],
            'fingerprint': fp_seq,
            'reward': data['rewards'][pidx],
        })
    return results

print("Extracting fingerprints from all replays...")
all_entries = []

for rp in replay_files:
    try:
        all_entries.extend(extract_fingerprints(rp))
    except Exception:
        continue

print(f"  {len(all_entries)} team-game entries from {len(replay_files)} replays")

# For each team, pick their most-played fingerprint (the "canonical" strategy)
team_fingerprints = defaultdict(list)
team_rewards = defaultdict(list)
for entry in all_entries:
    team_fingerprints[entry['team']].append(tuple(entry['fingerprint']))
    team_rewards[entry['team']].append(entry['reward'])

team_canonical = {}
team_avg_reward = {}
team_game_count = {}
for team, fps in team_fingerprints.items():
    team_canonical[team] = list(Counter(fps).most_common(1)[0][0])
    team_avg_reward[team] = np.mean(team_rewards[team])
    team_game_count[team] = len(fps)

print(f"  {len(team_canonical)} unique teams")

def fingerprint_similarity(fp1, fp2):
    """Fraction of turns with identical action fingerprints."""
    n = min(len(fp1), len(fp2))
    if n == 0:
        return 0.0
    return sum(a == b for a, b in zip(fp1, fp2)) / n

# Take teams with enough games for a reliable fingerprint
min_games = 3
eligible = [t for t in team_fingerprints if len(team_fingerprints[t]) >= min_games]
eligible.sort(key=lambda t: -team_avg_reward[t])

N = min(200, len(eligible))
teams = eligible[:N]
print(f"Computing {N}x{N} similarity matrix ({N*(N-1)//2:,} pairs)...")

sim = np.zeros((N, N))
for i in range(N):
    for j in range(i, N):
        s = fingerprint_similarity(team_canonical[teams[i]], team_canonical[teams[j]])
        sim[i, j] = s
        sim[j, i] = s

upper = sim[np.triu_indices(N, k=1)]
print(f"  Mean pairwise similarity: {upper.mean():.1%}")
print(f"  Pairs ≥ 90% similar: {(upper >= 0.90).mean():.0%}")
print(f"  Pairs ≥ 80% similar: {(upper >= 0.80).mean():.0%}")

class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py: return
        if self.rank[px] < self.rank[py]: px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]: self.rank[px] += 1

threshold = 0.90
uf = UnionFind(N)
for i in range(N):
    for j in range(i + 1, N):
        if sim[i, j] >= threshold:
            uf.union(i, j)

clusters = defaultdict(list)
for i in range(N):
    clusters[uf.find(i)].append(i)

sizes = sorted([len(v) for v in clusters.values()], reverse=True)
main_root = max(clusters, key=lambda k: len(clusters[k]))
main_idx = set(clusters[main_root])
outlier_idx = [i for i in range(N) if i not in main_idx]

print(f"Clusters at ≥{threshold:.0%}: {len(sizes)}")
print(f"  Largest: {sizes[0]} teams ({sizes[0]/N:.0%})")
print(f"  Outliers (cluster size=1): {sum(1 for s in sizes if s == 1)}")

# Reorder: main cluster first (sorted by reward), then outliers (sorted by reward)
main_sorted = sorted(main_idx, key=lambda i: -team_avg_reward[teams[i]])
outlier_sorted = sorted(outlier_idx, key=lambda i: -team_avg_reward[teams[i]])
order = main_sorted + outlier_sorted

sim_ordered = sim[np.ix_(order, order)]
boundary = len(main_sorted)

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(sim_ordered, cmap='inferno', vmin=0.4, vmax=1.0, aspect='equal')
# Mark the boundary between main cluster and outliers
ax.axhline(y=boundary - 0.5, color='white', linewidth=1.5, linestyle='--', alpha=0.7)
ax.axvline(x=boundary - 0.5, color='white', linewidth=1.5, linestyle='--', alpha=0.7)

ax.set_xlabel("Team index")
ax.set_ylabel("Team index")
ax.set_title(f"Strategy Similarity Across {N} Teams (first 144 turns)\n"
             f"Main cluster = {len(main_sorted)} teams  |  Mean similarity = {upper.mean():.0%}")
cbar = plt.colorbar(im, ax=ax, label="Fraction of identical turns", shrink=0.8)
ax.text(boundary/2, -6, f"← Main cluster ({len(main_sorted)}) →",
        ha='center', fontsize=9, color='white',
        bbox=dict(boxstyle='round', facecolor='#FF5722', alpha=0.8))
plt.tight_layout()
plt.savefig("similarity_heatmap.png", dpi=150, bbox_inches='tight')
plt.show()

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.hist(upper, bins=60, color='#2196F3', edgecolor='white', alpha=0.9, zorder=2)
ax.axvline(x=0.90, color='red', linestyle='--', linewidth=2, label='90% clustering threshold', zorder=3)

pct90 = (upper >= 0.90).mean() * 100
pct80 = (upper >= 0.80).mean() * 100

ax.set_xlabel("Pairwise Similarity (fraction of identical opening turns)")
ax.set_ylabel("Number of team pairs")
ax.set_title("How Similar Are Teams' Strategies?")
ax.legend(loc='upper left')

ax.text(0.97, 0.95,
        f"{pct90:.0f}% of pairs ≥ 90% similar\n"
        f"{pct80:.0f}% of pairs ≥ 80% similar",
        transform=ax.transAxes, fontsize=11, ha='right', va='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

# Annotate the bimodal peaks
ax.annotate("Outlier ↔ Main cluster\n(low similarity)",
           xy=(0.03, 0), xytext=(0.15, ax.get_ylim()[1]*0.5),
           arrowprops=dict(arrowstyle='->', color='gray'),
           fontsize=9, color='gray', ha='center')

plt.tight_layout()
plt.savefig("similarity_distribution.png", dpi=150, bbox_inches='tight')
plt.show()

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Left: bar chart of cluster sizes
ax = axes[0]
top_sizes = sizes[:min(15, len(sizes))]
colors = ['#FF5722' if i == 0 else '#90A4AE' for i in range(len(top_sizes))]
ax.bar(range(len(top_sizes)), top_sizes, color=colors, edgecolor='white')
ax.set_xlabel("Cluster rank")
ax.set_ylabel("Teams in cluster")
ax.set_title(f"Strategy Clusters (≥{threshold:.0%} similarity)")
ax.annotate(f"{sizes[0]} teams\n({sizes[0]/N:.0%} of all)",
           xy=(0, sizes[0]), xytext=(2.5, sizes[0] * 0.8),
           arrowprops=dict(arrowstyle='->', color='black', lw=1.5),
           fontsize=13, fontweight='bold')

# Right: donut chart
ax = axes[1]
main_n = sizes[0]
other_n = N - main_n
wedges, texts, autotexts = ax.pie(
    [main_n, other_n],
    labels=[f'Main cluster\n({main_n} teams)', f'Outliers\n({other_n} teams)'],
    colors=['#FF5722', '#90A4AE'],
    autopct='%1.0f%%', startangle=90,
    textprops={'fontsize': 12},
    wedgeprops={'edgecolor': 'white', 'linewidth': 2},
    pctdistance=0.75,
)
centre_circle = plt.Circle((0, 0), 0.45, fc='white')
ax.add_artist(centre_circle)
ax.set_title("Share of Teams")

plt.tight_layout()
plt.savefig("cluster_breakdown.png", dpi=150, bbox_inches='tight')
plt.show()

main_rewards = np.array([team_avg_reward[teams[i]] for i in main_sorted])
outlier_rewards = np.array([team_avg_reward[teams[i]] for i in outlier_sorted]) if outlier_sorted else np.array([])

fig, ax = plt.subplots(figsize=(10, 5))
lo = min(main_rewards.min(), outlier_rewards.min() if len(outlier_rewards) else main_rewards.min()) * 0.95
hi = max(main_rewards.max(), outlier_rewards.max() if len(outlier_rewards) else main_rewards.max()) * 1.02
bins = np.linspace(lo, hi, 40)

ax.hist(main_rewards, bins=bins, alpha=0.85, label=f'Main cluster ({len(main_sorted)} teams)',
        color='#FF5722', edgecolor='white', zorder=2)
if len(outlier_rewards):
    ax.hist(outlier_rewards, bins=bins, alpha=0.7, label=f'Outliers ({len(outlier_sorted)} teams)',
            color='#2196F3', edgecolor='white', zorder=2)

ax.set_xlabel("Average Game Reward")
ax.set_ylabel("Number of teams")
ax.set_title("Same Strategy, Different Results")
ax.legend()

spread = main_rewards.max() - main_rewards.min()
ax.text(0.02, 0.95,
        f"Within the main cluster:\n"
        f"  Best:  {main_rewards.max():>10,.0f}\n"
        f"  Worst: {main_rewards.min():>10,.0f}\n"
        f"  Gap:   {spread:>10,.0f}  ({spread/main_rewards.mean():.0%} of mean)",
        transform=ax.transAxes, fontsize=10, va='top', family='monospace',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
plt.tight_layout()
plt.savefig("reward_spread.png", dpi=150, bbox_inches='tight')
plt.show()

# For each main-cluster team, compute their mean similarity to all other main-cluster members
main_list = list(main_sorted)
main_sim_scores = []
for i in main_list:
    sims_to_others = [sim[i, j] for j in main_list if j != i]
    main_sim_scores.append(np.mean(sims_to_others))

fig, ax = plt.subplots(figsize=(9, 6))
rewards_arr = np.array([team_avg_reward[teams[i]] for i in main_list])
sims_arr = np.array(main_sim_scores)

scatter = ax.scatter(sims_arr, rewards_arr, c=rewards_arr, cmap='RdYlGn',
                     s=40, alpha=0.7, edgecolors='gray', linewidth=0.3, zorder=2)
plt.colorbar(scatter, ax=ax, label="Avg reward", shrink=0.8)

ax.set_xlabel("Mean similarity to other main-cluster teams")
ax.set_ylabel("Average game reward")
ax.set_title("Conformity vs. Performance\n(Each dot = one team in the main cluster)")

# Trend line
z = np.polyfit(sims_arr, rewards_arr, 1)
x_line = np.linspace(sims_arr.min(), sims_arr.max(), 100)
ax.plot(x_line, np.polyval(z, x_line), '--', color='gray', alpha=0.5, zorder=1)

corr = np.corrcoef(sims_arr, rewards_arr)[0, 1]
ax.text(0.03, 0.05, f"Pearson r = {corr:.2f}",
        transform=ax.transAxes, fontsize=11,
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

plt.tight_layout()
plt.savefig("conformity_vs_reward.png", dpi=150, bbox_inches='tight')
plt.show()

# Re-extract full-game fingerprints for a sample of replays
print("Extracting full-game fingerprints...")
sample_files = random.sample(replay_files, min(200, len(replay_files)))

full_entries = []
for rp in sample_files:
    try:
        with open(rp) as f:
            data = json.load(f)
        teams_names = data['info']['TeamNames']
        for pidx in range(2):
            fp = []
            for s in range(len(data['steps'])):
                action = data['steps'][s][pidx]['action']
                fp.append(action_to_fingerprint(action))
            full_entries.append({'team': teams_names[pidx], 'fingerprint': fp})
    except Exception:
        continue

# Build canonical full fingerprints
full_fps = defaultdict(list)
for e in full_entries:
    full_fps[e['team']].append(tuple(e['fingerprint']))

full_canonical = {}
for team, fps in full_fps.items():
    full_canonical[team] = list(Counter(fps).most_common(1)[0][0])

# Compute windowed similarity for main-cluster teams
main_teams_with_full = [teams[i] for i in main_list if teams[i] in full_canonical]
n_full = min(80, len(main_teams_with_full))  # cap for speed
sample_main = random.sample(main_teams_with_full, n_full)

window = 36  # 36-turn windows (5% of game)
max_turns = min(len(full_canonical[t]) for t in sample_main)
n_windows = max_turns - window + 1

window_sims = []
window_centers = []
for start in range(0, n_windows, window // 2):  # 50% overlap
    end = start + window
    if end > max_turns:
        break
    pair_sims = []
    for i in range(n_full):
        for j in range(i + 1, n_full):
            fp_i = full_canonical[sample_main[i]][start:end]
            fp_j = full_canonical[sample_main[j]][start:end]
            pair_sims.append(sum(a == b for a, b in zip(fp_i, fp_j)) / window)
    window_sims.append(np.mean(pair_sims))
    window_centers.append((start + end) / 2)

fig, ax = plt.subplots(figsize=(11, 4.5))
ax.fill_between(window_centers, window_sims, alpha=0.3, color='#FF5722')
ax.plot(window_centers, window_sims, '-o', color='#FF5722', markersize=3, linewidth=2)
ax.set_xlabel("Turn (center of 36-turn window)")
ax.set_ylabel("Mean pairwise similarity")
ax.set_title("Strategy Similarity Over the Full Game (Main Cluster)")
ax.set_ylim(0, 1.05)
ax.set_xlim(0, max_turns)
ax.axhline(y=0.9, color='gray', linestyle=':', alpha=0.4)

# Annotate game phases
phases = [(0, 144, 'Opening\n(turns 0-144)'), (144, 360, 'Midgame'),
          (360, 540, 'Late game'), (540, 720, 'Endgame')]
for start, end, label in phases:
    mid = (start + end) / 2
    ax.axvline(x=start, color='lightgray', linestyle='-', alpha=0.3)
    ax.text(mid, 0.05, label, ha='center', fontsize=8, color='gray')

plt.tight_layout()
plt.savefig("similarity_over_time.png", dpi=150, bbox_inches='tight')
plt.show()