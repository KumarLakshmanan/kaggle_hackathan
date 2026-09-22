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

TEAM_QUERY = "Jiachen Li"

files = replay_files()
print(f"Found {len(files):,} replay files")
index = replay_index(files)
save(index.drop(columns="path"), "replay_index.csv")

query = TEAM_QUERY.casefold().strip()
mask_0 = index["player_0"].str.casefold().str.contains(query, regex=False)
mask_1 = index["player_1"].str.casefold().str.contains(query, regex=False)
hits = index[mask_0 | mask_1].copy()

if hits.empty:
    print(f"No replay contains {TEAM_QUERY!r}. The highlight reel remains mysterious.")
    crowd = pd.concat([index["player_0"], index["player_1"]]).value_counts().rename_axis("team").rename("appearances").reset_index()
    print("Try one of the busiest names in this collection:")
    show(crowd, 15)
else:
    hits["seat"] = np.where(mask_0.loc[hits.index], 0, 1)
    hits["team"] = np.where(hits["seat"].eq(0), hits["player_0"], hits["player_1"])
    hits["opponent"] = np.where(hits["seat"].eq(0), hits["player_1"], hits["player_0"])
    hits["team_reward"] = np.where(hits["seat"].eq(0), hits["reward_0"], hits["reward_1"])
    hits["opponent_reward"] = np.where(hits["seat"].eq(0), hits["reward_1"], hits["reward_0"])
    hits["result"] = np.select(
        [hits["team_reward"] > hits["opponent_reward"], hits["team_reward"] < hits["opponent_reward"]],
        ["Win", "Loss"],
        default="Tie",
    )
    all_rewards = pd.concat([index["reward_0"], index["reward_1"]]).dropna().to_numpy(dtype=float)
    hits["collection_percentile"] = hits["team_reward"].map(lambda value: round(float((all_rewards <= value).mean() * 100), 1))
    columns = ["episode_id", "team", "opponent", "seat", "result", "team_reward", "opponent_reward", "collection_percentile", "avg_reward"]
    show(hits[columns].sort_values("team_reward", ascending=False), 25)
    save(hits[columns], "highlight_reel_hits.csv")

    result_counts = hits["result"].value_counts().reindex(["Win", "Tie", "Loss"], fill_value=0)
    print(f"\n{len(hits):,} appearances | {result_counts['Win']} wins | {hits['opponent'].nunique()} different opponents")
    ax = result_counts.plot.bar(color=["#2a9d8f", "#e9c46a", "#e76f51"], figsize=(7, 4), rot=0)
    ax.set_title(f"{TEAM_QUERY}: replay results")
    ax.set_xlabel("")
    ax.set_ylabel("Episodes")
    plt.tight_layout()
    plt.show()