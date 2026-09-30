"""Read-only physical trace audit for the two largest completed fresh losses."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "diagnostics/fresh90_improvement_20260929"
sys.path.insert(0, str(ROOT))
from diagnostics.physical_route_rollout_20260928 import native_core as core


def load_trace(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def op_name(action: object) -> str:
    return action[0] if isinstance(action, list) and action else "INVALID"


def asset_summary(farm: dict) -> tuple[Counter, Counter, Counter, Counter]:
    assets: Counter = Counter()
    yields: Counter = Counter()
    fragile: Counter = Counter()
    held_crops: Counter = Counter()
    for row in farm.get("tiles", []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            kind = tile.get("kind")
            if kind == "PLANT":
                crop = str(tile.get("crop"))
                assets[crop] += 1
                yields[crop] += int(tile.get("yield_units", 0) or 0)
                if int(tile.get("consecutive_unwatered", 0) or 0):
                    fragile[crop] += 1
            elif "animal" in tile:
                animal = str(tile["animal"])
                assets[animal] += 1
                yields[animal] += int(tile.get("yield_units", 0) or 0)
                if int(tile.get("consecutive_unfed", 0) or 0):
                    fragile[animal] += 1
            elif kind in ("COOP", "PASTURE"):
                assets[kind] += 1
    return assets, yields, fragile, held_crops


def action_reason(farm: dict, private: dict, idx: int, action: object,
                  day: int, blocked_plants: set[str]) -> str:
    if not isinstance(action, list) or not action:
        return "invalid"
    op = action[0]
    pos = core._farmer_position(farm, idx)
    if pos is None:
        return "missing_worker"
    x, y = pos
    invs = private.get("inventories", [])
    inv = invs[idx] if idx < len(invs) else {}
    tile = farm["tiles"][y][x]
    if op in core.FARMER_MOVES:
        dx, dy = core.FARMER_MOVES[op]
        nx, ny = x + dx, y + dy
        return "off_board_move" if not (0 <= nx < len(farm["tiles"]) and 0 <= ny < len(farm["tiles"])) else "unexpected_move_noop"
    if op in ("PASS",):
        return "pass"
    if op == "PICKUP":
        item = action[1] if len(action) > 1 else ""
        if tuple(pos) not in set(core._shed_access_tiles(len(farm["tiles"]))):
            return "not_at_shed_access"
        if int(private.get("shed", {}).get(item, 0) or 0) <= 0:
            return "shed_stock_empty"
        return "unexpected_pickup_noop"
    if op == "DROP":
        if tuple(pos) not in set(core._shed_access_tiles(len(farm["tiles"]))):
            return "not_at_shed_access"
        if not any(int(q or 0) > 0 for q in inv.values()):
            return "worker_cargo_empty"
        return "unexpected_drop_noop"
    if op == "PLACE":
        item = action[1] if len(action) > 1 else ""
        if item in core.ANIMALS:
            if not isinstance(tile, dict) or tile.get("kind") != core.ANIMALS[item]["structure"] or "animal" in tile:
                return "no_matching_empty_structure"
            if int(inv.get(item, 0) or 0) <= 0:
                return "animal_not_in_worker_cargo"
        return "unexpected_place_noop"
    if op == "PLANT":
        crop = action[1] if len(action) > 1 else ""
        if crop in blocked_plants:
            return "atomic_seed_shortage_gate"
        if tile == "LOCKED":
            return "locked_tile"
        if tile is not None:
            return "tile_occupied"
        if int(private.get("seeds", {}).get(crop, 0) or 0) <= 0:
            return "seed_stock_empty"
        return "unexpected_plant_noop"
    if op == "WATER":
        if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
            return "not_on_plant"
        if tile.get("watered_today"):
            return "already_watered_today"
        return "unexpected_water_noop"
    if op == "HARVEST":
        if not isinstance(tile, dict):
            return "not_on_producer"
        if int(tile.get("yield_units", 0) or 0) <= 0:
            return "no_yield_ready"
        if tile.get("kind") == "PLANT" and tile.get("crop") in core.CROPS and day - int(tile.get("planted_day", 0)) < core.CROPS[tile["crop"]]["first_yield_day"]:
            return "plant_not_mature"
        return "unexpected_harvest_noop"
    if op == "FEED":
        if not isinstance(tile, dict) or "animal" not in tile:
            return "not_on_animal"
        if tile.get("fed_today"):
            return "already_fed_today"
        if int(inv.get("WHEAT", 0) or 0) <= 0:
            return "worker_has_no_feed"
        return "unexpected_feed_noop"
    if op == "CARE":
        if not isinstance(tile, dict) or "animal" not in tile:
            return "not_on_animal"
        if tile.get("cared_today"):
            return "already_cared_today"
        return "unexpected_care_noop"
    if op == "COLLECT_FERTILIZER":
        if not isinstance(tile, dict) or "animal" not in tile:
            return "not_on_animal"
        if not tile.get("fertilizer_available"):
            return "not_ready"
        return "unexpected_collect_noop"
    if op == "FERTILIZE":
        if not isinstance(tile, dict) or tile.get("kind") != "PLANT":
            return "not_on_plant"
        if int(inv.get("FERTILIZER", 0) or 0) <= 0:
            return "worker_has_no_fertilizer"
        return "unexpected_fertilize_noop"
    if op == "DIG":
        if tile is None:
            return "empty_tile"
        if isinstance(tile, dict) and "animal" in tile:
            return "occupied_by_animal"
        return "unexpected_dig_noop"
    if op in ("BUILD_COOP", "BUILD_PASTURE"):
        return "tile_occupied" if tile is not None else "unexpected_build_noop"
    return "unsupported_op"


def simulate_own_farm_actions(obs: dict, actions: dict) -> tuple[dict, dict, list[dict]]:
    player = int(obs["player"])
    farm = deepcopy(obs["farms"][player])
    private = deepcopy(obs["private"])
    day = int(obs.get("day", 0))
    unit_actions = [actions.get("farmer", ["PASS"]), *actions.get("hands", [])]
    plant_demand: Counter = Counter()
    for action in unit_actions:
        if isinstance(action, list) and len(action) >= 2 and action[0] == "PLANT":
            plant_demand[str(action[1])] += 1
    seeds = private.get("seeds", {})
    blocked = {crop for crop, n in plant_demand.items() if n > int(seeds.get(crop, 0) or 0)}
    attempts = []
    board_size = len(farm.get("tiles", []))
    for idx, action in enumerate(unit_actions):
        name = op_name(action)
        if name == "PASS":
            continue
        reason = action_reason(farm, private, idx, action, day, blocked)
        before_farm, before_private = deepcopy(farm), deepcopy(private)
        effective = ["PASS"] if name == "PLANT" and len(action) >= 2 and str(action[1]) in blocked else action
        core._apply_unit_action(farm, private, idx, effective, board_size, day, 24, 100)
        changed = farm != before_farm or private != before_private
        attempts.append({"idx": idx, "action": action, "reason": reason, "changed": changed})
    return farm, private, attempts


def premarket_sell_capacity(obs: dict, actions: dict) -> list[dict]:
    """Exact own-inventory test for SELL fills, including prior worker and order effects."""
    player = int(obs["player"])
    farm, private, _ = simulate_own_farm_actions(obs, actions)
    market = deepcopy(obs.get("market", {}))
    records = []
    orders = actions.get("market", []) if isinstance(actions.get("market", []), list) else []
    for index, order in enumerate(orders[:10]):
        if not isinstance(order, list) or not order:
            continue
        op = str(order[0])
        if op == "HIRE":
            core._do_hire(farm, private, len(farm["tiles"]), 1)
            continue
        if op == "BUY_LAND":
            core._do_buy_land(farm, len(farm["tiles"]))
            continue
        if len(order) < 3:
            continue
        item = str(order[1])
        try:
            qty = max(0, int(order[2]))
        except (TypeError, ValueError):
            continue
        if op == "SELL":
            available = int(private.get("shed", {}).get(item, 0) or 0)
            filled = min(qty, available)
            failed = qty - filled
            if failed:
                records.append({"order_index": index, "step": int(obs["step"]), "day": int(obs["day"]),
                                "item": item, "requested": qty, "filled_by_own_stock": filled,
                                "unfilled": failed, "available_at_order": available})
        else:
            filled = 0
        for _ in range(qty):
            price = 0
            if op == "SELL" and item in core.PRODUCTS:
                price = core.market_price(item, market.get("inventory", {}).get(item, 10000), market.get("params"))
            elif op == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
                price = core.market_price(item, market.get("inventory", {}).get(item, 10000) - 1, market.get("params"))
            elif op == "BUY_SEED" and item in core.CROPS:
                price = int(core.CROPS[item]["seed"])
            elif op == "BUY_ANIMAL" and item in core.ANIMALS:
                price = int(core.ANIMALS[item]["cost"])
            else:
                break
            if not core._commit_unit(op, item, price, farm, private, market, 100):
                break
            filled += 1
            if op == "SELL" and price <= 1:
                market.setdefault("inventory", {}).setdefault(item, 10000)
            if op == "SELL" and price > 1:
                market.setdefault("inventory", {}).setdefault(item, 10000)
            if op in ("SELL", "BUY_PRODUCT"):
                core._refresh_prices(market)
    return records


def daily_line(obs: dict) -> dict:
    player = int(obs["player"])
    me, rival = obs["farms"][player], obs["farms"][1 - player]
    mine, my_yield, my_fragile, _ = asset_summary(me)
    theirs, their_yield, their_fragile, _ = asset_summary(rival)
    private = obs.get("private", {})
    return {
        "day": int(obs.get("day", 0)), "step": int(obs.get("step", -1)),
        "own_cash": round(float(me.get("money", 0))), "rival_cash": round(float(rival.get("money", 0))),
        "own_assets": dict(sorted(mine.items())), "own_yield": dict(sorted(my_yield.items())),
        "own_at_risk": dict(sorted(my_fragile.items())),
        "rival_assets": dict(sorted(theirs.items())), "rival_yield": dict(sorted(their_yield.items())),
        "rival_at_risk": dict(sorted(their_fragile.items())),
        "own_shed": {k: int(v or 0) for k, v in sorted(private.get("shed", {}).items()) if int(v or 0)},
        "own_seeds": {k: int(v or 0) for k, v in sorted(private.get("seeds", {}).items()) if int(v or 0)},
        "shops": list(obs.get("town", {}).get("unlocked_shops", [])),
    }


def analyze_case(rank: int, episode_id: int, seat: int, result: dict) -> dict:
    trace_path = ROOT / result["trace_path"]
    trace = load_trace(trace_path)
    assert trace and all(int(row["observation"]["player"]) == seat for row in trace)
    failures: Counter = Counter()
    failure_examples: dict[str, list] = {}
    sell_failures = []
    plant_demand_gates = Counter()
    farm_ops = Counter()
    successful_farm_ops = Counter()
    noops = Counter()
    bought = Counter()
    for row in trace:
        obs, action = row["observation"], row["action"]
        _, _, attempts = simulate_own_farm_actions(obs, action)
        for attempt in attempts:
            op = op_name(attempt["action"])
            farm_ops[op] += 1
            if attempt["changed"]:
                successful_farm_ops[op] += 1
            else:
                noops[op] += 1
                failures[(op, attempt["reason"])] += 1
                failure_examples.setdefault(f"{op}:{attempt['reason']}", [])
                if len(failure_examples[f"{op}:{attempt['reason']}"]) < 4:
                    failure_examples[f"{op}:{attempt['reason']}"] .append((int(obs["step"]), attempt["idx"], attempt["action"]))
        for order in action.get("market", [])[:10]:
            if isinstance(order, list) and len(order) >= 3:
                if order[0] in ("BUY_ANIMAL", "BUY_SEED"):
                    try:
                        bought[(str(order[0]), str(order[1]))] += int(order[2])
                    except (ValueError, TypeError):
                        pass
        sell_failures.extend(premarket_sell_capacity(obs, action))

    daily = [daily_line(row["observation"]) for row in trace if int(row["step"]) % 24 == 0]
    plant_losses = Counter()
    animal_escapes = Counter()
    for before, after in zip(trace, trace[1:]):
        pre, post = before["observation"], after["observation"]
        p = int(pre["player"])
        f0, f1 = pre["farms"][p], post["farms"][p]
        for y, row in enumerate(f0.get("tiles", [])):
            for x, tile in enumerate(row):
                new = f1.get("tiles", [])[y][x]
                if isinstance(tile, dict) and tile.get("kind") == "PLANT":
                    if isinstance(new, dict) and new.get("kind") == "WEED":
                        plant_losses[str(tile.get("crop"))] += 1
                if isinstance(tile, dict) and "animal" in tile:
                    if isinstance(new, dict) and new.get("kind") == tile.get("kind") and "animal" not in new:
                        animal_escapes[str(tile.get("animal"))] += 1

    return {
        "rank": rank, "episode_id": episode_id, "team": result["team"], "seat": seat,
        "margin": result["margin"], "candidate_reward": result["candidate_reward"],
        "opponent_reward": result["opponent_reward"], "route_pair": result["candidate_telemetry"].get("minimal_route_pair144"),
        "route_switch": result["candidate_telemetry"].get("minimal_route"),
        "trace_path": str(trace_path), "trace_rows": len(trace),
        "farm_ops": dict(farm_ops), "successful_farm_ops": dict(successful_farm_ops), "noops_by_op": dict(noops),
        "noops_by_reason": {f"{op}:{reason}": n for (op, reason), n in sorted(failures.items())},
        "failure_examples": failure_examples,
        "unfilled_sell_quantities": sum(x["unfilled"] for x in sell_failures),
        "unfilled_sell_orders": len(sell_failures), "unfilled_sell_by_item": dict(Counter({item: sum(x["unfilled"] for x in sell_failures if x["item"] == item) for item in {x["item"] for x in sell_failures}})),
        "sell_failure_examples": sell_failures[:30], "buy_order_qty_requested": {f"{op} {item}": n for (op, item), n in sorted(bought.items())},
        "plant_losses_to_weed": dict(plant_losses), "animals_escaped": dict(animal_escapes),
        "daily": daily,
    }


def main() -> None:
    path = BASE / "cb76_top20_jobs_results.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    groups = {}
    for row in rows:
        if row.get("result") == "loss":
            groups.setdefault(row["fixture_id"], []).append(row)
    losses = sorted(groups.values(), key=lambda rs: min(float(r["margin"]) for r in rs))
    chosen = []
    for pair in losses:
        if len(chosen) == 2:
            break
        chosen.append(pair)
    report = []
    for pair in chosen:
        representative = next(r for r in pair if r["candidate_seat"] == 0)
        for r in sorted(pair, key=lambda x: x["candidate_seat"]):
            report.append(analyze_case(int(r["rank"]), int(r["episode_id"]), int(r["candidate_seat"]), r))
    target = ROOT / "diagnostics/fresh90_loss_audit_20260929/fresh_trace_findings.json"
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps([{k: v for k, v in x.items() if k != "daily" and k != "failure_examples" and k != "sell_failure_examples"}
                      for x in report], indent=2, ensure_ascii=False))
    for x in report:
        print(f"\nDAILY rank{x['rank']} seat{x['seat']} {x['team']}")
        for d in x["daily"]:
            if d["day"] in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 18, 21, 24, 27, 29):
                print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    main()
