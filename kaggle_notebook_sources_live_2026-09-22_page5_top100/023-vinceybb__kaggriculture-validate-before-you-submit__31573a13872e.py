from __future__ import annotations

import subprocess
import sys
from importlib.metadata import version

REQUIRED_ENGINE_VERSION = "1.32.7"
installed_engine_version = version("kaggle-environments")
if installed_engine_version != REQUIRED_ENGINE_VERSION:
    print(
        f"Installing kaggle-environments=={REQUIRED_ENGINE_VERSION}; "
        f"base image has {installed_engine_version}"
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            f"kaggle-environments=={REQUIRED_ENGINE_VERSION}",
        ],
        check=True,
    )

import ast
import gzip
import hashlib
import importlib.util
import io
import json
import os
import statistics
import tarfile
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from kaggle_environments import make

EXPECTED_MAIN_SHA256 = "69f06a802b62aa08f28705dab5728eb924bb6a7c23ffe0164f65b104cc3dadf3"
EXPECTED_ARCHIVE_SHA256 = "fb821a9f9867cd413e40323e1e79f1014b74eac7aab3db2bcdbfc6eea5e36a10"
UPSTREAM = "kaitofukami/103-128-fresh-public-v43-sparse-shop-hybrid"
SEEDS = [111, 222, 333]
BANNED_IMPORT_ROOTS = {"ftplib", "http", "requests", "socket", "subprocess", "urllib"}

engine_version = version("kaggle-environments")
assert engine_version == REQUIRED_ENGINE_VERSION, (
    f"Expected kaggle-environments {REQUIRED_ENGINE_VERSION}, got {engine_version}"
)
print("kaggle-environments:", engine_version)
print("fresh validation seeds:", SEEDS)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


override = os.environ.get("KAGGRICULTURE_AGENT_SOURCE")
candidates = [Path(override)] if override else []
kaggle_input = Path("/kaggle/input")
if kaggle_input.exists():
    candidates.extend(kaggle_input.rglob("main.py"))

matching = [path for path in candidates if path.is_file() and sha256_path(path) == EXPECTED_MAIN_SHA256]
if len(matching) != 1:
    raise RuntimeError(
        f"Expected exactly one upstream main.py with SHA {EXPECTED_MAIN_SHA256}; "
        f"found {len(matching)}"
    )

upstream_main = matching[0]
agent_bytes = upstream_main.read_bytes()
assert len(agent_bytes) == 63_309
compile(agent_bytes, "main.py", "exec")
Path("main.py").write_bytes(agent_bytes)

print("upstream:", UPSTREAM)
print("resolved path:", upstream_main)
print("main.py bytes:", len(agent_bytes))
print("main.py SHA-256:", sha256_path(Path("main.py")))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def imported_roots(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


smoke_module = load_module(Path("main.py"), "artifact_audit")
if not callable(getattr(smoke_module, "agent", None)):
    raise RuntimeError("main.py does not expose a callable agent")

source_groups = {"main.py": agent_bytes.decode("utf-8")}
source_groups.update(getattr(smoke_module, "_V43_MODULES", {}))
import_roots = {name: sorted(imported_roots(source)) for name, source in source_groups.items()}
banned = {
    name: sorted(set(roots) & BANNED_IMPORT_ROOTS)
    for name, roots in import_roots.items()
    if set(roots) & BANNED_IMPORT_ROOTS
}
assert not banned, f"Forbidden direct imports: {banned}"

with Path("submission.tar.gz").open("wb") as raw:
    with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode="w") as archive:
            info = tarfile.TarInfo("main.py")
            info.size = len(agent_bytes)
            info.mode = 0o644
            info.mtime = 0
            archive.addfile(info, io.BytesIO(agent_bytes))

with tarfile.open("submission.tar.gz", "r:gz") as archive:
    members = archive.getmembers()
    assert [member.name for member in members] == ["main.py"]
    assert members[0].isfile() and not members[0].issym() and not members[0].islnk()

archive_sha = sha256_path(Path("submission.tar.gz"))
assert archive_sha == EXPECTED_ARCHIVE_SHA256
print("audited source groups:", len(source_groups))
print("forbidden direct imports: none")
print("submission.tar.gz SHA-256:", archive_sha)


def fresh_agent(tag: str):
    module = load_module(Path("main.py"), f"candidate_{tag}_{time.time_ns()}")
    return module.agent


def run_game(seed: int, opponent: str, candidate_seat: int) -> dict[str, Any]:
    if opponent == "self":
        agents = [fresh_agent(f"self_left_{seed}"), fresh_agent(f"self_right_{seed}")]
        candidate_seat = 0
    else:
        candidate = fresh_agent(f"starter_{seed}_{candidate_seat}")
        agents = [candidate, opponent] if candidate_seat == 0 else [opponent, candidate]

    started = time.perf_counter()
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": seed},
        debug=False,
    )
    env.run(agents)
    elapsed = time.perf_counter() - started
    final = env.steps[-1]
    statuses = [str(state.status) for state in final]
    rewards = [None if state.reward is None else float(state.reward) for state in final]
    assert statuses == ["DONE", "DONE"], (seed, opponent, candidate_seat, statuses)
    assert None not in rewards
    candidate_reward = rewards[candidate_seat]
    other_reward = rewards[1 - candidate_seat]
    return {
        "seed": seed,
        "opponent": opponent,
        "candidate_seat": candidate_seat,
        "candidate_reward": candidate_reward,
        "other_reward": other_reward,
        "candidate_margin": candidate_reward - other_reward,
        "statuses": statuses,
        "elapsed_seconds": round(elapsed, 3),
    }


games = []
for seed in SEEDS:
    games.append(run_game(seed, "self", 0))
    games.append(run_game(seed, "starter", 0))
    games.append(run_game(seed, "starter", 1))

results = pd.DataFrame(games)
starter = results[results["opponent"] == "starter"]
summary = {
    "games": int(len(results)),
    "all_done": bool(results["statuses"].map(lambda value: value == ["DONE", "DONE"]).all()),
    "starter_wins": int((starter["candidate_margin"] > 0).sum()),
    "starter_games": int(len(starter)),
    "mean_starter_margin": float(starter["candidate_margin"].mean()),
    "median_starter_margin": float(starter["candidate_margin"].median()),
    "max_game_seconds": float(results["elapsed_seconds"].max()),
}
display(results)
print(json.dumps(summary, indent=2))


plot_data = starter.copy()
plot_data["seed_and_seat"] = plot_data.apply(
    lambda row: f"{int(row.seed)} · seat {int(row.candidate_seat)}", axis=1
)
colors = ["#2E7D32" if margin > 0 else "#C62828" for margin in plot_data["candidate_margin"]]

fig, ax = plt.subplots(figsize=(10, 4.5))
ax.bar(plot_data["seed_and_seat"], plot_data["candidate_margin"], color=colors)
ax.axhline(0, color="#333333", linewidth=1)
ax.set_title("Fresh-seed margin versus starter, from both seats")
ax.set_ylabel("candidate reward − starter reward")
ax.set_xlabel("seed · candidate seat")
ax.tick_params(axis="x", rotation=25)
ax.grid(axis="y", alpha=0.2)
plt.tight_layout()
plt.show()


report = {
    "competition": "kaggriculture",
    "engine_version": engine_version,
    "upstream": UPSTREAM,
    "main_sha256": EXPECTED_MAIN_SHA256,
    "archive_sha256": archive_sha,
    "seeds": SEEDS,
    "paired_seats": True,
    "summary": summary,
    "games": games,
    "source_audit": {
        "source_groups": len(source_groups),
        "banned_direct_imports": banned,
    },
    "evidence_boundary": (
        "Self-play and starter games validate execution and packaging only; "
        "they do not establish leaderboard strength."
    ),
}
Path("validation_report.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print("Wrote submission.tar.gz and validation_report.json")
