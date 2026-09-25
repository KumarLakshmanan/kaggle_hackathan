from pathlib import Path
import hashlib
import importlib.util
import itertools
import json
import math
import time
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from kaggle_environments import make

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams.update({"figure.figsize": (10, 4.8), "axes.titleweight": "bold"})

ROOT = Path("/Users/wei/Documents/Codex/2026-09-13/ge")
ORIGINAL_PATH = ROOT / "work/v46d_review/main.py"
REBUILT_PATH = ROOT / "work/v46d_rebuilt/main.py"
DELIVERED_SOURCE = ROOT / "outputs/main_v46d_skill_rebuilt.py"
DELIVERED_ARCHIVE = ROOT / "outputs/submission_v46d_skill_rebuilt.tar.gz"

FAST_MODE = True
EVAL_SEEDS = [6100, 6101] if FAST_MODE else list(range(6000, 6064))
ROUTE_DEMO_SEED = 2125   # vs pass: YARN_STORE, ICE_CREAM_SHOP; switch is enabled
STRONG_GATE_SEED = 2265  # vs starter: same world; opponent activity blocks the switch
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

artifact_rows = []
for path in [ORIGINAL_PATH, REBUILT_PATH, DELIVERED_SOURCE, DELIVERED_ARCHIVE]:
    artifact_rows.append({
        "artifact": f"{path.parent.name}/{path.name}",
        "exists": path.exists(),
        "size_kib": round(path.stat().st_size / 1024, 1) if path.exists() else None,
        "sha256": sha256(path)[:16] if path.exists() else None,
    })
print(pd.DataFrame(artifact_rows).to_string(index=False))
print(
    f"\nFAST_MODE={FAST_MODE}; EVAL_SEEDS={EVAL_SEEDS}; "
    f"passive route seed={ROUTE_DEMO_SEED}; strong-gate seed={STRONG_GATE_SEED}"
)

AGENTS = ["rebuilt", "original", "starter", "pass"]
match_rows = []
started = time.perf_counter()
for first, second in itertools.combinations(AGENTS, 2):
    for seed in EVAL_SEEDS:
        for left, right in [(first, second), (second, first)]:
            summary, _ = run_game(left, right, seed, capture_trace=False)
            match_rows.append(summary)
MATCHES = pd.DataFrame(match_rows)

perspective_rows = []
for row in match_rows:
    perspective_rows.extend([
        {
            "seed": row["seed"], "model": row["left"], "opponent": row["right"], "seat": 0,
            "reward": row["left_reward"], "opponent_reward": row["right_reward"],
            "battle_margin": row["left_margin"], "shops": row["shops"], "route": row["left_route"],
        },
        {
            "seed": row["seed"], "model": row["right"], "opponent": row["left"], "seat": 1,
            "reward": row["right_reward"], "opponent_reward": row["left_reward"],
            "battle_margin": -row["left_margin"], "shops": row["shops"], "route": row["right_route"],
        },
    ])
PERSPECTIVE = pd.DataFrame(perspective_rows)

# A known passive-world route-switch replay plus a strong-opponent gate check.
special_rows = []
SPECIAL_TRACES = {}
for left, right, seed in [
    ("original", "pass", ROUTE_DEMO_SEED),
    ("rebuilt", "pass", ROUTE_DEMO_SEED),
    ("original", "starter", STRONG_GATE_SEED),
    ("rebuilt", "starter", STRONG_GATE_SEED),
]:
    summary, trace = run_game(left, right, seed, capture_trace=True)
    special_rows.append(summary)
    SPECIAL_TRACES[(left, right, seed)] = trace
SPECIAL = pd.DataFrame(special_rows)

elapsed = time.perf_counter() - started
compact = MATCHES[["seed", "left", "right", "left_reward", "right_reward", "left_margin", "shops"]]
print(f"Completed {len(MATCHES)} round-robin games + {len(SPECIAL)} route demos in {elapsed:.1f}s")
print("\nRound-robin sample:")
print(compact.head(10).to_string(index=False))
print("\nRoute demo:")
print(SPECIAL[["seed", "left", "right", "left_reward", "right_reward", "left_margin", "shops", "left_route"]].to_string(index=False))

def fit_bradley_terry(matches, names, ridge=1.0, max_iter=100):
    index = {name: i for i, name in enumerate(names)}
    theta = np.zeros(len(names), dtype=float)
    for _ in range(max_iter):
        gradient = -ridge * theta
        information = ridge * np.eye(len(names))
        for row in matches.to_dict("records"):
            i, j = index[row["left"]], index[row["right"]]
            margin = row["left_margin"]
            outcome = 1.0 if margin > 0 else 0.0 if margin < 0 else 0.5
            diff = np.clip(theta[i] - theta[j], -30, 30)
            probability = 1.0 / (1.0 + np.exp(-diff))
            residual = outcome - probability
            gradient[i] += residual
            gradient[j] -= residual
            weight = probability * (1.0 - probability)
            information[i, i] += weight
            information[j, j] += weight
            information[i, j] -= weight
            information[j, i] -= weight
        step = np.linalg.solve(information + 1e-9 * np.eye(len(names)), gradient)
        theta += step
        theta -= theta.mean()
        if np.max(np.abs(step)) < 1e-9:
            break
    rating = 1000.0 + (400.0 / np.log(10.0)) * theta
    return dict(zip(names, rating))

ratings = fit_bradley_terry(MATCHES, AGENTS)
ranking = (
    PERSPECTIVE.assign(
        win=(PERSPECTIVE.battle_margin > 0).astype(float),
        tie=(PERSPECTIVE.battle_margin == 0).astype(float),
    )
    .groupby("model", as_index=False)
    .agg(
        games=("reward", "size"),
        mean_reward=("reward", "mean"),
        mean_margin=("battle_margin", "mean"),
        median_margin=("battle_margin", "median"),
        win_rate=("win", "mean"),
        tie_rate=("tie", "mean"),
    )
)
ranking["bt_rating"] = ranking.model.map(ratings)
ranking = ranking.sort_values(["bt_rating", "mean_margin"], ascending=False)
print(ranking.round(2).to_string(index=False))

colors = {"rebuilt": "#0F766E", "original": "#64748B", "starter": "#D97706", "pass": "#991B1B"}
fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
order = ranking.model.tolist()
axes[0].barh(order[::-1], ranking.set_index("model").loc[order[::-1], "bt_rating"], color=[colors[x] for x in order[::-1]])
axes[0].axvline(1000, color="#111827", linewidth=1)
axes[0].set_title("Bradley-Terry rating (quick smoke run)")
axes[0].set_xlabel("Rating")
axes[1].barh(order[::-1], ranking.set_index("model").loc[order[::-1], "mean_margin"], color=[colors[x] for x in order[::-1]])
axes[1].axvline(0, color="#111827", linewidth=1)
axes[1].set_title("Mean battle margin")
axes[1].set_xlabel("Reward difference")
axes[1].xaxis.set_major_formatter(lambda x, pos: f"{x/1000:.0f}k")
fig.tight_layout()
plt.show()

base_trace = SPECIAL_TRACES[("original", "pass", ROUTE_DEMO_SEED)]
rebuilt_trace = SPECIAL_TRACES[("rebuilt", "pass", ROUTE_DEMO_SEED)]
base_self = base_trace[base_trace.seat == 0].set_index("step")
rebuilt_self = rebuilt_trace[rebuilt_trace.seat == 0].set_index("step")
common_steps = base_self.index.intersection(rebuilt_self.index)

fig, axes = plt.subplots(3, 1, figsize=(11, 9.0), sharex=True)
axes[0].plot(common_steps, base_self.loc[common_steps, "money"], label="original money", color="#64748B", linewidth=2)
axes[0].plot(common_steps, rebuilt_self.loc[common_steps, "money"], label="rebuilt money", color="#0F766E", linewidth=2)
axes[0].set_ylabel("Money")
axes[0].set_title(f"Route demo reward curve, seed {ROUTE_DEMO_SEED} vs pass")
axes[0].legend()
axes[1].plot(common_steps, rebuilt_self.loc[common_steps, "money"] - base_self.loc[common_steps, "money"], color="#D97706", linewidth=2, label="paired money uplift")
axes[1].axhline(0, color="#111827", linewidth=1)
axes[1].set_ylabel("Uplift")
axes[1].legend()
axes[2].plot(common_steps, rebuilt_self.loc[common_steps, "battle_margin"], color="#0F766E", linewidth=2, label="rebuilt battle margin")
axes[2].axhline(0, color="#111827", linewidth=1)
axes[2].set_ylabel("Battle margin")
axes[2].set_xlabel("Step")
axes[2].legend()
for ax in axes:
    for step in range(72, 577, 72):
        ax.axvline(step, color="#CBD5E1", linewidth=0.8, alpha=0.7)
    ax.axvline(240, color="#B91C1C", linestyle="--", linewidth=1.4)
fig.tight_layout()
plt.show()

metric_rows = []
for row in special_rows:
    metrics = row["left_metrics"] or {}
    metric_rows.append({
        "match": f'{row["left"]} vs {row["right"]} / seed {row["seed"]}',
        "route": row["left_route"],
        "reward": row["left_reward"],
        "margin": row["left_margin"],
        "route_switches": metrics.get("route_switches", 0),
        "capacity_sales": metrics.get("capacity_sales", 0),
        "survival_overrides": metrics.get("survival_overrides", 0),
        "weed_blocks": metrics.get("weed_blocks", 0),
    })
print(pd.DataFrame(metric_rows).to_string(index=False))

TAPES = ORIGINAL._TAPES
DEFAULT = TAPES["default"]
SHOPS = [
    "BAKERY", "PIZZA_SHOP", "BRUNCH_SPOT", "YARN_STORE",
    "ICE_CREAM_SHOP", "PET_CAFE", "SMOOTHIE_SHOP", "FARMERS_MARKET",
]

def action_signature(action):
    return json.dumps(action, sort_keys=True, separators=(",", ":"))

def operation_counts(tape):
    counts = {
        "worker_actions": 0, "move": 0, "crop": 0, "animal": 0, "shed": 0,
        "market_orders": 0, "sell_units": 0, "hire": 0, "buy_land": 0,
    }
    for action in tape:
        workers = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
        for worker in workers:
            op = worker[0] if worker else "PASS"
            if op != "PASS": counts["worker_actions"] += 1
            if op in {"NORTH", "SOUTH", "EAST", "WEST"}: counts["move"] += 1
            if op in {"PLANT", "WATER", "HARVEST", "FERTILIZE", "DIG"}: counts["crop"] += 1
            if op in {"BUILD_COOP", "BUILD_PASTURE", "FEED", "CARE", "COLLECT_FERTILIZER"}: counts["animal"] += 1
            if op in {"PICKUP", "DROP", "PLACE"}: counts["shed"] += 1
        for order in action.get("market") or []:
            counts["market_orders"] += 1
            if order and order[0] == "HIRE": counts["hire"] += 1
            if order and order[0] == "BUY_LAND": counts["buy_land"] += 1
            if order and order[0] == "SELL":
                try: counts["sell_units"] += int(order[2])
                except Exception: pass
    return counts

tape_rows = []
for route, tape in TAPES.items():
    signatures = [action_signature(a) for a in tape]
    default_signatures = [action_signature(a) for a in DEFAULT]
    different = [i for i, (a, b) in enumerate(zip(signatures, default_signatures)) if a != b]
    tape_rows.append({
        "route": route,
        "steps": len(tape),
        "diff_steps_vs_default": len(different),
        "first_diff": min(different) if different else None,
        "last_diff": max(different) if different else None,
        **operation_counts(tape),
    })
TAPE_PROFILE = pd.DataFrame(tape_rows).sort_values("diff_steps_vs_default", ascending=False)
print(f"routes={len(TAPES)}, named pairs={len(TAPES)-1}, tape length range={TAPE_PROFILE.steps.min()}..{TAPE_PROFILE.steps.max()}")
print("\nMost divergent routes:")
print(TAPE_PROFILE.head(12).to_string(index=False))

coverage = pd.DataFrame(0, index=SHOPS, columns=SHOPS, dtype=int)
for route in TAPES:
    if route == "default" or "__" not in route:
        continue
    first, second = route.split("__", 1)
    if first in coverage.index and second in coverage.columns:
        coverage.loc[first, second] = 1

fig, ax = plt.subplots(figsize=(9, 7))
sns.heatmap(
    coverage, annot=True, fmt="d", cmap=sns.color_palette(["#E2E8F0", "#0F766E"], as_cmap=True),
    cbar=False, linewidths=0.5, linecolor="white", square=True, ax=ax,
)
ax.set_title("Dedicated tape coverage for the first two shops")
ax.set_xlabel("Second shop")
ax.set_ylabel("First shop")
ax.tick_params(axis="x", rotation=50)
ax.tick_params(axis="y", rotation=0)
fig.tight_layout()
plt.show()
print(f"Dedicated coverage: {coverage.values.sum()}/64 = {coverage.values.mean():.1%}")

route_names = list(TAPES)
max_steps = min(len(TAPES[name]) for name in route_names)
diversity = []
for step in range(max_steps):
    diversity.append(len({action_signature(TAPES[name][step]) for name in route_names}))
DIVERSITY = pd.DataFrame({"step": np.arange(max_steps), "unique_actions": diversity})

fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
axes[0].plot(DIVERSITY.step, DIVERSITY.unique_actions, color="#0F766E", linewidth=1.8)
axes[0].set_title("Cross-route action diversity by step")
axes[0].set_xlabel("Step")
axes[0].set_ylabel("Unique action signatures")
for step in range(72, 577, 72):
    axes[0].axvline(step, color="#CBD5E1", linewidth=0.8)
axes[0].axvline(240, color="#B91C1C", linestyle="--", linewidth=1.3, label="validated switch")
axes[0].legend()

distance = TAPE_PROFILE[TAPE_PROFILE.route != "default"].nlargest(15, "diff_steps_vs_default").sort_values("diff_steps_vs_default")
axes[1].barh(distance.route, distance.diff_steps_vs_default, color="#D97706")
axes[1].set_title("Top route distances from default")
axes[1].set_xlabel("Different steps")
fig.tight_layout()
plt.show()

checkpoint_view = DIVERSITY[DIVERSITY.step.isin([72, 144, 216, 240, 288, 360, 432, 504, 576])]
print(checkpoint_view.to_string(index=False))

def action_bucket_counts(action):
    buckets = {"move": 0, "crop": 0, "animal": 0, "shed": 0, "sell": 0, "capital": 0}
    workers = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
    for worker in workers:
        op = worker[0] if worker else "PASS"
        if op in {"NORTH", "SOUTH", "EAST", "WEST"}: buckets["move"] += 1
        elif op in {"PLANT", "WATER", "HARVEST", "FERTILIZE", "DIG"}: buckets["crop"] += 1
        elif op in {"BUILD_COOP", "BUILD_PASTURE", "FEED", "CARE", "COLLECT_FERTILIZER"}: buckets["animal"] += 1
        elif op in {"PICKUP", "DROP", "PLACE"}: buckets["shed"] += 1
    for order in action.get("market") or []:
        if order and order[0] == "SELL": buckets["sell"] += 1
        elif order: buckets["capital"] += 1
    return buckets

selected_routes = ["default", "YARN_STORE__YARN_STORE", "YARN_STORE__SMOOTHIE_SHOP"]
density_rows = []
for route in selected_routes:
    for step, action in enumerate(TAPES[route]):
        density_rows.append({"route": route, "day": step // 24, **action_bucket_counts(action)})
density = pd.DataFrame(density_rows).groupby(["route", "day"], as_index=False).sum()

fig, axes = plt.subplots(len(selected_routes), 1, figsize=(12, 8.5), sharex=True)
palette = {"move": "#64748B", "crop": "#16A34A", "animal": "#7C3AED", "shed": "#0891B2", "sell": "#D97706", "capital": "#B91C1C"}
for ax, route in zip(axes, selected_routes):
    subset = density[density.route == route].set_index("day")
    for bucket, color in palette.items():
        ax.plot(subset.index, subset[bucket], label=bucket, color=color, linewidth=1.5)
    ax.set_title(route, loc="left", fontsize=10)
    ax.set_ylabel("actions/day")
axes[-1].set_xlabel("Day")
axes[0].legend(ncol=6, fontsize=8, loc="upper right")
fig.suptitle("Daily action density of representative tapes", y=1.01, fontweight="bold")
fig.tight_layout()
plt.show()

def normalize_replay_json(replay_or_path):
    if isinstance(replay_or_path, (str, Path)):
        replay = json.loads(Path(replay_or_path).read_text())
    else:
        replay = replay_or_path
    rows = []
    for frame_index, frame in enumerate(replay["steps"]):
        shared = frame[0]["observation"]
        farms = shared["farms"]
        shops = [str(x) for x in shared["town"].get("unlocked_shops", [])]
        prices = shared["market"].get("prices", {})
        inventory = shared["market"].get("inventory", {})
        for seat, state in enumerate(frame):
            obs = state["observation"]
            farm, opponent = farms[seat], farms[1 - seat]
            private = obs.get("private", {})
            shed = private.get("shed", {})
            own_tiles, opp_tiles = tile_features(farm), tile_features(opponent)
            row = {
                "frame": frame_index, "step": obs.get("step", frame_index),
                "day": obs.get("day", 0), "hour": obs.get("hour", 0), "seat": seat,
                "model": f"player_{seat}", "opponent": f"player_{1-seat}",
                "money": farm.get("money", 0), "opponent_money": opponent.get("money", 0),
                "battle_margin": farm.get("money", 0) - opponent.get("money", 0),
                "shed_total": sum(max(0, int(v or 0)) for v in shed.values()),
                "carried_total": sum(sum(max(0, int(v or 0)) for v in bag.values()) for bag in private.get("inventories", [])),
                "hands": len(farm.get("hands", [])), "opponent_hands": len(opponent.get("hands", [])),
                "land": len(farm.get("unlocked_quadrants", [])), "opponent_land": len(opponent.get("unlocked_quadrants", [])),
                "shops": "__".join(shops), **own_tiles,
                **{f"opponent_{k}": v for k, v in opp_tiles.items()},
                **action_features(state.get("action")),
            }
            for product in PRODUCTS:
                row[f"price_{product}"] = int(prices.get(product, 0) or 0)
                row[f"market_{product}"] = int(inventory.get(product, 0) or 0)
            rows.append(row)
    return pd.DataFrame(rows)

print("Usage: replay_df = normalize_replay_json('/path/to/replay.json')")
print("Then: replay_events(replay_df, seat=0), checkpoint_features(replay_df, observer_seat=0)")

## 14. Review Checklist

- [ ] Does the formal comparison fix the same seed, opponent, and seat?
- [ ] Does it report reward uplift, margin uplift, p10, worst case, and positive/tie/negative counts?
- [ ] Does the BT input include both seats, a connected opponent graph, and consistent tie handling?
- [ ] Does every route alias have checkpoint compatibility checks and an opponent gate?
- [ ] Does replay logging capture shop unlocks, shed pressure, opponent activity, market inventory, and SELL events?
- [ ] Is every new defensive action restricted to the minimum necessary change?
- [ ] Are there independent holdouts for strong opponents, passive opponents, and mirrored self-play?
- [ ] Are runtime limits, exception fallback, and the submission rule of root-level `main.py` verified?

**Current recommendation:** Keep the rebuilt v46d agent as the stable baseline. Do not expand unscreened route aliases in the next version. Implement replay-verifiable market counterfactuals first, then use contextual BT and paired uplift to decide whether the change should enter the submission.