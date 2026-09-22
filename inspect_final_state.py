"""Compact final-state/action diagnostic for a selected replay."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from kaggle_environments import make

from paired_benchmark import _load_agent


def _compact(value):
    if isinstance(value, dict):
        return {key: _compact(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_compact(child) for child in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    args = parser.parse_args()
    entries = json.loads(args.summary.read_text(encoding="utf-8"))
    by_seed = {}
    for entry in entries:
        by_seed.setdefault(int(entry["seed"]), entry)

    for seed in args.seeds:
        entry = by_seed[seed]
        route_path = Path(entry["path"]).resolve()
        candidate, _ = _load_agent(args.candidate, f"final_{seed}")
        opponent, _ = _load_agent(f"rawroute:{route_path}", f"final_opp_{seed}")
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        env.run([candidate, opponent])
        final = env.steps[-1]
        out = {"seed": seed, "team": entry["team"], "states": []}
        for seat, state in enumerate(final):
            obs = state.get("observation", {})
            farm = (obs.get("farms", []) or [{}])[seat]
            private = obs.get("private", {}) or {}
            out["states"].append(
                {
                    "seat": seat,
                    "reward": state.get("reward"),
                    "money": farm.get("money"),
                    "shed": private.get("shed", {}),
                    "inventories": private.get("inventories", []),
                    "action": state.get("action"),
                    "shops": (obs.get("town", {}) or {}).get("unlocked_shops", []),
                    "prices": (obs.get("market", {}) or {}).get("prices", {}),
                }
            )
        print(json.dumps(out, separators=(",", ":"), default=str), flush=True)


if __name__ == "__main__":
    main()
