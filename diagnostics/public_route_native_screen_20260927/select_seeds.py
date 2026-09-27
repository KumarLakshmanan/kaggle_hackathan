"""Outcome-blind original-shop seed selection for public-route test."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
MAIN_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
START = 2628000
MAX_SCANNED = 1024
NEEDED = 8
TARGET = ["YARN_STORE", "YARN_STORE"]


def first_shops(seed: int) -> dict:
    from kaggle_environments import make

    name = f"double_yarn_select_{seed}"
    spec = importlib.util.spec_from_file_location(name, MAIN)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.reset()
        for step in range(145):
            actions = []
            for player in env.state:
                observation = dict(player.observation)
                observation.setdefault("step", step)
                actions.append(module.agent(observation, dict(env.configuration)))
            env.step(actions)
        shops = [list(player.observation["town"]["unlocked_shops"])[:2]
                 for player in env.state]
        assert shops[0] == shops[1]
        return {"seed": seed, "shops": shops[0]}
    finally:
        sys.modules.pop(name, None)


def main() -> None:
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == MAIN_HASH
    previous_path = HERE / "seed_selection.json"
    if previous_path.exists():
        previous = json.loads(previous_path.read_text(encoding="utf8"))
        assert previous["main_sha256"] == MAIN_HASH
        scanned = list(previous["scanned"])
        assert [row["seed"] for row in scanned] == list(range(START, START + len(scanned)))
        assert len(scanned) <= MAX_SCANNED
    else:
        scanned = []
    selected = [row["seed"] for row in scanned if row["shops"] == TARGET][:NEEDED]
    with ProcessPoolExecutor(max_workers=6) as pool:
        for start in range(START + len(scanned), START + MAX_SCANNED, 64):
            rows = list(pool.map(first_shops, range(start, min(start + 64, START + MAX_SCANNED))))
            scanned.extend(rows)
            selected = [row["seed"] for row in scanned if row["shops"] == TARGET][:NEEDED]
            print(f"scanned {len(scanned)}, found {len(selected)} double-Yarn seeds", flush=True)
            (HERE / "seed_selection_partial.json").write_text(
                json.dumps({"main_sha256": MAIN_HASH, "scanned": scanned,
                            "selected_so_far": selected}, indent=2), encoding="utf8")
            if len(selected) == NEEDED:
                break
    result = {"main_sha256": MAIN_HASH, "start_seed": START,
              "max_scanned": MAX_SCANNED, "target": TARGET,
              "selected": selected, "scanned": scanned}
    (HERE / "seed_selection.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    assert len(selected) == NEEDED, f"Only {len(selected)} selected after {len(scanned)} scans"
    print("selected", selected, flush=True)


if __name__ == "__main__":
    main()
