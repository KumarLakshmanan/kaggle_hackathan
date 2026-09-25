"""Exact one-turn market invariant for opening wheat queue permutations.

The counterparty submits no market orders. This diagnostic checks transaction
execution only; its results are not candidate-vs-opponent game scores.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from kaggle_environments import __version__ as engine_version
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as simulator


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "diagnostics" / "opening_market_no_trade_invariant_v2_2026-09-24.json"
SEED = 154853
ARMS = {
    "A": [
        ["BUY_PRODUCT", "WHEAT", 20],
        ["SELL", "WHEAT", 15],
        ["BUY_SEED", "WHEAT", 1],
    ],
    "B": [
        ["BUY_PRODUCT", "WHEAT", 8],
        ["SELL", "WHEAT", 8],
        ["BUY_PRODUCT", "WHEAT", 5],
        ["BUY_SEED", "WHEAT", 1],
    ],
    "P": [
        ["BUY_PRODUCT", "WHEAT", 8],
        ["BUY_PRODUCT", "WHEAT", 5],
        ["SELL", "WHEAT", 8],
        ["BUY_SEED", "WHEAT", 1],
    ],
    "D": [
        ["BUY_PRODUCT", "WHEAT", 13],
        ["SELL", "WHEAT", 8],
        ["BUY_SEED", "WHEAT", 1],
    ],
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_one(arm: str, candidate_seat: int) -> dict:
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": SEED},
        debug=False,
    )
    state = env.reset()
    player = candidate_seat
    opponent = 1 - player
    observation = state[0].observation
    farm = observation.farms[player]
    private = state[player].observation.private
    market = observation.market
    before = {
        "cash": float(farm["money"]),
        "wheat_shed": int(private.shed.get("WHEAT", 0)),
        "wheat_seed": int(private.seeds.get("WHEAT", 0)),
        "wheat_market_inventory": int(market.inventory["WHEAT"]),
        "wheat_market_price": int(market.prices["WHEAT"]),
    }
    state[player].action = {"farmer": ["PASS"], "hands": [], "market": copy.deepcopy(ARMS[arm])}
    state[opponent].action = {"farmer": ["PASS"], "hands": [], "market": []}

    original_commit = simulator._commit_unit
    farm_seats = {id(observation.farms[index]): index for index in (0, 1)}
    events: list[dict] = []

    def record_commit(op, item, price, farm_obj, private_obj, market_obj, shed_capacity=100):
        seat = farm_seats[id(farm_obj)]
        pre_cash = float(farm_obj["money"])
        pre_inventory = int(market_obj.inventory.get(item, 0))
        pre_shed = int(private_obj.shed.get(item, 0))
        pre_seed = int(private_obj.seeds.get(item, 0))
        success = original_commit(
            op, item, price, farm_obj, private_obj, market_obj, shed_capacity
        )
        events.append(
            {
                "seat": seat,
                "op": op,
                "item": item,
                "price": int(price),
                "success": bool(success),
                "cash_before": pre_cash,
                "cash_after": float(farm_obj["money"]),
                "market_inventory_before": pre_inventory,
                "market_inventory_after": int(market_obj.inventory.get(item, 0)),
                "shed_before": pre_shed,
                "shed_after": int(private_obj.shed.get(item, 0)),
                "seed_before": pre_seed,
                "seed_after": int(private_obj.seeds.get(item, 0)),
            }
        )
        return success

    simulator._commit_unit = record_commit
    try:
        simulator._process_market(state, env)
    finally:
        simulator._commit_unit = original_commit

    after = {
        "cash": float(farm["money"]),
        "wheat_shed": int(private.shed.get("WHEAT", 0)),
        "wheat_seed": int(private.seeds.get("WHEAT", 0)),
        "wheat_market_inventory": int(market.inventory["WHEAT"]),
        "wheat_market_price": int(market.prices["WHEAT"]),
    }
    price_params = market.get("params")
    expected_buy_cost = sum(
        simulator.market_price("WHEAT", before["wheat_market_inventory"] - unit, price_params)
        for unit in range(1, 6)
    )
    seed_cost = int(simulator.CROPS["WHEAT"]["seed"])
    expected_cash_delta = -float(expected_buy_cost + seed_cost)
    result = {
        "arm": arm,
        "candidate_seat": player,
        "queue": ARMS[arm],
        "counterparty_market_queue": [],
        "before": before,
        "after": after,
        "cash_delta": after["cash"] - before["cash"],
        "expected_cash_delta": expected_cash_delta,
        "opponent_cash_delta": float(state[opponent].observation.farms[opponent]["money"]) - 3000.0,
        "events": events,
    }
    result["invariants"] = {
        "all_market_units_filled": all(event["success"] for event in events),
        "net_wheat_plus_5": after["wheat_shed"] - before["wheat_shed"] == 5,
        "one_seed_added": after["wheat_seed"] - before["wheat_seed"] == 1,
        "market_inventory_minus_5": after["wheat_market_inventory"] - before["wheat_market_inventory"] == -5,
        "cash_path_independent_endpoint": result["cash_delta"] == expected_cash_delta,
        "opponent_unchanged": result["opponent_cash_delta"] == 0.0,
    }
    result["passed"] = all(result["invariants"].values())
    return result


def main() -> None:
    if OUTPUT_PATH.exists():
        raise FileExistsError(f"Refusing to overwrite existing report: {OUTPUT_PATH}")
    module_path = Path(simulator.__file__).resolve()
    results = [run_one(arm, seat) for arm in ARMS for seat in (0, 1)]
    payload = {
        "engine_version": engine_version,
        "simulator_source": str(module_path),
        "simulator_source_sha256": file_sha256(module_path),
        "seed": SEED,
        "scope": "single initial market-clearing turn; not a full-game score",
        "results": results,
        "all_passed": all(result["passed"] for result in results),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    for result in results:
        print(
            f"arm={result['arm']} seat={result['candidate_seat']} "
            f"cash_delta={result['cash_delta']:.0f} "
            f"wheat={result['after']['wheat_shed']-result['before']['wheat_shed']:+d} "
            f"seed={result['after']['wheat_seed']-result['before']['wheat_seed']:+d} "
            f"market={result['after']['wheat_market_inventory']-result['before']['wheat_market_inventory']:+d} "
            f"passed={result['passed']}"
        )
    print("SUMMARY " + json.dumps({"all_passed": payload["all_passed"], "runs": len(results)}))
    print(f"wrote={OUTPUT_PATH}")
    if not payload["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
