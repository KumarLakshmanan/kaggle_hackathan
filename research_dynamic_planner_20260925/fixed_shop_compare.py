"""Causal diagnostic: compare agents under an identical observed shop sequence.

The sequence comes from a prior native run and is used only by this local
simulator harness, never by an agent. Native game results remain authoritative.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from kaggle_environments.envs.kaggriculture import kaggriculture as engine
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paired_benchmark import run_game


def compare(agents, opponent, seed, schedule, out):
    shops_by_day = {int(row["day"]): list(row["shops"]) for row in schedule}
    original = engine._end_of_day
    changed_days = []

    def fixed(state, env, day):
        result = original(state, env, day)
        next_day = day+1
        if next_day in shops_by_day:
            town = state[0].observation.town
            if list(town["unlocked_shops"]) != shops_by_day[next_day]:
                changed_days.append(next_day)
            town["unlocked_shops"] = list(shops_by_day[next_day])
        return result

    engine._end_of_day = fixed
    try:
        rows = []
        for agent in agents:
            for seat in (0, 1):
                row = run_game(agent, opponent, seed, seat, False, None, {})
                rows.append(row)
                print(agent, seat, row["candidate_reward"], row["opponent_reward"], row["margin"])
    finally:
        engine._end_of_day = original
    payload = {"seed": seed, "source": "native audit's observed shop schedule",
               "shops": shops_by_day, "forced_overrides": changed_days, "rows": rows}
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", nargs="+", required=True)
    parser.add_argument("--opponent", default="main.py")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--schedule-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    compare(args.candidate, args.opponent, args.seed,
            json.loads(args.schedule_audit.read_text(encoding="utf-8"))["daily"], args.output)
