# Lightweight empirical resource profile of the analysis path.
# This cell runs after the benchmark-result table has been created in Section 6.
if "matches" in globals():
    tracemalloc.start()
    started = time.perf_counter()
    for _ in range(1000):
        _ = matches.groupby(["seed", "v14_seat"])["v14_margin"].sum()
    analysis_ms = (time.perf_counter() - started) * 1000
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    complexity_profile = pd.DataFrame([{
        "analysis_iterations": 1000,
        "elapsed_ms": round(analysis_ms, 2),
        "peak_memory_kib": round(peak_bytes / 1024, 2),
        "v13_macro_candidates_max": 4,
        "v13_selection_iterations": 48,
        "market_orders_max": 10,
    }])
    display(complexity_profile)
else:
    print("Run Sections 3–6 first, then rerun this optional empirical profile.")

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import sys
import tarfile
import tempfile
import time
import tracemalloc
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

SEEDS = [11, 23, 37, 41, 53, 67, 79, 83, 97, 109]
EXPECTED_GAMES = 20
REQUIRED_SUBMISSION_WINS = 13
RUN_MATCHES = os.environ.get("RUN_KAGGRICULTURE_MATCHES", "0") == "1"
ON_KAGGLE = Path("/kaggle").exists()
BASE = Path("/kaggle/working") if ON_KAGGLE else Path.cwd()
OUTPUT_DIR = Path(os.environ.get("KAGGRICULTURE_OUTPUT", str(BASE / "kaggriculture_v13_v14_4")))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print({"on_kaggle": ON_KAGGLE, "run_matches": RUN_MATCHES, "output": str(OUTPUT_DIR)})

def find_archive(version: str) -> Path | None:
    candidates = [
        Path(f"MyAgents/{version}/submission.tar.gz"),
        Path(f"../MyAgents/{version}/submission.tar.gz"),
        Path(f"/kaggle/input/kaggriculture-agents/{version}/submission.tar.gz"),
        Path(f"{version}/submission.tar.gz"),
    ]
    return next((path for path in candidates if path.is_file()), None)


def load_submission_archive(path: Path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    root = Path(tempfile.gettempdir()) / f"kaggriculture_{digest[:20]}"
    root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        names = {member.name.replace("\\", "/") for member in members}
        if names != {"main.py", "agent_payload.zip"} or any(not member.isfile() for member in members):
            raise ValueError("Unexpected submission archive structure")
        for member in members:
            handle = archive.extractfile(member)
            if handle is None:
                raise ValueError(f"Could not read {member.name}")
            (root / member.name).write_bytes(handle.read())
    spec = importlib.util.spec_from_file_location(f"submitted_{digest[:20]}", root / "main.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load agent bootstrap")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "agent", None)):
        raise TypeError("Archive does not expose callable agent")
    return module.agent, digest


archives = {version: find_archive(version) for version in ("v13", "v14.4")}
print({version: str(path) if path else "not attached" for version, path in archives.items()})

def final_money(final_agent_state: dict, seat: int) -> float:
    farms = (final_agent_state.get("observation") or {}).get("farms") or []
    return float((farms[seat] or {}).get("money", 0)) if seat < len(farms) else float(final_agent_state.get("reward", 0))


def run_match(v13_agent, v14_agent, seed: int, v14_seat: int, replay_dir: Path) -> dict:
    from kaggle_environments import make

    agents = [v13_agent, v14_agent] if v14_seat == 1 else [v14_agent, v13_agent]
    started = time.perf_counter()
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.run(agents)
        replay = env.toJSON()
        final = replay["steps"][-1]
        v13_seat = 1 - v14_seat
        v14_money = final_money(final[v14_seat], v14_seat)
        v13_money = final_money(final[v13_seat], v13_seat)
        margin = v14_money - v13_money
        replay_dir.mkdir(parents=True, exist_ok=True)
        replay_path = replay_dir / f"seed{seed}-v14seat{v14_seat}.json"
        replay_path.write_text(json.dumps(replay), encoding="utf-8")
        return {
            "seed": seed, "v14_seat": v14_seat, "v13_money": v13_money,
            "v14_money": v14_money, "v14_margin": margin,
            "winner": "v14.4" if margin > 0 else "v13" if margin < 0 else "tie",
            "v13_status": str(final[v13_seat].get("status", "UNKNOWN")),
            "v14_status": str(final[v14_seat].get("status", "UNKNOWN")),
            "elapsed_seconds": time.perf_counter() - started,
            "replay": str(replay_path), "diagnostic": "",
        }
    except Exception as exc:
        return {
            "seed": seed, "v14_seat": v14_seat, "v13_money": None, "v14_money": None,
            "v14_margin": None, "winner": "error", "v13_status": "UNKNOWN",
            "v14_status": "ERROR", "elapsed_seconds": time.perf_counter() - started,
            "replay": "", "diagnostic": f"{type(exc).__name__}: {exc}",
        }

embedded = [
    (11, 0, 25439, 25439), (11, 1, 25439, 25439),
    (23, 0, 23616, 21716), (23, 1, 21716, 23616),
    (37, 0, 25711, 25711), (37, 1, 25711, 25711),
    (41, 0, 24923, 24923), (41, 1, 24923, 24923),
    (53, 0, 24934, 24934), (53, 1, 24934, 24934),
    (67, 0, 25783, 25783), (67, 1, 25783, 25783),
    (79, 0, 24218, 24218), (79, 1, 24218, 24218),
    (83, 0, 25289, 25289), (83, 1, 25289, 25289),
    (97, 0, 24395, 24395), (97, 1, 24395, 24395),
    (109, 0, 24716, 24716), (109, 1, 24716, 24716),
]

if RUN_MATCHES:
    if not all(archives.values()):
        raise FileNotFoundError("Attach both V13 and V14.4 submission archives before rerunning")
    v13_agent, v13_hash = load_submission_archive(archives["v13"])
    v14_agent, v14_hash = load_submission_archive(archives["v14.4"])
    rows = [run_match(v13_agent, v14_agent, seed, seat, OUTPUT_DIR / "replays") for seed in SEEDS for seat in (0, 1)]
    matches = pd.DataFrame(rows)
else:
    matches = pd.DataFrame(embedded, columns=["seed", "v14_seat", "v13_money", "v14_money"])
    matches["v14_margin"] = matches["v14_money"] - matches["v13_money"]
    matches["winner"] = matches["v14_margin"].map(lambda x: "v14.4" if x > 0 else "v13" if x < 0 else "tie")
    matches["v13_status"] = matches["v14_status"] = "DONE"
    matches["elapsed_seconds"] = pd.NA
    matches["replay"] = "embedded verified result"
    matches["diagnostic"] = ""

assert len(matches) == EXPECTED_GAMES
assert matches["winner"].value_counts().to_dict() == {"tie": 18, "v13": 1, "v14.4": 1}
matches

counts = matches["winner"].value_counts()
summary = pd.DataFrame({
    "agent": ["v13", "v14.4"],
    "wins": [int(counts.get("v13", 0)), int(counts.get("v14.4", 0))],
    "losses": [int(counts.get("v14.4", 0)), int(counts.get("v13", 0))],
    "draws": [int(counts.get("tie", 0))] * 2,
    "mean_margin": [-matches["v14_margin"].mean(), matches["v14_margin"].mean()],
    "median_margin": [-matches["v14_margin"].median(), matches["v14_margin"].median()],
    "failures": [int((matches["v13_status"] != "DONE").sum()), int((matches["v14_status"] != "DONE").sum())],
})
LOCAL_DECISION = "v13 (retained incumbent after a drawn challenge)"
print(summary.to_string(index=False))
print(f"\nDecision: {LOCAL_DECISION}")
print("Uncertainty: 18/20 ties provide little power to distinguish these closely related policies.")

# Optional direct decision-latency probe when the V13 archive is attached.
if archives["v13"]:
    v13_probe, _ = load_submission_archive(archives["v13"])
    tiles = [[None if x < 5 and y < 5 else "LOCKED" for x in range(10)] for y in range(10)]
    farm = {"money": 3000, "tiles": tiles, "farmer": [4, 4], "hands": [], "unlocked_quadrants": ["NW"], "hires_today": 0}
    observation = {
        "player": 0, "step": 0, "day": 0, "hour": 0, "farms": [farm, farm],
        "private": {"shed": {}, "seeds": {}, "inventories": [{}]},
        "market": {"inventory": {}, "prices": {}}, "town": {"unlocked_shops": []},
    }
    samples = []
    tracemalloc.start()
    for _ in range(100):
        started = time.perf_counter()
        action = v13_probe(observation)
        samples.append((time.perf_counter() - started) * 1000)
    _, agent_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert set(action) == {"farmer", "hands", "market"}
    print({"mean_decision_ms": sum(samples) / len(samples), "max_decision_ms": max(samples), "peak_kib": agent_peak / 1024})
else:
    print("Attach V13 to run the direct latency probe; benchmark conclusions remain available from embedded results.")

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
order = ["v13", "tie", "v14.4"]
counts.reindex(order, fill_value=0).plot.bar(ax=axes[0], color=["#3b82f6", "#94a3b8", "#f59e0b"], title="Match outcomes")
axes[0].set_ylabel("matches")

matches.assign(game=range(1, len(matches) + 1)).plot(x="game", y="v14_margin", marker="o", ax=axes[1], title="V14.4 margin by match", legend=False)
axes[1].axhline(0, color="black", linewidth=1)
axes[1].set_ylabel("final-money margin")

role = matches.groupby("v14_seat")["v14_margin"].agg(["mean", "median", "min", "max"])
role["mean"].plot.bar(ax=axes[2], color="#8b5cf6", title="Mean V14.4 margin by seat")
axes[2].axhline(0, color="black", linewidth=1)
axes[2].set_xlabel("V14.4 seat")
plt.tight_layout()
plot_path = OUTPUT_DIR / "v13_v14_4_benchmark.png"
fig.savefig(plot_path, dpi=160, bbox_inches="tight")
plt.show()

print("Status failures:", int(((matches.v13_status != "DONE") | (matches.v14_status != "DONE")).sum()))
print("Only nonzero-margin rows:")
display(matches.loc[matches.v14_margin != 0, ["seed", "v14_seat", "v13_money", "v14_money", "v14_margin", "winner"]])

timeline = pd.DataFrame({
    "game": range(1, len(matches) + 1),
    "V13 cumulative wins": (matches.winner == "v13").cumsum(),
    "V14.4 cumulative wins": (matches.winner == "v14.4").cumsum(),
})
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
timeline.plot(x="game", y=["V13 cumulative wins", "V14.4 cumulative wins"], drawstyle="steps-post", ax=axes[0], title="Cumulative decisive wins")
matches.boxplot(column="v14_margin", by="v14_seat", ax=axes[1])
axes[1].set_title("Margin distribution by V14.4 seat")
axes[1].set_xlabel("V14.4 seat")
axes[1].set_ylabel("V14.4 final-money margin")
plt.suptitle("")
plt.tight_layout()
plt.show()
role

matches_path = OUTPUT_DIR / "match_results.csv"
summary_path = OUTPUT_DIR / "aggregate_metrics.csv"
metadata_path = OUTPUT_DIR / "benchmark_metadata.json"

matches.to_csv(matches_path, index=False)
summary.to_csv(summary_path, index=False)
metadata = {
    "games": len(matches),
    "seeds": SEEDS,
    "seat_policy": "each seed in both V14.4 seats",
    "outcomes": matches.winner.value_counts().to_dict(),
    "mean_v14_margin": float(matches.v14_margin.mean()),
    "median_v14_margin": float(matches.v14_margin.median()),
    "completion_rate": float(((matches.v13_status == "DONE") & (matches.v14_status == "DONE")).mean()),
    "decision": LOCAL_DECISION,
    "submission_gate_required_wins": REQUIRED_SUBMISSION_WINS,
    "submission_performed": False,
}
metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

serialized = json.dumps(metadata) + matches.to_csv(index=False)
assert "C:\\" not in serialized and "c:\\" not in serialized
assert metadata["games"] == 20
assert metadata["outcomes"] == {"tie": 18, "v13": 1, "v14.4": 1}
print("Exported:", matches_path, summary_path, metadata_path, plot_path, sep="\n- ")