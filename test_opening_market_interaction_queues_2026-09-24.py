"""One-turn, per-unit opening-market interaction traces for saved tapes.

The candidate arm is varied while the counterparty's recorded step-0 market
queue, initial state, seed, and seat are held fixed. This is an execution
diagnostic only; it is not a full-game performance benchmark.
"""

from __future__ import annotations

import copy
import gzip
import hashlib
import json
from pathlib import Path

from kaggle_environments import __version__ as engine_version
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as simulator


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "diagnostics" / "opening_market_interaction_queues_2026-09-24.json"
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_opening_queue(route: dict) -> list:
    raw_path = Path(route["opponent_path"])
    raw = json.load(gzip.open(raw_path, "rt", encoding="utf-8"))
    return copy.deepcopy(raw["actions"][0].get("market", []))


def load_cases() -> list[dict]:
    panel_501 = json.loads(
        (ROOT / "diagnostics" / "mainfrontier_opening_queue_full98_2026-09-24.json").read_text(encoding="utf-8")
    )
    panel_301 = json.loads(
        (ROOT / "diagnostics" / "mainfrontier_h6_opening_B_ranks301-420_full_2026-09-24.json").read_text(encoding="utf-8")
    )
    terry = next(row for row in panel_501["rows"] if row["team"] == "Terry Luo")
    yamazaking = next(row for row in panel_301["rows"] if row["team"].lower() == "yamazaking")
    max_trace_path = ROOT / "diagnostics" / "trace_B_MaxPower_861869639_seat0_2026-09-24.json.gz"
    max_trace = json.load(gzip.open(max_trace_path, "rt", encoding="utf-8"))
    max_queue = copy.deepcopy(max_trace["traces"][1][0]["action"].get("market", []))
    return [
        {
            "name": "Terry Luo",
            "seed": int(terry["seed"]),
            "source": str(terry["opponent_path"]),
            "queue": raw_opening_queue(terry),
        },
        {
            "name": "yamazaking",
            "seed": int(yamazaking["seed"]),
            "source": str(yamazaking["opponent_path"]),
            "queue": raw_opening_queue(yamazaking),
        },
        {
            "name": "Max Power",
            "seed": int(max_trace["seed"]),
            "source": str(max_trace_path),
            "queue": max_queue,
        },
    ]


def initial_remaining(queue: list) -> list[int]:
    return [int(order[2]) if len(order) >= 3 else 1 for order in queue]


def run_one(case: dict, arm: str, candidate_seat: int) -> dict:
    env = make(
        "kaggriculture",
        configuration={"episodeSteps": 720, "seed": int(case["seed"])},
        debug=False,
    )
    state = env.reset()
    opponent_seat = 1 - candidate_seat
    observation = state[0].observation
    farms = observation.farms
    market = observation.market
    private_by_seat = [state[index].observation.private for index in (0, 1)]
    before = {
        "cash": [float(farms[index]["money"]) for index in (0, 1)],
        "wheat_shed": [int(private_by_seat[index].shed.get("WHEAT", 0)) for index in (0, 1)],
        "wheat_seed": [int(private_by_seat[index].seeds.get("WHEAT", 0)) for index in (0, 1)],
        "wheat_market_inventory": int(market.inventory["WHEAT"]),
        "wheat_market_price": int(market.prices["WHEAT"]),
    }
    queues = {candidate_seat: copy.deepcopy(ARMS[arm]), opponent_seat: copy.deepcopy(case["queue"])}
    for seat in (0, 1):
        state[seat].action = {"farmer": ["PASS"], "hands": [], "market": queues[seat]}

    remaining = {seat: initial_remaining(queues[seat]) for seat in (0, 1)}
    cursor = {0: 0, 1: 0}
    original_commit = simulator._commit_unit
    farm_to_seat = {id(farms[index]): index for index in (0, 1)}
    events: list[dict] = []

    def matching_order_index(seat: int, op: str, item: str) -> int | None:
        index = cursor[seat]
        while index < len(queues[seat]):
            order = queues[seat][index]
            if remaining[seat][index] <= 0:
                index += 1
                continue
            if order and order[0] == op and (len(order) < 2 or order[1] == item):
                cursor[seat] = index
                return index
            index += 1
        cursor[seat] = index
        return None

    def record_commit(op, item, price, farm_obj, private_obj, market_obj, shed_capacity=100):
        seat = farm_to_seat[id(farm_obj)]
        order_index = matching_order_index(seat, op, item)
        cash_before = float(farm_obj["money"])
        inventory_before = int(market_obj.inventory.get(item, 0))
        shed_before = int(private_obj.shed.get(item, 0))
        seed_before = int(private_obj.seeds.get(item, 0))
        success = original_commit(
            op, item, price, farm_obj, private_obj, market_obj, shed_capacity
        )
        if order_index is not None:
            remaining[seat][order_index] = max(0, remaining[seat][order_index] - 1)
            if remaining[seat][order_index] == 0:
                cursor[seat] = order_index + 1
        if not success:
            if order_index is not None:
                remaining[seat][order_index] = 0
                cursor[seat] = order_index + 1
            if op == "SELL" and shed_before <= 0:
                failure_reason = "no item in shed"
            elif op in ("BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL") and cash_before < price:
                failure_reason = "insufficient cash"
            elif op in ("BUY_PRODUCT", "BUY_ANIMAL") and sum(private_obj.shed.values()) >= shed_capacity:
                failure_reason = "shed full"
            else:
                failure_reason = "other engine rejection"
        else:
            failure_reason = None
        events.append(
            {
                "event_index": len(events),
                "step": int(state[0].observation.step),
                "seat": seat,
                "role": "candidate" if seat == candidate_seat else "opponent",
                "order_index": order_index,
                "op": op,
                "item": item,
                "actual_quote": int(price),
                "success": bool(success),
                "failure_reason": failure_reason,
                "cash_before": cash_before,
                "cash_after": float(farm_obj["money"]),
                "market_inventory_before_commit": inventory_before,
                "market_inventory_after_commit": int(market_obj.inventory.get(item, 0)),
                "shed_before": shed_before,
                "shed_after": int(private_obj.shed.get(item, 0)),
                "seed_before": seed_before,
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
        "cash": [float(farms[index]["money"]) for index in (0, 1)],
        "wheat_shed": [int(private_by_seat[index].shed.get("WHEAT", 0)) for index in (0, 1)],
        "wheat_seed": [int(private_by_seat[index].seeds.get("WHEAT", 0)) for index in (0, 1)],
        "wheat_market_inventory": int(market.inventory["WHEAT"]),
        "wheat_market_price": int(market.prices["WHEAT"]),
    }
    order_fills = []
    for seat in (0, 1):
        for index, order in enumerate(queues[seat]):
            expected = int(order[2]) if len(order) >= 3 else 1
            units = [event for event in events if event["seat"] == seat and event["order_index"] == index]
            order_fills.append(
                {
                    "seat": seat,
                    "role": "candidate" if seat == candidate_seat else "opponent",
                    "order_index": index,
                    "order": order,
                    "requested_units": expected,
                    "executed_units": sum(bool(event["success"]) for event in units),
                    "failed_units": sum(not event["success"] for event in units),
                }
            )
    return {
        "case": case["name"],
        "seed": int(case["seed"]),
        "source": case["source"],
        "arm": arm,
        "candidate_seat": candidate_seat,
        "candidate_queue": ARMS[arm],
        "opponent_queue": case["queue"],
        "before": before,
        "after": after,
        "cash_delta": [after["cash"][i] - before["cash"][i] for i in (0, 1)],
        "candidate_cash_delta": after["cash"][candidate_seat] - before["cash"][candidate_seat],
        "opponent_cash_delta": after["cash"][opponent_seat] - before["cash"][opponent_seat],
        "candidate_wheat_delta": after["wheat_shed"][candidate_seat] - before["wheat_shed"][candidate_seat],
        "candidate_seed_delta": after["wheat_seed"][candidate_seat] - before["wheat_seed"][candidate_seat],
        "all_units_filled": all(fill["requested_units"] == fill["executed_units"] for fill in order_fills),
        "order_fills": order_fills,
        "events": events,
    }


def main() -> None:
    if OUTPUT_PATH.exists():
        raise FileExistsError(f"Refusing to overwrite existing report: {OUTPUT_PATH}")
    cases = load_cases()
    results = [run_one(case, arm, seat) for case in cases for arm in ARMS for seat in (0, 1)]
    module_path = Path(simulator.__file__).resolve()
    payload = {
        "engine_version": engine_version,
        "simulator_source": str(module_path),
        "simulator_source_sha256": sha256(module_path),
        "scope": "opening market clearing only; no farm actions, town consumption, end-of-day refresh, or score",
        "candidate_arms": ARMS,
        "cases": [{"name": case["name"], "seed": case["seed"], "source": case["source"], "opponent_queue": case["queue"]} for case in cases],
        "results": results,
        "all_units_filled": all(result["all_units_filled"] for result in results),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    for result in results:
        print(
            f"{result['case']} arm={result['arm']} seat={result['candidate_seat']} "
            f"candidate_cash={result['candidate_cash_delta']:+.0f} "
            f"opponent_cash={result['opponent_cash_delta']:+.0f} "
            f"cand_wheat={result['candidate_wheat_delta']:+d} "
            f"cand_seed={result['candidate_seed_delta']:+d} "
            f"market={result['before']['wheat_market_inventory']}->{result['after']['wheat_market_inventory']} "
            f"fills={result['all_units_filled']}"
        )
    print("SUMMARY " + json.dumps({"runs": len(results), "all_units_filled": payload["all_units_filled"]}))
    print(f"wrote={OUTPUT_PATH}")
    if not payload["all_units_filled"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
