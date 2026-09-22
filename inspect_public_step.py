"""Print one candidate's compact live observation at a selected step."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from kaggle_environments import make

from paired_benchmark import _load_agent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--step", type=int, default=88)
    args = parser.parse_args()
    entries = json.loads(args.summary.read_text(encoding="utf-8"))
    by_seed = {}
    for entry in entries:
        by_seed.setdefault(int(entry["seed"]), entry)

    for seed in args.seeds:
        entry = by_seed[seed]
        route_path = Path(entry["path"]).resolve()
        with gzip.open(route_path, "rt", encoding="utf-8") as handle:
            actions = json.load(handle)["actions"]
        candidate, _ = _load_agent(args.candidate, f"inspect_{seed}")
        opponent, _ = _load_agent(f"rawroute:{route_path}", f"inspect_opp_{seed}")
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        print("CONFIG", seed, getattr(env, "configuration", None), flush=True)
        env.run([candidate, opponent])
        for frame in env.steps:
            state = frame[0]
            obs = state.get("observation", {})
            if int(obs.get("step", -1) or -1) == args.step:
                market = obs.get("market", {}) or {}
                print(
                    json.dumps(
                        {
                            "seed": seed,
                            "step": args.step,
                            "shops": (obs.get("town", {}) or {}).get("unlocked_shops", []),
                            "market_inventory": market.get("inventory", {}),
                            "market_prices": market.get("prices", {}),
                            "farm_sha256": hashlib.sha256(
                                json.dumps(obs.get("farms", []), sort_keys=True).encode()
                            ).hexdigest(),
                        },
                        separators=(",", ":"),
                    )
                )
                break


if __name__ == "__main__":
    main()
