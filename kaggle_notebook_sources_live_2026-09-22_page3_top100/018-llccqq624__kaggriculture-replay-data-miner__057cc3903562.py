from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

pd.set_option("display.max_colwidth", 120)
plt.style.use("seaborn-v0_8-whitegrid")

OUTPUT_DIR = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path("analysis_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def replay_files() -> list[Path]:
    configured = os.environ.get("KAGGRICULTURE_REPLAY_DIR")
    roots = []
    if configured:
        roots.append(Path(configured))
    roots.extend([
        Path("/kaggle/input/kaggriculture-episodes-2026-07-30"),
        Path("/kaggle/input"),
        Path("research/sample_replay"),
    ])
    seen = set()
    files = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.json"):
            if path.name in {"dataset-metadata.json", "kernel-metadata.json"}:
                continue
            key = str(path.resolve())
            if key not in seen:
                seen.add(key)
                files.append(path)
        if files:
            break
    return sorted(files, key=lambda p: int(p.stem) if p.stem.isdigit() else p.stem)


def _value_after_key(raw: bytes, key: bytes):
    start = raw.find(key)
    if start < 0:
        return None
    colon = raw.find(b":", start + len(key))
    if colon < 0:
        return None
    text = raw[colon + 1 :].decode("utf-8", errors="ignore").lstrip()
    try:
        return json.JSONDecoder().raw_decode(text)[0]
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def replay_header(path: Path) -> dict:
    raw = b""
    with path.open("rb") as stream:
        for limit in (131_072, 524_288, 1_048_576):
            raw += stream.read(limit - len(raw))
            teams = _value_after_key(raw, b'"TeamNames"')
            rewards = _value_after_key(raw, b'"rewards"')
            episode_id = _value_after_key(raw, b'"EpisodeId"')
            if teams is not None and rewards is not None:
                break
    teams = list(teams or [])
    rewards = list(rewards or [])
    while len(teams) < 2:
        teams.append(f"Player {len(teams)}")
    while len(rewards) < 2:
        rewards.append(np.nan)
    clean_rewards = [float(x) if x is not None else np.nan for x in rewards[:2]]
    return {
        "episode_id": int(episode_id or (int(path.stem) if path.stem.isdigit() else -1)),
        "path": str(path),
        "player_0": teams[0],
        "player_1": teams[1],
        "reward_0": clean_rewards[0],
        "reward_1": clean_rewards[1],
        "avg_reward": float(np.nanmean(clean_rewards)),
        "winner": teams[int(np.nanargmax(clean_rewards))] if not np.all(np.isnan(clean_rewards)) and clean_rewards[0] != clean_rewards[1] else "Tie",
    }


def replay_index(files: list[Path]) -> pd.DataFrame:
    rows = [replay_header(path) for path in files]
    return pd.DataFrame(rows).sort_values(["avg_reward", "episode_id"], ascending=[False, True]).reset_index(drop=True)


def load_replay(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def operation_name(action) -> str:
    if isinstance(action, list) and action:
        return str(action[0])
    if isinstance(action, str):
        return action
    return "PASS"


def show(frame: pd.DataFrame, rows: int = 12):
    try:
        from IPython.display import display
        display(frame.head(rows))
    except ImportError:
        print(frame.head(rows).to_string(index=False))


def save(frame: pd.DataFrame, name: str):
    path = OUTPUT_DIR / name
    frame.to_csv(path, index=False)
    print(f"Saved {len(frame):,} rows -> {path}")
    return path

TOP_REPLAYS = 24

files = replay_files()
index = replay_index(files)
selected = index.head(min(TOP_REPLAYS, len(index)))
print(f"Mining {len(selected)} replays from a collection of {len(index):,}")

episode_rows = []
player_rows = []
action_rows = []

for rank, meta in enumerate(selected.itertuples(index=False), start=1):
    replay = load_replay(meta.path)
    teams = list(replay.get("info", {}).get("TeamNames", [meta.player_0, meta.player_1]))
    rewards = list(replay.get("rewards", [meta.reward_0, meta.reward_1]))
    steps = replay.get("steps", [])
    episode_rows.append({
        "collection_rank": rank,
        "episode_id": meta.episode_id,
        "player_0": teams[0],
        "player_1": teams[1],
        "reward_0": rewards[0],
        "reward_1": rewards[1],
        "winner": meta.winner,
        "turns": len(steps),
    })

    for player_id, team in enumerate(teams[:2]):
        counters = Counter()
        for step_id, states in enumerate(steps):
            state = states[player_id]
            action = state.get("action") or {}
            if not isinstance(action, dict):
                action = {"farmer": action}
            day, hour = divmod(step_id, 24)

            farmer_op = operation_name(action.get("farmer"))
            counters[f"farmer:{farmer_op}"] += 1
            if farmer_op != "PASS":
                action_rows.append({"episode_id": meta.episode_id, "team": team, "player": player_id, "step": step_id, "day": day, "hour": hour, "actor": "farmer", "operation": farmer_op, "item": None, "quantity": None})

            for hand_id, hand_action in enumerate(action.get("hands") or []):
                hand_op = operation_name(hand_action)
                counters[f"hand:{hand_op}"] += 1
                if hand_op != "PASS":
                    action_rows.append({"episode_id": meta.episode_id, "team": team, "player": player_id, "step": step_id, "day": day, "hour": hour, "actor": f"hand_{hand_id}", "operation": hand_op, "item": None, "quantity": None})

            for order in action.get("market") or []:
                if not isinstance(order, list) or not order:
                    continue
                op = str(order[0])
                item = order[1] if len(order) > 1 else None
                quantity = order[2] if len(order) > 2 else 1
                counters[f"market:{op}"] += 1
                action_rows.append({"episode_id": meta.episode_id, "team": team, "player": player_id, "step": step_id, "day": day, "hour": hour, "actor": "market", "operation": op, "item": item, "quantity": quantity})

        player_rows.append({
            "episode_id": meta.episode_id,
            "team": team,
            "player": player_id,
            "final_reward": rewards[player_id],
            "won": rewards[player_id] > rewards[1 - player_id],
            "farmer_actions": sum(v for k, v in counters.items() if k.startswith("farmer:")),
            "hand_actions": sum(v for k, v in counters.items() if k.startswith("hand:")),
            "market_orders": sum(v for k, v in counters.items() if k.startswith("market:")),
            "top_operations": " | ".join(f"{k}={v}" for k, v in counters.most_common(12)),
        })

episodes = pd.DataFrame(episode_rows)
players = pd.DataFrame(player_rows)
actions = pd.DataFrame(action_rows)
save(episodes, "episodes.csv")
save(players, "players.csv")
save(actions, "action_events.csv")

show(players.sort_values("final_reward", ascending=False), 15)
if not actions.empty:
    popular = actions.groupby(["actor", "operation"]).size().rename("events").reset_index().sort_values("events", ascending=False).head(18)
    show(popular, 18)
    labels = popular["actor"] + ": " + popular["operation"]
    ax = popular.assign(label=labels).sort_values("events").plot.barh(x="label", y="events", legend=False, figsize=(9, 6), color="#386641")
    ax.set_title("What busy farms spend their turns doing")
    ax.set_xlabel("Recorded events")
    ax.set_ylabel("")
    plt.tight_layout()
    plt.show()