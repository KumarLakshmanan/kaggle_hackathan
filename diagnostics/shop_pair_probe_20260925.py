"""Replay only the first six days to identify *observed* public shop pairs.

This stratifies local tests; it is never imported by the competition agent.
The opponent uses its recorded actions, while main.py responds normally.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import json
from pathlib import Path
import sys

from kaggle_environments import make

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paired_benchmark import _load_file_agent


def probe(route: dict, seat: int, index: int) -> dict:
    path = Path(route["path"])
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        actions = json.load(handle)["actions"]
    if len(actions) != 719:
        raise ValueError(f"Expected 719 actions: {path}")
    candidate = _load_file_agent(Path(__file__).resolve().parents[1] / "main.py",
                                 f"shop_probe_{index}_{seat}")
    try:
        env = make("kaggriculture", configuration={"episodeSteps": 720,
                                                   "seed": int(route["seed"])}, debug=False)
        state = env.reset(2)
        for step in range(144):
            moves = [None, None]
            observation = dict(state[seat].observation)
            observation.setdefault("step", step)
            moves[seat] = candidate(observation, env.configuration)
            moves[1 - seat] = copy.deepcopy(actions[step])
            state = env.step(moves)
        shops = list(state[seat].observation["town"]["unlocked_shops"][:2])
        if len(shops) != 2:
            raise RuntimeError(f"Did not reveal two shops: {path}")
        return {"team": route["team"], "episode_id": route["episode_id"],
                "seed": route["seed"], "action_sha256": route["action_sha256"],
                "seat": seat, "shops": shops}
    finally:
        if candidate.module_name:
            sys.modules.pop(candidate.module_name, None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    routes = json.loads(args.summary.read_text(encoding="utf-8"))
    if args.limit:
        routes = routes[:args.limit]
    result = []
    for index, route in enumerate(routes, 1):
        for seat in (0, 1):
            row = probe(route, seat, index)
            result.append(row)
            if row["shops"] == ["ICE_CREAM_SHOP", "YARN_STORE"]:
                print(index, row["team"], row["episode_id"], seat,
                      row["seed"], row["shops"], flush=True)
        if index % 10 == 0:
            print("probed", index, "of", len(routes), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("wrote", args.output, "rows", len(result), flush=True)


if __name__ == "__main__":
    main()
