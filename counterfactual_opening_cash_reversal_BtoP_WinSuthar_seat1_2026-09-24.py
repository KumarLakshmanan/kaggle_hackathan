"""Reverse only the observed B-vs-P opening cash transfer in candidate seat 1.

This is a diagnostic counterfactual, not a native score or submission. It runs
the B opening against the unchanged Win Suthar fixed tape, then replaces only
the two farms' cash immediately after step-0 market clearing with the values
observed in the matched P run. Both agents continue normally afterward.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path

from kaggle_environments.envs.kaggriculture import kaggriculture as simulator

from trace_paired_game import run


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = (
    ROOT
    / "diagnostics"
    / "counterfactual_opening_cash_reversal_BtoP_WinSuthar_seed467762674_seat1_2026-09-24.json.gz"
)
CANDIDATE_PATH = ROOT / "main_frontier_h6_opening_arm_2026-09-24.py"
OPPONENT_PATH = (
    ROOT
    / "live_leaderboard_routes_2026-09-23_ranks301-340_1ep"
    / "Win-Suthar-submission-56442820-episode-112125381-seat1.json.gz"
)
B_TRACE_PATH = (
    ROOT / "diagnostics" / "trace_BvsP_WinSuthar_seed467762674_seat1_2026-09-24.json.gz"
)
P_TRACE_PATH = (
    ROOT / "diagnostics" / "trace_PvsB_WinSuthar_seed467762674_seat1_2026-09-24.json.gz"
)
SEED = 467762674
CANDIDATE_SEAT = 1
B_QUEUE = [
    ["BUY_PRODUCT", "WHEAT", 8],
    ["SELL", "WHEAT", 8],
    ["BUY_PRODUCT", "WHEAT", 5],
    ["BUY_SEED", "WHEAT", 1],
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_gz(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as source:
        return json.load(source)


def post_opening_cash(trace: dict) -> list[float]:
    observation = trace["traces"][CANDIDATE_SEAT][1]["observation"]
    return [float(farm["money"]) for farm in observation["farms"]]


def main() -> None:
    if OUTPUT_PATH.exists():
        raise FileExistsError(f"Refusing to overwrite existing report: {OUTPUT_PATH}")
    for path in (CANDIDATE_PATH, OPPONENT_PATH, B_TRACE_PATH, P_TRACE_PATH):
        if not path.is_file():
            raise FileNotFoundError(path)

    b_trace = load_json_gz(B_TRACE_PATH)
    p_trace = load_json_gz(P_TRACE_PATH)
    expected_b_cash = post_opening_cash(b_trace)
    target_cash = post_opening_cash(p_trace)
    if expected_b_cash != [2843.0, 2865.0] or target_cash != [2860.0, 2848.0]:
        raise AssertionError(
            f"Unexpected native cash vectors: B={expected_b_cash}, P={target_cash}"
        )

    old_arm = os.environ.get("KAGG_OPENING_ARM")
    os.environ["KAGG_OPENING_ARM"] = "B"
    original_process_market = simulator._process_market
    intervention: dict = {"applied": False}

    def process_market_then_reverse_cash(state, env):
        original_process_market(state, env)
        step = int(state[0].observation.step)
        if step != 0:
            return
        farms = state[0].observation.farms
        before = [float(farms[seat]["money"]) for seat in (0, 1)]
        if before != expected_b_cash:
            raise AssertionError(
                f"B opening cash changed: expected {expected_b_cash}, got {before}"
            )
        for seat, cash in enumerate(target_cash):
            farms[seat]["money"] = cash
        intervention.update(
            applied=True,
            step=step,
            phase="immediately after step-0 market clearing",
            before_cash=before,
            target_cash=list(target_cash),
            cash_delta=[target_cash[seat] - before[seat] for seat in (0, 1)],
            changed_fields=["farms[0].money", "farms[1].money"],
        )

    simulator._process_market = process_market_then_reverse_cash
    try:
        result = run(
            str(CANDIDATE_PATH),
            "rawroute:" + str(OPPONENT_PATH),
            SEED,
            CANDIDATE_SEAT,
        )
    finally:
        simulator._process_market = original_process_market
        if old_arm is None:
            os.environ.pop("KAGG_OPENING_ARM", None)
        else:
            os.environ["KAGG_OPENING_ARM"] = old_arm

    if not intervention.get("applied"):
        raise AssertionError("Cash reversal hook did not run")
    if result["traces"][CANDIDATE_SEAT][0]["action"].get("market") != B_QUEUE:
        raise AssertionError("Expected B opening queue was not used")

    payload = {
        "purpose": "diagnostic cash-transfer reversal; excluded from native score totals",
        "engine_version": result["engine_version"],
        "simulator_source": str(Path(simulator.__file__).resolve()),
        "simulator_source_sha256": sha256(Path(simulator.__file__).resolve()),
        "candidate": str(CANDIDATE_PATH),
        "candidate_sha256": sha256(CANDIDATE_PATH),
        "opponent": str(OPPONENT_PATH),
        "opponent_sha256": sha256(OPPONENT_PATH),
        "seed": SEED,
        "candidate_seat": CANDIDATE_SEAT,
        "opening_arm": "B",
        "intervention": intervention,
        "native_comparator_trace_files": [str(B_TRACE_PATH), str(P_TRACE_PATH)],
        "result": result,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUTPUT_PATH, "wt", encoding="utf-8") as target:
        json.dump(payload, target, separators=(",", ":"))
    print(
        "INTERVENTION "
        + json.dumps(
            {
                "applied": intervention["applied"],
                "before_cash": intervention["before_cash"],
                "target_cash": intervention["target_cash"],
                "cash_delta": intervention["cash_delta"],
                "margin": result["margin"],
                "candidate_reward": result["candidate_reward"],
                "opponent_reward": result["opponent_reward"],
                "candidate_status": result["candidate_status"],
                "opponent_status": result["opponent_status"],
                "out": str(OUTPUT_PATH),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
