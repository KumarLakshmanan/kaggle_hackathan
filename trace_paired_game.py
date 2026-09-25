"""Capture per-turn observations/actions for one exact Kaggriculture matchup.

This diagnostic harness is kept separate from paired_benchmark.py so existing
benchmark behavior and any local edits to it remain untouched.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import json
from pathlib import Path
from typing import Any

from kaggle_environments import __version__ as engine_version
from kaggle_environments import make

from paired_benchmark import _load_agent, _reward, _status, _value


def _plain(value: Any) -> Any:
    """Copy Kaggle observation/action values into JSON-friendly structures."""
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _snapshot(observation: Any) -> dict[str, Any]:
    return _plain(observation)


class TraceAgent:
    def __init__(
        self,
        delegate: Any,
        records: list[dict[str, Any]],
        cow_to_sheep_step: int | None = None,
        opening_market: list[list[Any]] | None = None,
    ):
        self.delegate = delegate
        self.records = records
        self.cow_to_sheep_step = cow_to_sheep_step
        self.opening_market = opening_market

    def __call__(self, observation: Any, configuration: Any = None) -> Any:
        action = self.delegate(observation, configuration)
        step = int(_value(observation, "step", -1))
        probe = None
        if self.opening_market is not None and step == 0 and isinstance(action, dict):
            action = dict(action, market=copy.deepcopy(self.opening_market))
            probe = "opening_market_override"
        if self.cow_to_sheep_step == step and isinstance(action, dict):
            market = [list(order) for order in (action.get("market") or [])]
            patched = False
            for order in market:
                if order[:3] == ["BUY_ANIMAL", "COW", 2]:
                    order[1] = "SHEEP"
                    patched = True
            if patched:
                action = dict(action, market=market)
                probe = "cow2_to_sheep2"
        self.records.append(
            {
                "step": step,
                "player": int(_value(observation, "player", -1)),
                "observation": _snapshot(observation),
                "action": _plain(action),
                "probe": probe,
            }
        )
        return action


def _attach_transitions(records: list[dict[str, Any]], final_state: Any) -> None:
    for index, record in enumerate(records):
        if index + 1 < len(records):
            post = records[index + 1]["observation"]
        else:
            post = _value(final_state, "observation", {}) or {}
        pre = record["observation"]
        seat = record["player"]
        before_farms = pre.get("farms", [])
        after_farms = post.get("farms", []) if isinstance(post, dict) else []
        before_farm = before_farms[seat] if seat < len(before_farms) else {}
        after_farm = after_farms[seat] if seat < len(after_farms) else {}
        before_private = pre.get("private", {}) or {}
        after_private = post.get("private", {}) or {} if isinstance(post, dict) else {}
        before_shed = before_private.get("shed", {}) or {}
        after_shed = after_private.get("shed", {}) or {}
        before_seeds = before_private.get("seeds", {}) or {}
        after_seeds = after_private.get("seeds", {}) or {}
        products = set(before_shed) | set(after_shed)
        seeds = set(before_seeds) | set(after_seeds)
        record["transition"] = {
            "cash_delta": round(
                float(after_farm.get("money", before_farm.get("money", 0)) or 0)
                - float(before_farm.get("money", 0) or 0),
                4,
            ),
            "shed_delta": {
                item: int(after_shed.get(item, 0) or 0)
                - int(before_shed.get(item, 0) or 0)
                for item in sorted(products)
                if int(after_shed.get(item, 0) or 0)
                != int(before_shed.get(item, 0) or 0)
            },
            "seed_delta": {
                item: int(after_seeds.get(item, 0) or 0)
                - int(before_seeds.get(item, 0) or 0)
                for item in sorted(seeds)
                if int(after_seeds.get(item, 0) or 0)
                != int(before_seeds.get(item, 0) or 0)
            },
        }


def run(
    candidate: str,
    opponent: str,
    seed: int,
    candidate_seat: int,
    cow_to_sheep_step: int | None = None,
    opening_market: list[list[Any]] | None = None,
) -> dict[str, Any]:
    traces: list[list[dict[str, Any]]] = [[], []]
    candidate_agent, candidate_timing = _load_agent(
        candidate, f"trace_candidate_s{seed}_p{candidate_seat}"
    )
    opponent_agent, opponent_timing = _load_agent(
        opponent, f"trace_opponent_s{seed}_p{1-candidate_seat}"
    )
    agents: list[Any] = [None, None]
    agents[candidate_seat] = TraceAgent(
        candidate_agent, traces[candidate_seat], cow_to_sheep_step, opening_market
    )
    agents[1 - candidate_seat] = TraceAgent(opponent_agent, traces[1 - candidate_seat])
    try:
        env = make(
            "kaggriculture",
            configuration={"episodeSteps": 720, "seed": int(seed)},
            debug=False,
        )
        env.run(agents)
        final = env.steps[-1]
        for seat in (0, 1):
            if traces[seat]:
                _attach_transitions(traces[seat], final[seat])
        candidate_reward = _reward(final[candidate_seat])
        opponent_reward = _reward(final[1 - candidate_seat])
        return {
            "engine_version": engine_version,
            "candidate": candidate,
            "opponent": opponent,
            "seed": seed,
            "candidate_seat": candidate_seat,
            "cow_to_sheep_step": cow_to_sheep_step,
            "opening_market": opening_market,
            "candidate_reward": candidate_reward,
            "opponent_reward": opponent_reward,
            "margin": candidate_reward - opponent_reward,
            "candidate_status": _status(final[candidate_seat]),
            "opponent_status": _status(final[1 - candidate_seat]),
            "candidate_timing": candidate_timing.timing.__dict__,
            "opponent_timing": opponent_timing.timing.__dict__,
            "traces": traces,
            "final_observations": [
                _snapshot(_value(state, "observation", {}) or {}) for state in final
            ],
        }
    finally:
        for timed in (candidate_timing, opponent_timing):
            if timed is not None and getattr(timed, "module_name", None):
                import sys

                sys.modules.pop(timed.module_name, None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--opponent", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--candidate-seat", type=int, choices=(0, 1), required=True)
    parser.add_argument(
        "--cow-to-sheep-step",
        type=int,
        help="Probe only: replace a candidate BUY_ANIMAL COW 2 at this step with SHEEP 2",
    )
    parser.add_argument(
        "--opening-market-json",
        help="Probe only: replace the candidate's turn-0 market queue with this JSON array",
    )
    parser.add_argument("--json-gz-out", type=Path, required=True)
    args = parser.parse_args()
    try:
        opening_market = (
            json.loads(args.opening_market_json)
            if args.opening_market_json is not None
            else None
        )
    except json.JSONDecodeError as exc:
        parser.error(f"Invalid --opening-market-json: {exc}")
    if opening_market is not None and (
        not isinstance(opening_market, list)
        or any(not isinstance(order, list) for order in opening_market)
    ):
        parser.error("--opening-market-json must be a JSON array of order arrays")
    payload = run(
        args.candidate,
        args.opponent,
        args.seed,
        args.candidate_seat,
        args.cow_to_sheep_step,
        opening_market,
    )
    args.json_gz_out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.json_gz_out, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"))
    print(
        f"engine={payload['engine_version']} seed={args.seed} seat={args.candidate_seat} "
        f"margin={payload['margin']:+.0f} status="
        f"{payload['candidate_status']}/{payload['opponent_status']} "
        f"calls={payload['candidate_timing']['calls']} out={args.json_gz_out}"
    )


if __name__ == "__main__":
    main()
