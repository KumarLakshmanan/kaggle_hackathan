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
SAMPLE_EVERY_TURNS = 6

files = replay_files()
index = replay_index(files)
selected = index.head(min(TOP_REPLAYS, len(index)))
market_rows = []

for meta in selected.itertuples(index=False):
    replay = load_replay(meta.path)
    for step_id, states in enumerate(replay.get("steps", [])):
        if step_id % SAMPLE_EVERY_TURNS:
            continue
        obs = states[0].get("observation") or {}
        market = obs.get("market") or {}
        prices = market.get("prices") or {}
        inventory = market.get("inventory") or {}
        day, hour = divmod(step_id, 24)
        for product, price in prices.items():
            market_rows.append({
                "episode_id": meta.episode_id,
                "step": step_id,
                "day": day,
                "hour": hour,
                "product": product,
                "price": float(price),
                "inventory": float(inventory.get(product, np.nan)),
            })

market = pd.DataFrame(market_rows)
weather = market.groupby(["day", "product"]).agg(
    median_price=("price", "median"),
    q25_price=("price", lambda x: x.quantile(0.25)),
    q75_price=("price", lambda x: x.quantile(0.75)),
    min_price=("price", "min"),
    max_price=("price", "max"),
    median_inventory=("inventory", "median"),
    observations=("price", "size"),
).reset_index()
save(market, "market_samples.csv")
save(weather, "market_weather.csv")

products = sorted(weather["product"].unique())
fig, axes = plt.subplots(3, 3, figsize=(16, 11), sharex=True)
for ax, product in zip(axes.flat, products):
    frame = weather[weather["product"] == product].sort_values("day")
    x = frame["day"].to_numpy(dtype=float)
    median = frame["median_price"].to_numpy(dtype=float)
    low = frame["q25_price"].to_numpy(dtype=float)
    high = frame["q75_price"].to_numpy(dtype=float)
    ax.plot(x, median, color="#264653", linewidth=2)
    ax.fill_between(x, low, high, color="#2a9d8f", alpha=0.25)
    ax.set_title(product.title())
    ax.set_ylabel("Coins")
for ax in axes[-1]:
    ax.set_xlabel("Day")
fig.suptitle("Market forecast: median price and middle 50% band", fontsize=16)
plt.tight_layout()
plt.show()

summary_rows = []
for product, frame in weather.groupby("product"):
    frame = frame.sort_values("day")
    best = frame.loc[frame["median_price"].idxmax()]
    summary_rows.append({
        "product": product,
        "best_median_day": int(best["day"]),
        "best_median_price": float(best["median_price"]),
        "season_low": float(frame["min_price"].min()),
        "season_high": float(frame["max_price"].max()),
        "median_price_range": float(frame["median_price"].max() - frame["median_price"].min()),
        "final_day_median": float(frame.iloc[-1]["median_price"]),
    })
summary = pd.DataFrame(summary_rows).sort_values("median_price_range", ascending=False)
save(summary, "market_weather_summary.csv")
show(summary, 12)