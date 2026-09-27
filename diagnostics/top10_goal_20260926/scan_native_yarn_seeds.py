"""Preselect native seeds with a public YARN_STORE by the day-6 decision."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from kaggle_environments import make


ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "main.py"
OUT = Path(__file__).resolve().parent / "native_yarn_seeds.json"
START_SEED = 2609000
MAX_SCANNED = 100
NEEDED = 8


def load_agent(seed: int):
    name = f"native_yarn_scan_{seed}"
    spec = importlib.util.spec_from_file_location(name, MAIN)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def first_shops(seed: int) -> list[str]:
    module = load_agent(seed)
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
        env.reset()
        for step in range(145):
            actions = []
            for player in env.state:
                observation = dict(player.observation)
                observation.setdefault("step", step)
                actions.append(module.agent(observation, dict(env.configuration)))
            env.step(actions)
        shops = [list(s.observation["town"]["unlocked_shops"])[:2] for s in env.state]
        assert shops[0] == shops[1], (seed, shops)
        return shops[0]
    finally:
        sys.modules.pop(module.__name__, None)


def main() -> None:
    selected = []
    scanned = []
    for seed in range(START_SEED, START_SEED + MAX_SCANNED):
        shops = first_shops(seed)
        scanned.append({"seed": seed, "shops": shops})
        if "YARN_STORE" in shops:
            selected.append(seed)
            print(f"selected {seed}: {shops}", flush=True)
            if len(selected) == NEEDED:
                break
    payload = {"main_sha256": hashlib.sha256(MAIN.read_bytes()).hexdigest(),
               "start_seed": START_SEED, "selected": selected, "scanned": scanned}
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if len(selected) != NEEDED:
        raise RuntimeError(f"Found only {len(selected)} yarn seeds among {len(scanned)}")
    print(f"wrote {OUT} after {len(scanned)} seeds")


if __name__ == "__main__":
    main()
