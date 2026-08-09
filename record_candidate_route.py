#!/usr/bin/env python3
"""Run one deterministic match and save the candidate's compact action route."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path

from kaggle_environments import make

from paired_benchmark import _load_agent, _reward, _status


PASS_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}


def _digest(actions: list[dict]) -> str:
    raw = json.dumps(actions, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--opponent", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--candidate-seat", type=int, choices=(0, 1), default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    candidate, _timing = _load_agent(args.candidate, "record_candidate")
    opponent, _opponent_timing = _load_agent(args.opponent, "record_opponent")
    agents = [candidate, opponent] if args.candidate_seat == 0 else [opponent, candidate]
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": int(args.seed)},
        debug=False,
    )
    env.run(agents)
    actions = [
        frame[args.candidate_seat].get("action") or PASS_ACTION
        for frame in env.steps[1:]
    ]
    final = env.steps[-1]
    opponent_seat = 1 - args.candidate_seat
    candidate_reward = _reward(final[args.candidate_seat])
    opponent_reward = _reward(final[opponent_seat])
    payload = {
        "metadata": {
            "seed": args.seed,
            "source_seat": args.candidate_seat,
            "candidate": args.candidate,
            "opponent": args.opponent,
            "reward": candidate_reward,
            "opponent_reward": opponent_reward,
            "margin": candidate_reward - opponent_reward,
            "statuses": [
                _status(final[args.candidate_seat]),
                _status(final[opponent_seat]),
            ],
            "action_count": len(actions),
            "action_sha256": _digest(actions),
        },
        "actions": actions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8") as text:
                json.dump(payload, text, sort_keys=True, separators=(",", ":"))
    print(json.dumps(payload["metadata"], sort_keys=True))
    print(args.output.resolve())


if __name__ == "__main__":
    main()
