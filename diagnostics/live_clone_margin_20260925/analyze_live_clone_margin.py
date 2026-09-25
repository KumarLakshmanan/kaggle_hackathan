#!/usr/bin/env python3
"""Read-only audit of completed replays for Kaggle submission 56530281.

Outputs are deliberately confined to this directory. SELL fills are only
attributed from private-inventory deltas on turns where the replay state makes
the item-level change unambiguous; other turns are reported as ambiguous.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "live_submission_56530281_20260925"
AUDIT = SOURCE / "audit_latest_24.json"
MAIN = HERE.parents[1] / "main.py"
ITEMS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "EGG", "MILK", "WOOL", "FERTILIZER")
PRICE_PARAMS = {
    "WHEAT": (25, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 450, "hinge", 1.0, "sqrt", 0.7),
    "TOMATO": (60, 200, "hinge", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 332, "hinge", 0.4, "log", 0.2),
    "MILK": (160, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 200, "linear", 0.4, "linear", 0.4),
}


def stock(private: dict, item: str) -> int:
    total = int((private.get("shed") or {}).get(item, 0) or 0)
    for inventory in private.get("inventories") or []:
        total += int((inventory or {}).get(item, 0) or 0)
    return total


def unit_actions(action: dict) -> list[list]:
    return [a for a in [action.get("farmer"), *(action.get("hands") or [])]
            if isinstance(a, list) and a]


def touches_item(action: dict, item: str) -> bool:
    for unit in unit_actions(action):
        op = unit[0]
        arg = unit[1] if len(unit) > 1 else None
        if op == "DROP" or op == "HARVEST":
            return True
        if op in ("PICKUP", "PLACE") and arg == item:
            return True
        if op == "FEED" and item == "WHEAT":
            return True
        if op in ("FERTILIZE", "COLLECT_FERTILIZER") and item == "FERTILIZER":
            return True
    return False


def shed_after_units(pre_obs: dict, action: dict, seat: int) -> dict:
    """Mirror main.py's observation-based projected-shed unit adjustments."""
    farm = pre_obs["farms"][seat]
    private = pre_obs["private"]
    projected = {k: int(v or 0) for k, v in (private.get("shed") or {}).items()}
    total = sum(projected.values())
    cap = 100
    positions = [farm.get("farmer")] + list(farm.get("hands") or [])
    units = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
    for index in range(min(len(units), len(positions))):
        pos = positions[index]
        if not (isinstance(pos, (list, tuple)) and len(pos) >= 2
                and pos[0] in (4, 5) and pos[1] in (4, 5)):
            continue
        unit = units[index]
        if not unit:
            continue
        op = unit[0]
        inventory = ((private.get("inventories") or [])[index]
                     if index < len(private.get("inventories") or []) else {})
        if op == "PICKUP" and len(unit) >= 2 and unit[1] in projected:
            quantity = max(0, int(unit[2])) if len(unit) >= 3 else 1
            take = min(projected[unit[1]], quantity)
            projected[unit[1]] -= take
            total -= take
        elif op == "DROP":
            for item, held in inventory.items():
                take = min(max(0, int(held or 0)), max(0, cap - total))
                projected[item] = projected.get(item, 0) + take
                total += take
        elif op == "PLACE" and len(unit) >= 2 and unit[1] not in ("GOOSE", "COW", "SHEEP"):
            item = unit[1]
            requested = max(0, int(unit[2])) if len(unit) >= 3 else 1
            take = min(requested, max(0, int(inventory.get(item, 0) or 0)),
                       max(0, cap - total))
            projected[item] = projected.get(item, 0) + take
            total += take
    return projected


def _shape(kind: str, value: float, threshold: float) -> float:
    value = max(0.0, value)
    if kind == "linear":
        return value
    if kind == "sq":
        return value * value
    if kind == "sqrt":
        return value ** 0.5
    if kind == "log":
        import math
        return math.log(1.0 + value)
    if kind == "hinge":
        ratio = value / threshold
        return ratio + 8.0 * max(0.0, ratio - 1.0) ** 2
    return value


def market_price(item: str, inventory: int, market: dict) -> int:
    """Mirror main.py's imported Kaggriculture per-unit market-price model."""
    base, threshold, below, below_target, above, above_target = PRICE_PARAMS[item]
    patch = (market.get("params") or {}).get(item, {})
    base = patch.get("base", base)
    threshold = patch.get("T", threshold)
    below = patch.get("below_func", below)
    below_target = patch.get("below_target", below_target)
    above = patch.get("above_func", above)
    above_target = patch.get("above_target", above_target)
    equilibrium = patch.get("I0", 10000)
    if inventory < equilibrium:
        amplitude = below_target * base / _shape(below, threshold, threshold)
        price = base + amplitude * _shape(below, equilibrium - inventory, threshold)
    else:
        amplitude = above_target * base / _shape(above, threshold, threshold)
        price = base - amplitude * _shape(above, inventory - equilibrium, threshold)
    return max(1, int(round(price)))


def episode_record(path: Path, audit_by_id: dict) -> dict:
    replay = json.loads(path.read_text(encoding="utf-8"))
    names = replay["info"]["TeamNames"]
    our_seat = names.index("Lakshmanan R")
    rival_seat = 1 - our_seat
    nsteps = len(replay["steps"])
    audited = audit_by_id[int(replay["info"]["EpisodeId"])]

    day_cash = []
    day_item = []
    clean_sales = defaultdict(lambda: {"qty": 0, "gross_at_open_quote_proxy": 0.0,
                                       "observed_cash_receipts": 0.0,
                                       "cash_receipt_events": 0, "events": 0,
                                       "requested": 0, "ambiguous_requests": 0})
    clean_revenue_checks = []
    fill_events = []
    item_cash_events = []
    sell_stats = {seat: Counter() for seat in (our_seat, rival_seat)}
    action_rows = {seat: [] for seat in (our_seat, rival_seat)}

    for seat in (our_seat, rival_seat):
        for step in replay["steps"]:
            action_rows[seat].append(step[seat].get("action") or {})

    # End-of-day values from the authoritative replay observations.
    for day in range(30):
        index = min((day + 1) * 24 - 1, nsteps - 1)
        pair = replay["steps"][index]
        own_obs = pair[our_seat]["observation"]
        rival_obs = pair[rival_seat]["observation"]
        own_cash = float(own_obs["farms"][our_seat]["money"])
        rival_cash = float(rival_obs["farms"][rival_seat]["money"])
        day_cash.append({"day": day, "our": own_cash, "rival": rival_cash,
                         "margin": own_cash - rival_cash})

        start_i = day * 24
        end_i = min((day + 1) * 24 - 1, nsteps - 1)
        start_obs = replay["steps"][start_i][our_seat]["observation"]
        end_obs = replay["steps"][end_i][our_seat]["observation"]
        item_rows = []
        for item in ITEMS:
            inv_start = int(start_obs["market"]["inventory"].get(item, 0))
            inv_end = int(end_obs["market"]["inventory"].get(item, 0))
            item_rows.append({
                "item": item,
                "market_inventory_start": inv_start,
                "market_inventory_end": inv_end,
                "market_inventory_delta": inv_end - inv_start,
                "price_start": int(start_obs["market"]["prices"].get(item, 0)),
                "price_end": int(end_obs["market"]["prices"].get(item, 0)),
            })
        day_item.append({"day": day, "items": item_rows})

    # Reconcile each SELL against an action-adjusted shed projection from the
    # recorded pre-action observation and the replay's post-action shed.
    for seat in (our_seat, rival_seat):
        for index in range(1, nsteps):
            step = replay["steps"][index][seat]
            prev = replay["steps"][index - 1][seat]["observation"]
            obs = step["observation"]
            action = step.get("action") or {}
            market_orders = action.get("market") or []
            sells_by_item = defaultdict(list)
            for order_index, order in enumerate(market_orders[:10]):
                if isinstance(order, list) and len(order) >= 3 and order[0] == "SELL":
                    sells_by_item[order[1]].append((order_index, order))
                    sell_stats[seat]["sell_orders"] += 1
                    sell_stats[seat]["requested_qty"] += max(0, int(order[2] or 0))
                    sell_stats[seat]["zero_qty_orders"] += int(max(0, int(order[2] or 0)) == 0)
            for item, same_sells in sells_by_item.items():
                total_requested = sum(max(0, int(o[2] or 0)) for _, o in same_sells)
                if item not in ITEMS or total_requested == 0:
                    continue
                key = (seat, int(obs["day"]), item)
                # A same-item buy is ambiguous because affordability and the
                # 100-unit shed cap can reduce its fill. All other unit changes
                # are applied from the recorded pre-action observation.
                same_item_buys = [j for j, o in enumerate(market_orders)
                                  if isinstance(o, list) and len(o) >= 3
                                  and o[0] == "BUY_PRODUCT" and o[1] == item]
                if same_item_buys:
                    clean_sales[key]["ambiguous_requests"] += total_requested
                    sell_stats[seat]["ambiguous_orders"] += len(same_sells)
                    continue
                predicted = shed_after_units(prev, action, seat)
                available = max(0, int(predicted.get(item, 0)))
                fills = []
                for _, order in same_sells:
                    fill = min(max(0, int(order[2] or 0)), available)
                    fills.append(fill)
                    available -= fill
                actual = sum(fills)
                # Reconcile the action-adjusted predicted shelf with the replay's
                # post-action private shed. This is the guard against mistaking
                # a submitted quantity for an executed fill.
                projected_end = max(0, int(predicted.get(item, 0)) - actual)
                observed_end = int((obs.get("private", {}).get("shed") or {}).get(item, 0) or 0)
                if (int(prev["day"]) != int(obs["day"]) or projected_end != observed_end):
                    clean_sales[key]["ambiguous_requests"] += total_requested
                    sell_stats[seat]["ambiguous_orders"] += len(same_sells)
                    continue
                quote = float(prev["market"]["prices"].get(item, 0) or 0)
                clean_sales[key]["requested"] += total_requested
                clean_sales[key]["qty"] += actual
                clean_sales[key]["gross_at_open_quote_proxy"] += actual * quote
                clean_sales[key]["events"] += 1
                sell_stats[seat]["clean_orders"] += len(same_sells)
                sell_stats[seat]["clean_requested_qty"] += total_requested
                sell_stats[seat]["clean_filled_qty"] += actual
                sell_stats[seat]["zero_fill_positive_requests"] += int(actual == 0)
                for (order_index, order), fill in zip(same_sells, fills):
                    fill_events.append({"step": index, "day": int(obs["day"]),
                                        "hour": int(obs["hour"]), "seat": seat,
                                        "item": item, "order_index": order_index,
                                        "requested": max(0, int(order[2] or 0)),
                                        "filled": fill,
                                        "pre_market_inventory": int(prev["market"]["inventory"].get(item, 0)),
                                        "post_market_inventory": int(obs["market"]["inventory"].get(item, 0))})

                # When this is the only kind of market order and every SELL is
                # for one item, the observed cash change is the actual item cash
                # receipt (including within-turn dynamic pricing/seat order).
                one_item_only = (len(market_orders) == len(same_sells)
                                 and {o[1] for _, o in same_sells} == {item}
                                 and int(obs["hour"]) != 23)
                if one_item_only:
                    before_cash = float(prev["farms"][seat]["money"])
                    after_cash = float(obs["farms"][seat]["money"])
                    cash_delta = after_cash - before_cash
                    clean_sales[key]["observed_cash_receipts"] += cash_delta
                    clean_sales[key]["cash_receipt_events"] += 1
                    clean_revenue_checks.append({
                        "step": index, "day": int(obs["day"]), "hour": int(obs["hour"]),
                        "seat": seat, "item": item, "requested": total_requested,
                        "observed_fill": actual, "pre_action_quote": quote,
                        "cash_delta": cash_delta,
                        "quote_value_proxy": actual * quote,
                        "residual_vs_quote_proxy": cash_delta - actual * quote,
                    })

    # Reconstruct exact per-item sale receipts from replay-confirmed fills and
    # Kaggriculture's simultaneous, per-unit market-order execution. We admit a
    # step/item only when neither player buys that item on the same turn.
    fills_by_step_item = defaultdict(list)
    for event in fill_events:
        fills_by_step_item[(event["step"], event["item"])].append(event)
    for (index, item), events in sorted(fills_by_step_item.items()):
        actions = [replay["steps"][index][seat].get("action") or {}
                   for seat in (0, 1)]
        if any(any(isinstance(order, list) and len(order) >= 3
                   and order[0] == "BUY_PRODUCT" and order[1] == item
                   for order in action.get("market") or []) for action in actions):
            continue
        pre_obs = replay["steps"][index - 1][0]["observation"]
        post_obs = replay["steps"][index][0]["observation"]
        market_before = pre_obs["market"]
        inv_before = int(market_before["inventory"].get(item, 0))
        inv_after = int(post_obs["market"]["inventory"].get(item, 0))
        fills_by_seat = {seat: sum(e["filled"] for e in events if e["seat"] == seat)
                         for seat in (0, 1)}
        receipts = {0: 0, 1: 0}
        remaining = {(e["seat"], e["order_index"]): e["filled"] for e in events}
        order_indices = sorted({e["order_index"] for e in events})
        inventory = inv_before
        for order_index in order_indices:
            while any(remaining.get((seat, order_index), 0) > 0 for seat in (0, 1)):
                quote = market_price(item, inventory, market_before)
                for seat in (0, 1):
                    key = (seat, order_index)
                    if remaining.get(key, 0) <= 0:
                        continue
                    receipts[seat] += quote
                    remaining[key] -= 1
                    if quote > 1:
                        inventory += 1
        item_cash_events.append({
            "step": index, "day": int(post_obs["day"]), "hour": int(post_obs["hour"]),
            "item": item, "inventory_before": inv_before,
            "inventory_after": inv_after, "filled_by_seat": fills_by_seat,
            "market_inventory_delta": inv_after - inv_before,
            "fill_minus_inventory_delta": sum(fills_by_seat.values()) - (inv_after - inv_before),
            "simultaneous_lockstep_receipts": receipts,
        })
    cash_event_map = {(e["step"], e["item"]): e for e in item_cash_events}
    for check in clean_revenue_checks:
        event = cash_event_map.get((check["step"], check["item"]))
        if event:
            check["model_lockstep_receipt"] = event["simultaneous_lockstep_receipts"][check["seat"]]
            check["model_lockstep_residual"] = check["cash_delta"] - check["model_lockstep_receipt"]

    # Cross-game similarity for the actual submitted farmer/hands actions.
    farmer = [a.get("farmer") or [] for a in action_rows[our_seat]]
    hands = [a.get("hands") or [] for a in action_rows[our_seat]]
    return {
        "episode_id": int(replay["info"]["EpisodeId"]),
        "seed": replay["info"]["seed"], "opponent": names[rival_seat],
        "our_seat": our_seat, "outcome": audited["outcome"],
        "margin": audited["margin"],
        "farmer_opponent_matches": audited["exact_action_matches"]["farmer"],
        "farmer_actions": farmer, "hands_actions": hands,
        "day_cash": day_cash, "day_item_market": day_item,
        "clean_sales": [
            {"seat": seat, "day": day, "item": item, **values}
            for (seat, day, item), values in sorted(clean_sales.items())
        ],
        "sell_stats": {str(seat): dict(counts) for seat, counts in sell_stats.items()},
        "clean_revenue_checks": clean_revenue_checks,
        "model_item_cash_events": item_cash_events,
    }


def main() -> None:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    audit_by_id = {int(row["episode_id"]): row for row in audit["episodes"]}
    records = [episode_record(p, audit_by_id)
               for p in sorted(SOURCE.glob("episode-*-replay.json"))]
    by_id = {r["episode_id"]: r for r in records}
    model_checks = [check for record in records for check in record["clean_revenue_checks"]
                    if "model_lockstep_residual" in check]
    residuals = [abs(check["model_lockstep_residual"]) for check in model_checks]
    lockstep_fit = {
        "checks": len(residuals),
        "exact_within_1": sum(value <= 1 for value in residuals),
        "median_abs_residual": sorted(residuals)[len(residuals) // 2] if residuals else None,
        "total_abs_residual": sum(residuals),
        "max_abs_residual": max(residuals) if residuals else None,
    }
    for record in records:
        aggregate = defaultdict(lambda: {"filled": 0, "receipt": 0})
        for event in record["model_item_cash_events"]:
            for seat in (0, 1):
                key = (seat, event["day"], event["item"])
                aggregate[key]["filled"] += event["filled_by_seat"][seat]
                aggregate[key]["receipt"] += event["simultaneous_lockstep_receipts"][seat]
        record["model_sale_cash_by_day_item"] = [
            {"seat": seat, "day": day, "item": item, **values}
            for (seat, day, item), values in sorted(aggregate.items())]
        record["market_execution_model"] = "simultaneous_lockstep_by_order_slot"
    pairs = []
    losses = [r for r in records if r["outcome"] == "loss"]
    wins = [r for r in records if r["outcome"] == "win"]
    for loss in losses:
        for win in wins:
            if loss["our_seat"] != win["our_seat"]:
                continue
            n = min(len(loss["farmer_actions"]), len(win["farmer_actions"]))
            farmer_match = sum(loss["farmer_actions"][i] == win["farmer_actions"][i]
                               for i in range(n))
            hands_match = sum(loss["hands_actions"][i] == win["hands_actions"][i]
                              for i in range(n))
            pairs.append({"loss": loss["episode_id"], "win": win["episode_id"],
                          "same_seat": loss["our_seat"], "farmer_match": farmer_match,
                          "hands_match": hands_match,
                          "farmer_hands_match": sum(
                              loss["farmer_actions"][i] == win["farmer_actions"][i]
                              and loss["hands_actions"][i] == win["hands_actions"][i]
                              for i in range(n)),
                          "loss_margin": loss["margin"], "win_margin": win["margin"]})
    pairs.sort(key=lambda p: (-p["farmer_hands_match"],
                              abs(abs(p["loss_margin"]) - p["win_margin"]),
                              abs(p["loss_margin"]) + p["win_margin"]))

    sha = hashlib.sha256(MAIN.read_bytes()).hexdigest()
    result = {
        "submission": audit["submission"], "main_sha256": sha,
        "replay_count": len(records),
        "outcomes": dict(Counter(r["outcome"] for r in records)),
        "market_price_model_validation": {
            "execution_model": "simultaneous_lockstep_by_order_slot",
            "single_item_no_buy_cash_reconciliation": lockstep_fit,
        },
        "episodes": [{k: v for k, v in r.items()
                      if k not in ("farmer_actions", "hands_actions")}
                     for r in records],
        "closest_same_seat_cross_outcome_pairs": pairs[:20],
        "cash_matched_revenue_checks": [
            {"episode_id": r["episode_id"], **check}
            for r in records for check in r["clean_revenue_checks"]],
    }
    output = HERE / "live_clone_margin_evidence.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print("episodes", len(records), "outcomes", result["outcomes"])
    print("main sha256", sha)
    print("best opposite-outcome same-seat pairs")
    for pair in pairs[:12]:
        print(pair)
    print("cash-vs-observed-quote checks", len(result["cash_matched_revenue_checks"]))
    print("lockstep cash reconciliation", lockstep_fit)
    checks = result["cash_matched_revenue_checks"]
    if checks:
        exact = sum(abs(row["residual_vs_quote_proxy"]) < 0.01 for row in checks)
        print("open-quote proxy exactly equals observed cash delta", exact, "/", len(checks))
        print("examples", checks[:8])
    print("wrote", output)


if __name__ == "__main__":
    main()
