"""Read-only audit of cb76 shed projection against its embedded native worker transition."""
from __future__ import annotations

import collections
import copy
import gzip
import hashlib
import importlib.util
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
DIAG = ROOT / "diagnostics" / "fresh90_improvement_20260929"
TRACE_DIR = DIAG / "cb76_top20_jobs_traces"
RESULTS = DIAG / "cb76_top20_jobs_results.jsonl"
SOURCE = ROOT / "main_candidate_minimal_repair_20260929_cb76fbc4.py"
EXPECTED_SHA256 = "cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74"
CFG = {
    "boardSize": 10,
    "turnsPerDay": 24,
    "shedCapacity": 100,
    "maxMarketOrdersPerTurn": 10,
    "farmHandCostMult": 1,
}


def load_candidate():
    actual = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if actual != EXPECTED_SHA256:
        raise RuntimeError(f"source hash mismatch: expected {EXPECTED_SHA256}, got {actual}")
    spec = importlib.util.spec_from_file_location("cb76_queue_stock_audit", SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, actual


def valid_traces():
    rows = [json.loads(line) for line in RESULTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    accepted, rejected = [], []
    for row in rows:
        path = TRACE_DIR / pathlib.Path(row["trace_path"]).name
        try:
            if row.get("candidate_status") != "DONE" or row.get("opponent_status") != "DONE":
                raise ValueError("result row not DONE on both sides")
            if row.get("frames") != 720:
                raise ValueError(f"unexpected frame count {row.get('frames')}")
            # Exhausting gzip validates the trailer/CRC as well as every JSON line.
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                lines = stream.readlines()
            if len(lines) != 719 or not lines[-1].endswith("\n"):
                raise ValueError(f"expected 719 newline-terminated decisions, got {len(lines)}")
            records = [json.loads(line) for line in lines]
            if [record["step"] for record in records] != list(range(719)):
                raise ValueError("decision steps are not 0..718")
            accepted.append((row, path, records))
        except Exception as exc:  # preserve every rejected job and reason in report
            rejected.append((row.get("job_id"), str(exc)))
    return rows, accepted, rejected


def native_shed(module, obs, action):
    """Apply all final worker actions with the exact executable worker transition."""
    player = int(obs["player"])
    farm = copy.deepcopy(obs["farms"][player])
    private = copy.deepcopy(obs["private"])
    core_apply = module._PLANT_CORE["_apply_unit_action"]
    day = int(obs["step"]) // CFG["turnsPerDay"]
    units = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
    for index, unit in enumerate(units):
        core_apply(farm, private, index, unit, CFG["boardSize"], day,
                   CFG["turnsPerDay"], CFG["shedCapacity"])
    return private["shed"]


def market_projection(module, obs, orders, stock, rival_orders):
    """Call the policy's exact native market engine with a supplied shed forecast."""
    player = int(obs["player"])
    farms = copy.deepcopy(obs["farms"])
    market = copy.deepcopy(obs["market"])
    private = obs["private"]
    privates = [
        {"shed": dict(stock), "seeds": dict(private["seeds"]),
         "inventories": [{} for _ in range(len(farm["hands"]) + 1)]}
        for farm in farms
    ]

    class Box:
        def __init__(self, **values):
            self.__dict__.update(values)

    states = [
        Box(action={"market": orders if i == player else rival_orders},
            observation=Box(farms=farms, market=market, private=privates[i]))
        for i in range(2)
    ]
    module._QUEUE_ENGINE["_process_market"](states, Box(configuration=CFG))
    own = farms[player]
    rival = farms[1 - player]
    return {
        "own_cash": own["money"],
        "rival_cash": rival["money"],
        "margin": own["money"] - rival["money"],
        "own_shed": dict(sorted(privates[player]["shed"].items())),
        "own_seeds": dict(sorted(privates[player]["seeds"].items())),
        "market_inventory": dict(sorted(market["inventory"].items())),
    }


def differs(a, b):
    return {key: (a.get(key, 0), b.get(key, 0))
            for key in set(a) | set(b) if a.get(key, 0) != b.get(key, 0)}


def audit():
    module, source_sha = load_candidate()
    result_rows, traces, rejected = valid_traces()
    counts = collections.Counter()
    mismatch_items = collections.Counter()
    mismatch_causes = collections.Counter()
    shed_action_units = collections.Counter()
    animal_place_audit = collections.Counter()
    examples = []
    market_changes = []
    unique_decision_keys = set()

    for result, path, records in traces:
        for record in records:
            obs, action = record["observation"], record["action"]
            player = int(obs["player"])
            farm_obs = obs["farms"][player]
            positions = [farm_obs["farmer"], *farm_obs["hands"]]
            units = [action.get("farmer", ["PASS"]), *action.get("hands", [])]

            # Native _apply_unit_action changes shed stock only through PICKUP,
            # DROP, and shed-fallback PLACE on one of the four access tiles.
            # Avoid cloning farm state when no such action can affect the shed.
            relevant = [
                (index, pos, unit)
                for index, (pos, unit) in enumerate(zip(positions, units))
                if pos[0] in (4, 5) and pos[1] in (4, 5)
                and unit and unit[0] in ("PICKUP", "DROP", "PLACE")
            ]
            if not relevant:
                counts["decision_turns_no_shed_action"] += 1
                continue

            counts["decision_turns_with_shed_action"] += 1
            for index, pos, unit in relevant:
                item = str(unit[1]) if len(unit) > 1 else ""
                shed_action_units[(unit[0], item)] += 1
                if unit[0] == "PLACE" and item in module._QUEUE_ENGINE["ANIMALS"]:
                    animal_place_audit["animal_place_at_shed_access"] += 1
                    tile = farm_obs["tiles"][pos[1]][pos[0]]
                    inventory = obs["private"]["inventories"][index].get(item, 0)
                    structure = module._QUEUE_ENGINE["ANIMALS"][item]["structure"]
                    matching_empty = (isinstance(tile, dict)
                                      and tile.get("kind") == structure
                                      and "animal" not in tile)
                    if inventory > 0:
                        animal_place_audit["animal_place_with_inventory"] += 1
                    if matching_empty:
                        animal_place_audit["matching_empty_structure"] += 1
                    else:
                        animal_place_audit["falls_through_to_shed_path"] += 1
                    room = max(0, CFG["shedCapacity"] - sum(obs["private"]["shed"].values()))
                    requested = int(unit[2]) if len(unit) > 2 else 1
                    if not matching_empty and inventory > 0 and room > 0 and requested > 0:
                        animal_place_audit["realized_fallback_drop_eligible"] += 1
            old_stock = module._queue_stock(obs, action, CFG)
            exact_stock = native_shed(module, obs, action)
            stock_diff = differs(old_stock, exact_stock)
            unique_decision_keys.add((result["episode_id"], record["step"]))
            if not stock_diff:
                counts["shed_action_turns_projection_match"] += 1
                continue

            counts["mismatch_turns"] += 1
            counts["mismatch_items"] += len(stock_diff)
            market_orders = action.get("market", [])
            if market_orders:
                counts["mismatches_with_market_orders"] += 1
            item_causes = []
            for item, (forecast, exact) in stock_diff.items():
                mismatch_items[(item, exact - forecast)] += 1
                if item in module._QUEUE_ENGINE.get("ANIMALS", {}):
                    item_causes.append("animal-stock")
                else:
                    item_causes.append("product-stock")
            cause_actions = tuple((unit[0], str(unit[1]) if len(unit) > 1 else "")
                                  for _, _, unit in relevant)
            mismatch_causes[(tuple(sorted(item_causes)), cause_actions)] += 1

            report = {
                "rank": result["rank"],
                "episode_id": result["episode_id"],
                "seat": result["candidate_seat"],
                "step": record["step"],
                "stock_diff": stock_diff,
                "relevant_actions": relevant,
                "market_orders": market_orders,
            }
            if len(examples) < 80:
                examples.append(report)

            if market_orders:
                for scenario, rival_orders in (("idle-empty", []),
                                               ("mirror-own-orders", market_orders)):
                    old_projection = market_projection(module, obs, market_orders,
                                                       old_stock, rival_orders)
                    exact_projection = market_projection(module, obs, market_orders,
                                                         exact_stock, rival_orders)
                    changes = {key: (old_projection[key], exact_projection[key])
                               for key in old_projection
                               if old_projection[key] != exact_projection[key]}
                    if changes:
                        counts["market_scenarios_changed"] += 1
                        if old_projection["own_cash"] != exact_projection["own_cash"]:
                            counts["changed_own_cash_scenarios"] += 1
                        if old_projection["margin"] != exact_projection["margin"]:
                            counts["changed_margin_scenarios"] += 1
                        market_changes.append({**report, "scenario": scenario,
                                               "changes": changes,
                                               "old_projection": old_projection,
                                               "exact_projection": exact_projection})
                    else:
                        counts["market_scenarios_unchanged"] += 1

    return {
        "source_sha256": source_sha,
        "result_rows": len(result_rows),
        "accepted_trace_count": len(traces),
        "rejected": rejected,
        "frames_per_trace": 719,
        "total_decision_frames": len(traces) * 719,
        "unique_episode_step_keys_seen_with_shed_action": len(unique_decision_keys),
        "counts": dict(counts),
        "shed_action_units": [(key, count) for key, count in shed_action_units.most_common()],
        "animal_place_audit": dict(animal_place_audit),
        "mismatch_items": [(key, count) for key, count in mismatch_items.most_common()],
        "mismatch_causes": [(key, count) for key, count in mismatch_causes.most_common()],
        "examples": examples,
        "market_changes": market_changes,
        "trace_manifest": [
            {"job_id": row["job_id"], "episode_id": row["episode_id"],
             "seat": row["candidate_seat"], "rank": row["rank"],
             "trace_file": path.name, "trace_bytes": path.stat().st_size,
             "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for row, path, _ in traces
        ],
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True, default=str))
