from __future__ import annotations

import gzip
import json
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOSS = ROOT / "diagnostics/loss_class_20260927/live_loss_ledgers_180951.json"
TOP20 = ROOT / "diagnostics/loss_class_20260927/current_top20_ledgers.json"
SHED_ACCESS = [(4, 4), (5, 4), (4, 5), (5, 5)]
MELON_MATURITY_DAYS = 10
DAY = 24


def load_rows(path: Path):
    blob = json.loads(path.read_text(encoding="utf-8"))
    for row in blob["rows"]:
        yield row


def action_for(rec: dict, actor: int):
    action = rec.get("actions", rec.get("action")) or {}
    if actor == 0:
        return action.get("farmer", ["PASS"])
    hands = action.get("hands", [])
    return hands[actor - 1] if actor - 1 < len(hands) else ["PASS"]


def owner_snapshot(rec: dict, player: int):
    obs = rec["observation"]
    farm = obs["farms"][player]
    return {
        "step": int(rec["step"]),
        "day": int(obs.get("day", int(rec["step"]) // DAY)),
        "farm": farm,
        "private": obs["private"],
        "actions": rec["action"] or {},
    }


def manhattan(a, b):
    return abs(int(a[0]) - int(b[0])) + abs(int(a[1]) - int(b[1]))


def harvest_flow_metrics(trace: dict, player: int, by_step: dict, crops: dict, last_step: int):
    """FIFO-map harvest batches through shed deposits and actual MELON sales."""
    sales_by_step = {}
    for event in trace["events"]:
        if (event.get("player") == player and event.get("phase") == "market_unit"
                and event.get("operation") == "SELL" and event.get("item") == "MELON"
                and event.get("success")):
            sales_by_step.setdefault(int(event["step"]), []).append(event)
    turns = {int(item["step"]): item for item in trace["turns"]}
    harvests_by_step = {}
    for crop in crops.values():
        if crop["harvest_step"] is not None:
            harvests_by_step.setdefault(crop["harvest_step"], []).append(crop)

    carrying, in_shed = deque(), deque()
    initial_shed = int(by_step[0]["private"].get("shed", {}).get("MELON", 0))
    if initial_shed:
        in_shed.append({"crop": None, "units": initial_shed, "harvest_step": -1})

    delivered_lags = []
    delayed_sale_count = 0
    delayed_actual_cash = delayed_earlier_peak_cash = 0.0
    delayed_signed_delta = delayed_positive_delta = 0.0
    all_signed_delta = all_positive_delta = 0.0
    unmatched_sale_units = 0
    pickup_steps = 0
    unmatched_deposit_units = 0

    for step in range(last_step):
        rec, next_rec = by_step[step], by_step.get(step + 1)
        if next_rec is None:
            break
        sales = sales_by_step.get(step, [])
        for event in sales:
            if not in_shed:
                unmatched_sale_units += 1
                continue
            lot = in_shed[0]
            lot["units"] -= 1
            actual = float(event["quoted_unit_price"])
            previous_peak = None
            previous_day = step // DAY - 1
            if previous_day >= 0:
                prices = [float(turns[t]["market_before"]["prices"]["MELON"])
                          for t in range(previous_day * DAY, (previous_day + 1) * DAY)
                          if t in turns]
                previous_peak = max(prices) if prices else None
            if previous_peak is not None:
                delta = previous_peak - actual
                all_signed_delta += delta
                all_positive_delta += max(0.0, delta)
                crop = lot["crop"]
                if crop is not None and crop.get("wait_gt_1_day", False):
                    delayed_sale_count += 1
                    delayed_actual_cash += actual
                    delayed_earlier_peak_cash += previous_peak
                    delayed_signed_delta += delta
                    delayed_positive_delta += max(0.0, delta)
            if lot["units"] <= 0:
                in_shed.popleft()

        # MELON pickup is not expected in these routes. Count it and use the
        # requested amount as a correction to the observed shed delta; any
        # such case is separately reported as an attribution limitation.
        pickup_requested = 0
        rec_positions = [rec["farm"]["farmer"], *rec["farm"].get("hands", [])]
        available = max(0, int(rec["private"].get("shed", {}).get("MELON", 0)) - len(sales))
        for actor, pos in enumerate(rec_positions):
            action = action_for(rec, actor)
            if (len(action) >= 2 and action[0] == "PICKUP" and action[1] == "MELON"
                    and tuple(pos) in SHED_ACCESS):
                requested = max(0, int(action[2]) if len(action) >= 3 else 1)
                actual_pickup = min(available, requested)
                pickup_requested += actual_pickup
                available -= actual_pickup
        if pickup_requested:
            pickup_steps += 1

        shed_before = int(rec["private"].get("shed", {}).get("MELON", 0))
        shed_after = int(next_rec["private"].get("shed", {}).get("MELON", 0))
        deposits = shed_after - shed_before + len(sales) + pickup_requested
        if deposits < 0:
            unmatched_deposit_units += -deposits
            deposits = 0

        day_end = step % DAY == DAY - 1
        harvests = harvests_by_step.get(step, [])
        if day_end:
            for crop in harvests:
                carrying.append({"crop": crop, "units": int(crop["harvest_units"]),
                                 "harvest_step": step})

        remaining = deposits
        while remaining > 0 and carrying:
            lot = carrying[0]
            moved = min(remaining, lot["units"])
            in_shed.append({"crop": lot["crop"], "units": moved,
                            "harvest_step": lot["harvest_step"]})
            delivered_lags.extend([step - lot["harvest_step"]] * moved)
            lot["units"] -= moved
            remaining -= moved
            if lot["units"] <= 0:
                carrying.popleft()
        if remaining > 0:
            unmatched_deposit_units += remaining

        if not day_end:
            for crop in harvests:
                carrying.append({"crop": crop, "units": int(crop["harvest_units"]),
                                 "harvest_step": step})

    return {
        "delivered_units": len(delivered_lags),
        "lag_turns": delivered_lags,
        "over_24_turn_units": sum(lag > DAY for lag in delivered_lags),
        "median_lag_turns": sorted(delivered_lags)[len(delivered_lags) // 2] if delivered_lags else None,
        "max_lag_turns": max(delivered_lags) if delivered_lags else None,
        "delayed_units_sold": delayed_sale_count,
        "delayed_actual_cash": round(delayed_actual_cash, 2),
        "delayed_prior_day_peak_cash": round(delayed_earlier_peak_cash, 2),
        "delayed_prior_day_signed_delta": round(delayed_signed_delta, 2),
        "delayed_prior_day_positive_only_ceiling": round(delayed_positive_delta, 2),
        "all_melon_prior_day_signed_delta": round(all_signed_delta, 2),
        "all_melon_prior_day_positive_only_ceiling": round(all_positive_delta, 2),
        "unmatched_sale_units": unmatched_sale_units,
        "unmatched_deposit_units": unmatched_deposit_units,
        "melon_pickup_steps": pickup_steps,
        "carrying_units_at_end": sum(lot["units"] for lot in carrying),
        "shed_units_at_end_in_fifo": sum(lot["units"] for lot in in_shed),
    }


def audit_one(row: dict):
    path = Path(row["trace_path"])
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        trace = json.load(handle)
    player = int(trace["candidate_seat"])
    records = [owner_snapshot(rec, player) for rec in trace["traces"][player]]
    by_step = {rec["step"]: rec for rec in records}
    last_step = max(by_step)
    crops = {}
    for rec in records:
        step, day, farm = rec["step"], rec["day"], rec["farm"]
        tiles = farm["tiles"]
        for y, tile_row in enumerate(tiles):
            for x, tile in enumerate(tile_row):
                if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"
                        and tile.get("crop") == "MELON"):
                    continue
                planted = int(tile["planted_day"])
                key = (x, y, planted)
                item = crops.setdefault(key, {
                    "x": x, "y": y, "planted_day": planted,
                    "mature_step": (planted + MELON_MATURITY_DAYS) * DAY,
                    "states": {}, "harvest_step": None, "harvest_units": 0,
                    "harvest_actor": None,
                })
                item["states"][step] = int(tile.get("yield_units", 0))
                age = day - planted
                if age < MELON_MATURITY_DAYS or int(tile.get("yield_units", 0)) <= 0:
                    continue
                for actor, pos in enumerate([farm["farmer"], *farm.get("hands", [])]):
                    if tuple(pos) != (x, y) or action_for(rec, actor) != ["HARVEST"]:
                        continue
                    if item["harvest_step"] is None:
                        item["harvest_step"] = step
                        item["harvest_units"] = int(tile.get("yield_units", 0))
                        item["harvest_actor"] = actor

    mature = []
    for crop in crops.values():
        ready_step = crop["mature_step"]
        ready = by_step.get(ready_step)
        if ready is None:
            continue
        x, y = crop["x"], crop["y"]
        tile = ready["farm"]["tiles"][y][x]
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"
                and tile.get("crop") == "MELON"
                and int(tile.get("planted_day", -1)) == crop["planted_day"]
                and int(tile.get("yield_units", 0)) > 0):
            continue
        crop["ready_units"] = int(tile["yield_units"])
        crop["ready_step_observed"] = ready_step
        harvest = crop["harvest_step"]
        if harvest is not None:
            crop["lag_turns"] = int(harvest - ready_step)
            crop["lag_days"] = crop["lag_turns"] / DAY
            crop["wait_gt_1_day"] = crop["lag_turns"] > DAY
        else:
            crop["lag_turns"] = None
            crop["lag_days"] = None
            crop["wait_gt_1_day"] = False
        threshold_step = ready_step + DAY + 1
        threshold_units = crop["states"].get(threshold_step, 0)
        crop["units_waiting_gt_1_day"] = int(threshold_units)
        mature.append(crop)

    # Assess both geometric feasibility and an intentionally conservative
    # no-displacement window: the worker must have one contiguous PASS run
    # long enough to harvest, reach the shed, drop, and return to its start.
    for crop in mature:
        ready_step = crop["mature_step"]
        stop_step = crop["harvest_step"] if crop["harvest_step"] is not None else last_step + 1
        ready_rec = by_step[ready_step]
        farm = ready_rec["farm"]
        positions = [farm["farmer"], *farm.get("hands", [])]
        crop_pos = (crop["x"], crop["y"])
        best_geom = None
        best_free = None
        for actor, start_pos in enumerate(positions):
            start = tuple(start_pos)
            to_crop = manhattan(start, crop_pos)
            to_shed = min(manhattan(crop_pos, access) for access in SHED_ACCESS)
            return_home = min(
                manhattan(access, start) for access in SHED_ACCESS
            )
            geom_actions = to_crop + 1 + to_shed + 1
            round_trip_actions = geom_actions + return_home
            if best_geom is None or geom_actions < best_geom["actions"]:
                best_geom = {"actor": actor, "actions": geom_actions,
                             "moves_to_crop": to_crop, "moves_to_shed": to_shed}
            if crop["harvest_step"] is not None and ready_step + geom_actions - 1 < stop_step:
                crop["geometrically_before_route"] = True
            horizon = min(stop_step, ready_step + 2 * DAY)
            best_run = 0
            run = 0
            run_start = None
            qualifying = False
            for step in range(ready_step, horizon):
                rec = by_step.get(step)
                if rec is None or action_for(rec, actor) != ["PASS"]:
                    if run > best_run:
                        best_run = run
                    run = 0
                    run_start = None
                    continue
                if run_start is None:
                    run_start = step
                run += 1
                if run >= round_trip_actions:
                    qualifying = True
            best_run = max(best_run, run)
            if best_free is None or best_run > best_free["pass_run"]:
                best_free = {"actor": actor, "pass_run": best_run,
                             "required": round_trip_actions,
                             "possible_without_route_displacement": qualifying}
            elif qualifying:
                best_free["possible_without_route_displacement"] = True
        crop["best_geometric_route"] = best_geom
        crop["best_free_window"] = best_free
        crop["geometrically_before_route"] = bool(crop.get("geometrically_before_route", False))
        crop.pop("states", None)

    total_ready_units = sum(c["ready_units"] for c in mature)
    harvested = [c for c in mature if c["harvest_step"] is not None]
    delayed = [c for c in harvested if c["lag_turns"] > DAY]
    outstanding_gt1 = [c for c in mature if c["units_waiting_gt_1_day"] > 0]
    free_before = [c for c in mature if c.get("best_free_window", {}).get(
        "possible_without_route_displacement", False)]
    geom_before = [c for c in mature if c["geometrically_before_route"]]
    flow = harvest_flow_metrics(trace, player, by_step, crops, last_step)
    return {
        "team": row.get("opponent", row.get("team")),
        "episode_id": row["episode_id"],
        "margin": float(row["margin"]),
        "trace_path": str(path),
        "mature_crop_count": len(mature),
        "mature_units_at_ready": total_ready_units,
        "harvested_crop_count": len(harvested),
        "delayed_over_24_turns_crop_count": len(delayed),
        "delayed_over_24_turns_harvest_units": sum(c["harvest_units"] for c in delayed),
        "units_still_waiting_over_24_turns": sum(c["units_waiting_gt_1_day"] for c in mature),
        "geometric_earlier_harvest_and_shed_possible": len(geom_before),
        "strict_pass_window_no_displacement_possible": len(free_before),
        "harvest_to_shed": flow,
        "crops": mature,
    }


def main():
    rows = list(load_rows(LOSS)) + list(load_rows(TOP20))
    audits = [audit_one(row) for row in rows]
    totals = {
        "trace_count": len(audits),
        "mature_crop_count": sum(a["mature_crop_count"] for a in audits),
        "mature_units_at_ready": sum(a["mature_units_at_ready"] for a in audits),
        "delayed_crop_count": sum(a["delayed_over_24_turns_crop_count"] for a in audits),
        "delayed_units_harvested": sum(a["delayed_over_24_turns_harvest_units"] for a in audits),
        "units_still_waiting_over_24_turns": sum(a["units_still_waiting_over_24_turns"] for a in audits),
        "geometric_earlier_harvest_and_shed_possible": sum(a["geometric_earlier_harvest_and_shed_possible"] for a in audits),
        "strict_pass_window_no_displacement_possible": sum(a["strict_pass_window_no_displacement_possible"] for a in audits),
        "harvest_to_shed_delivered_units": sum(a["harvest_to_shed"]["delivered_units"] for a in audits),
        "harvest_to_shed_over_24_turn_units": sum(a["harvest_to_shed"]["over_24_turn_units"] for a in audits),
        "harvest_to_shed_max_lag_turns": max(a["harvest_to_shed"]["max_lag_turns"] or 0 for a in audits),
        "delayed_harvest_units_sold": sum(a["harvest_to_shed"]["delayed_units_sold"] for a in audits),
        "delayed_harvest_actual_cash": round(sum(a["harvest_to_shed"]["delayed_actual_cash"] for a in audits), 2),
        "delayed_harvest_prior_day_signed_delta": round(sum(a["harvest_to_shed"]["delayed_prior_day_signed_delta"] for a in audits), 2),
        "delayed_harvest_prior_day_positive_only_ceiling": round(sum(a["harvest_to_shed"]["delayed_prior_day_positive_only_ceiling"] for a in audits), 2),
        "all_melon_prior_day_positive_only_ceiling": round(sum(a["harvest_to_shed"]["all_melon_prior_day_positive_only_ceiling"] for a in audits), 2),
        "flow_unmatched_sale_units": sum(a["harvest_to_shed"]["unmatched_sale_units"] for a in audits),
        "flow_unmatched_deposit_units": sum(a["harvest_to_shed"]["unmatched_deposit_units"] for a in audits),
        "melon_pickup_steps": sum(a["harvest_to_shed"]["melon_pickup_steps"] for a in audits),
    }
    output = {"scope": "30 live losses plus 4 current top20 one-seat native traces",
              "maturity_rule": "MELON can be harvested at day - planted_day >= 10; ready step is (planted_day + 10) * 24.",
              "delay_rule": "More than one day means more than 24 turns after the first mature step.",
              "physical_route_rule": "Manhattan movement, HARVEST, shortest route to shed-access tile, DROP.",
              "no_displacement_rule": "A contiguous PASS-only window must fit harvest, shed delivery, and return to the starting tile.",
              "totals": totals,
              "traces": audits}
    target = Path(__file__).with_name("lag_audit.json")
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), "totals": totals,
                      "per_trace": [{k: a[k] for k in ("team", "episode_id", "mature_crop_count",
                                                       "delayed_over_24_turns_crop_count",
                                                       "delayed_over_24_turns_harvest_units",
                                                       "units_still_waiting_over_24_turns",
                                                       "geometric_earlier_harvest_and_shed_possible",
                                                       "strict_pass_window_no_displacement_possible")}
                                    | {"harvest_to_shed": a["harvest_to_shed"]}
                                    for a in audits if a["mature_crop_count"]]}, indent=2))


if __name__ == "__main__":
    main()
