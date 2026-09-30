"""Summarize the four frozen DECEM mechanism traces; makes no game calls."""

from __future__ import annotations

from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CHECKPOINT_DAYS = (3, 6, 10, 18)
ITEMS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("GOOSE", "COW", "SHEEP")


def read(policy: str, seat: int) -> dict[str, Any]:
    with gzip.open(HERE / f"{policy}-seat{seat}.json.gz", "rt", encoding="utf-8") as handle:
        return json.load(handle)


def first_paths(left: Any, right: Any, prefix: str = "", limit: int = 12) -> list[str]:
    """Return bounded differing leaf paths in stable order."""
    out: list[str] = []
    if type(left) is not type(right):
        return [prefix or "$"]
    if isinstance(left, dict):
        for key in sorted(set(left) | set(right)):
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in left or key not in right:
                out.append(path)
            elif left[key] != right[key]:
                out.extend(first_paths(left[key], right[key], path, limit - len(out)))
            if len(out) >= limit:
                break
    elif isinstance(left, list):
        if len(left) != len(right):
            out.append(f"{prefix}.length")
        for index, (a, b) in enumerate(zip(left, right)):
            if a != b:
                out.extend(first_paths(a, b, f"{prefix}[{index}]", limit - len(out)))
            if len(out) >= limit:
                break
    elif left != right:
        out.append(prefix or "$")
    return out[:limit]


def name_action(action: Any) -> str:
    if isinstance(action, list) and action:
        return str(action[0])
    return "?"


def record_map(data: dict[str, Any], player: int) -> dict[int, dict[str, Any]]:
    return {int(row["step"]): row for row in data["traces"][player]}


def tile_summary(farm: dict[str, Any]) -> dict[str, Any]:
    crops: Counter[str] = Counter()
    animals: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    for row in farm.get("tiles", []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            kind = str(tile.get("kind", "?"))
            kinds[kind] += 1
            if kind == "PLANT":
                crops[str(tile.get("crop", "?"))] += 1
            elif kind == "PASTURE":
                animals[str(tile.get("animal", "?"))] += 1
    return {
        "crops": {item: int(crops.get(item, 0)) for item in ITEMS},
        "animals": {item: int(animals.get(item, 0)) for item in ANIMALS},
        "pasture_tiles": int(kinds.get("PASTURE", 0)),
        "weed_tiles": int(kinds.get("WEED", 0)),
        "occupied_tiles": int(sum(kinds.values())),
    }


def state_at(data: dict[str, Any], candidate_seat: int, step: int, player: int) -> dict[str, Any]:
    player_record = record_map(data, player)[step]
    observation = player_record["observation"]
    farm = observation["farms"][player]
    # Each player sees their own private ledger only. Select it from that
    # player's observation so both public farms have their correct private data.
    private = observation.get("private", {}) or {}
    return {
        "cash": float(farm.get("money", 0) or 0),
        "land": list(farm.get("unlocked_quadrants", []) or []),
        "hands": farm.get("hands", []) or [],
        **tile_summary(farm),
        "shed": private.get("shed", {}) or {},
        "seeds": private.get("seeds", {}) or {},
    }


def tile_alignment(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_tiles = left.get("tiles", [])
    right_tiles = right.get("tiles", [])
    left_cells: dict[tuple[int, int], Any] = {}
    right_cells: dict[tuple[int, int], Any] = {}
    for y, row in enumerate(left_tiles):
        for x, tile in enumerate(row):
            if isinstance(tile, dict):
                left_cells[(x, y)] = tile
    for y, row in enumerate(right_tiles):
        for x, tile in enumerate(row):
            if isinstance(tile, dict):
                right_cells[(x, y)] = tile
    overlap = set(left_cells) & set(right_cells)
    same_kind = sum(left_cells[pos].get("kind") == right_cells[pos].get("kind") for pos in overlap)
    same_identity = sum(
        left_cells[pos].get("kind") == right_cells[pos].get("kind")
        and left_cells[pos].get("crop") == right_cells[pos].get("crop")
        and left_cells[pos].get("animal") == right_cells[pos].get("animal")
        for pos in overlap
    )
    exact = sum(left_cells[pos] == right_cells[pos] for pos in overlap)
    union = set(left_cells) | set(right_cells)
    return {
        "left_occupied": len(left_cells), "right_occupied": len(right_cells),
        "occupied_coordinate_overlap": len(overlap),
        "same_kind_at_overlap": int(same_kind),
        "same_crop_or_animal_identity_at_overlap": int(same_identity),
        "exact_tile_records_at_overlap": int(exact),
        "union_occupied_coordinates": len(union),
    }


def daily_events(data: dict[str, Any], candidate_seat: int) -> dict[int, dict[int, dict[str, Any]]]:
    rows: dict[int, dict[int, dict[str, Any]]] = defaultdict(dict)
    hand_counts: dict[tuple[int, int], int] = {}
    for player in (0, 1):
        for record in data["traces"][player]:
            farm = record["observation"]["farms"][player]
            hand_counts[(player, int(record["step"]))] = len(farm.get("hands", []) or [])
    def slot(day: int, player: int) -> dict[str, Any]:
        return rows[day].setdefault(player, {
            "successful_sell_receipts": 0.0,
            "sell_receipts_by_item": {},
            "market_cash_delta_by_operation": {},
            "successful_market_calls_by_operation": {},
            "harvest_commands": 0,
            "changed_harvest_commands": 0,
            "worker_nonpass_commands": 0,
            "worker_nonpass_noops": 0,
            "worker_noops_by_action": {},
        })
    for event in data["events"]:
        step = event.get("step")
        player = event.get("player")
        if step is None or player is None:
            continue
        day = int(step) // 24
        player = int(player)
        row = slot(day, player)
        if event.get("phase") in ("market_unit", "market_atomic"):
            operation = str(event.get("operation", "?"))
            if event.get("phase") == "market_unit":
                cash_delta = float(event.get("cash_delta", 0) or 0)
            else:
                cash_delta = float(event.get("cash_after", 0) or 0) - float(event.get("cash_before", 0) or 0)
            op_map = row["market_cash_delta_by_operation"]
            op_map[operation] = float(op_map.get(operation, 0) or 0) + cash_delta
            success_map = row["successful_market_calls_by_operation"]
            success_map[operation] = int(success_map.get(operation, 0)) + int(bool(event.get("success")))
            if event.get("phase") == "market_unit" and operation == "SELL" and event.get("success"):
                item = str(event.get("item", "?"))
                row["successful_sell_receipts"] += cash_delta
                item_map = row["sell_receipts_by_item"]
                item_map[item] = float(item_map.get(item, 0) or 0) + cash_delta
        elif event.get("phase") == "unit_action":
            action = event.get("action")
            kind = name_action(action)
            actor = int(event.get("actor", 0) or 0)
            if kind == "HARVEST":
                row["harvest_commands"] += 1
                row["changed_harvest_commands"] += int(bool(event.get("changed")))
            # actor 0 is the farmer; actor 1..N are actual hired hands only
            # when the pre-action observation contains that hand. Higher action
            # slots are silently ignored by the engine and are not worker work.
            if 1 <= actor <= hand_counts.get((player, int(step)), 0) and kind != "PASS":
                row["worker_nonpass_commands"] += 1
                if not event.get("changed"):
                    row["worker_nonpass_noops"] += 1
                    noop_map = row["worker_noops_by_action"]
                    noop_map[kind] = int(noop_map.get(kind, 0)) + 1
    for day_rows in rows.values():
        for row in day_rows.values():
            row["successful_sell_receipts"] = round(row["successful_sell_receipts"], 2)
            row["sell_receipts_by_item"] = {
                key: round(value, 2) for key, value in sorted(row["sell_receipts_by_item"].items())
            }
            row["market_cash_delta_by_operation"] = {
                key: round(value, 2) for key, value in sorted(row["market_cash_delta_by_operation"].items())
            }
            row["successful_market_calls_by_operation"] = dict(
                sorted(row["successful_market_calls_by_operation"].items())
            )
    return rows


def close_cash_by_day(data: dict[str, Any]) -> dict[int, dict[int, float]]:
    last_by_day: dict[int, dict[str, Any]] = {}
    for row in data["turns"]:
        day = int(row["day"])
        prev = last_by_day.get(day)
        if prev is None or (int(row["step"]), int(row["events_end"])) > (int(prev["step"]), int(prev["events_end"])):
            last_by_day[day] = row
    return {
        day: {int(player["player"]): float(player["cash"]) for player in row["players_after"]}
        for day, row in last_by_day.items()
    }


def market_totals(data: dict[str, Any]) -> dict[int, dict[str, Any]]:
    totals: dict[int, dict[str, Any]] = {
        player: {"net_cash_delta": 0.0, "cash_delta_by_operation": {},
                 "successful_calls_by_operation": {}, "sell_receipts": 0.0,
                 "sell_receipts_by_item": {}}
        for player in (0, 1)
    }
    for event in data["events"]:
        if event.get("player") is None or event.get("phase") not in ("market_unit", "market_atomic"):
            continue
        player = int(event["player"])
        row = totals[player]
        operation = str(event.get("operation", "?"))
        if event.get("phase") == "market_unit":
            delta = float(event.get("cash_delta", 0) or 0)
        else:
            delta = float(event.get("cash_after", 0) or 0) - float(event.get("cash_before", 0) or 0)
        row["net_cash_delta"] += delta
        by_op = row["cash_delta_by_operation"]
        by_op[operation] = float(by_op.get(operation, 0) or 0) + delta
        success_by_op = row["successful_calls_by_operation"]
        success_by_op[operation] = int(success_by_op.get(operation, 0)) + int(bool(event.get("success")))
        if event.get("phase") == "market_unit" and operation == "SELL" and event.get("success"):
            item = str(event.get("item", "?"))
            row["sell_receipts"] += delta
            by_item = row["sell_receipts_by_item"]
            by_item[item] = float(by_item.get(item, 0) or 0) + delta
    for row in totals.values():
        for key in ("net_cash_delta", "sell_receipts"):
            row[key] = round(row[key], 2)
        row["cash_delta_by_operation"] = {
            key: round(value, 2) for key, value in sorted(row["cash_delta_by_operation"].items())
        }
        row["successful_calls_by_operation"] = dict(sorted(row["successful_calls_by_operation"].items()))
        row["sell_receipts_by_item"] = {
            key: round(value, 2) for key, value in sorted(row["sell_receipts_by_item"].items())
        }
    return totals


def compare_seat(seat: int) -> dict[str, Any]:
    base = read("4ee", seat)
    alt = read("V43", seat)
    base_candidate = record_map(base, seat)
    alt_candidate = record_map(alt, seat)
    first_action_divergence = None
    first_state_divergence = None
    for step in sorted(set(base_candidate) & set(alt_candidate)):
        base_action = base_candidate[step]["action"]
        alt_action = alt_candidate[step]["action"]
        if first_action_divergence is None and base_action != alt_action:
            first_action_divergence = {
                "step": step,
                "path_differences": first_paths(base_action, alt_action),
                "4ee_action": base_action,
                "V43_action": alt_action,
            }
        if first_state_divergence is None:
            base_obs = base_candidate[step]["observation"]
            alt_obs = alt_candidate[step]["observation"]
            if base_obs != alt_obs:
                first_state_divergence = {
                    "step": step,
                    "path_differences": first_paths(base_obs, alt_obs),
                    "same_full_observation": False,
                }
    event_base = daily_events(base, seat)
    event_alt = daily_events(alt, seat)
    cash_base = close_cash_by_day(base)
    cash_alt = close_cash_by_day(alt)
    daily = []
    for day in range(30):
        end_step = min(24 * day + 23, 718)
        start_step = 24 * day
        close_b = cash_base.get(day, {})
        close_a = cash_alt.get(day, {})
        eb = event_base.get(day, {})
        ea = event_alt.get(day, {})
        cand_other = 1 - seat
        daily.append({
            "day": day,
            "step_start": start_step,
            "step_end": end_step,
            "4ee_cash_close_candidate": close_b.get(seat),
            "4ee_cash_close_rival": close_b.get(cand_other),
            "V43_cash_close_candidate": close_a.get(seat),
            "V43_cash_close_rival": close_a.get(cand_other),
            "4ee_candidate": eb.get(seat, {}),
            "4ee_rival": eb.get(cand_other, {}),
            "V43_candidate": ea.get(seat, {}),
            "V43_rival": ea.get(cand_other, {}),
        })

    checkpoints = []
    for day in CHECKPOINT_DAYS:
        step = day * 24
        base_obs = base_candidate[step]["observation"]
        alt_obs = alt_candidate[step]["observation"]
        p = seat
        base_farm = base_obs["farms"][p]
        alt_farm = alt_obs["farms"][p]
        base_rival_farm = base_obs["farms"][1 - p]
        alt_rival_farm = alt_obs["farms"][1 - p]
        base_state = state_at(base, seat, step, p)
        alt_state = state_at(alt, seat, step, p)
        # Rival private state is taken from the opponent route's own trace.
        base_rival_state = state_at(base, seat, step, 1 - p)
        alt_rival_state = state_at(alt, seat, step, 1 - p)
        checkpoints.append({
            "day": day,
            "step": step,
            "4ee": {"candidate": base_state, "rival": base_rival_state,
                    "shops": list(base_obs.get("town", {}).get("unlocked_shops", []))},
            "V43": {"candidate": alt_state, "rival": alt_rival_state,
                    "shops": list(alt_obs.get("town", {}).get("unlocked_shops", []))},
            "compatibility": {
                "full_candidate_observation_equal": base_obs == alt_obs,
                "candidate_farm_equal": base_farm == alt_farm,
                "rival_public_farm_equal": base_rival_farm == alt_rival_farm,
                "candidate_cash_equal": base_state["cash"] == alt_state["cash"],
                "candidate_land_equal": base_state["land"] == alt_state["land"],
                "candidate_hands_equal": base_state["hands"] == alt_state["hands"],
                "candidate_private_shed_equal": base_state["shed"] == alt_state["shed"],
                "candidate_private_seeds_equal": base_state["seeds"] == alt_state["seeds"],
                "rival_private_shed_equal": base_rival_state["shed"] == alt_rival_state["shed"],
                "rival_private_seeds_equal": base_rival_state["seeds"] == alt_rival_state["seeds"],
                "shops_equal": base_obs.get("town", {}).get("unlocked_shops") == alt_obs.get("town", {}).get("unlocked_shops"),
                "candidate_tile_alignment": tile_alignment(base_farm, alt_farm),
                "rival_tile_alignment": tile_alignment(base_rival_farm, alt_rival_farm),
                "candidate_observation_differences": first_paths(base_obs, alt_obs, limit=20),
            },
        })
    return {
        "candidate_seat": seat,
        "margins": {"4ee": float(base["margin"]), "V43": float(alt["margin"])},
        "rewards": {
            "4ee_candidate": float(base["candidate_reward"]),
            "4ee_rival": float(base["opponent_reward"]),
            "V43_candidate": float(alt["candidate_reward"]),
            "V43_rival": float(alt["opponent_reward"]),
        },
        "market_cash_flows": {
            policy: {
                "candidate": market_totals(data)[seat],
                "rival": market_totals(data)[1 - seat],
            }
            for policy, data in (("4ee", base), ("V43", alt))
        },
        "first_action_divergence": first_action_divergence,
        "first_observation_divergence": first_state_divergence,
        "daily": daily,
        "switch_checkpoints": checkpoints,
    }


def main() -> None:
    result = {
        "interpretation": "Read-only summaries of the four already-scored native fixed-tape DECEM traces; no new policy outcome test.",
        "fixture": {
            "team": "DECEM", "episode_id": 114267880, "seed": 1390733823,
            "action_sha256": "a326e4f9e779ce21762e8cac5a0058884a1676271f296bf4c2291180b0175226",
            "replay_sha256": "1d6a1d7ce66a2e07bd1576528e930ac5f13777fdb88f673eea3aa0a4c34c8072",
            "engine_version": "1.32.7",
            "seat_note": "Candidate seat 0/1 versus the same saved DECEM source-seat-1 actions; fixed-tape diagnostic only.",
        },
        "seats": [compare_seat(seat) for seat in (0, 1)],
    }
    out = HERE / "trace_analysis.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "output": str(out.resolve()),
        "seats": [{
            "seat": row["candidate_seat"],
            "margins": row["margins"],
            "first_action_step": row["first_action_divergence"]["step"] if row["first_action_divergence"] else None,
            "first_observation_step": row["first_observation_divergence"]["step"] if row["first_observation_divergence"] else None,
            "checkpoint_compatibility": [checkpoint["compatibility"] for checkpoint in row["switch_checkpoints"]],
        } for row in result["seats"]],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
