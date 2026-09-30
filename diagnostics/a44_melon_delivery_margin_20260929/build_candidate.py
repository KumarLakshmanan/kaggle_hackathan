"""Build the isolated, hash-pinned a44 melon-delivery candidate; do not execute it."""
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "diagnostics" / "adaptive_donor_pair_repair_20260928" / "candidate_combined.py"
OUTPUT = Path(__file__).resolve().parent / "candidate_a44_melon_delivery_v2.py"
EXPECTED_SOURCE_SHA256 = "a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f"


APPEND = r'''

# Isolated wrapper: frozen step-713 selector plus a player-keyed route latch.
import copy as _a44_melon_copy

_A44_MELON_PARENT = agent
_A44_MELON_COUNTERS = {}  # Cumulative diagnostics only; never used to choose actions.
_A44_MELON_ROUTE_STATE = {}  # Keyed by observation.player; reset at step 0 and cleared after step 716.


def _a44_melon_note(name):
    _A44_MELON_COUNTERS[name] = _A44_MELON_COUNTERS.get(name, 0) + 1
    telemetry = getattr(_A44_MELON_PARENT, "telemetry", None)
    if isinstance(telemetry, dict):
        telemetry["melon_delivery_" + name] = _A44_MELON_COUNTERS[name]


def _a44_melon_cfg(configuration, name):
    if isinstance(configuration, dict):
        if name not in configuration:
            return None
        value = configuration[name]
    else:
        if configuration is None or not hasattr(configuration, name):
            return None
        value = getattr(configuration, name)
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _a44_melon_pass(action, hand_index):
    hands = action.get("hands") if isinstance(action, dict) else None
    if isinstance(hands, list) and 0 <= hand_index < len(hands):
        hands[hand_index] = ["PASS"]


def _a44_melon_delivery_apply(observation, action, configuration=None):
    """Apply the frozen route with a per-player latch and fail-closed guards."""
    if not isinstance(observation, dict) or not isinstance(action, dict):
        return action
    try:
        step = int(observation.get("step", -1))
        player = int(observation.get("player", -1))
    except (TypeError, ValueError, OverflowError):
        return action

    if step == 0:
        _A44_MELON_ROUTE_STATE.pop(player, None)
        return action

    route = _A44_MELON_ROUTE_STATE.get(player)
    if route is not None and step != route.get("next_step"):
        _A44_MELON_ROUTE_STATE.pop(player, None)
        _a44_melon_note("guard_unexpected_step")
        return action

    if step not in (713, 714, 715, 716):
        return action

    expected = {713: (17, [1, 4]), 714: (18, [2, 4]), 715: (19, [3, 4]), 716: (20, [4, 4])}
    expected_hour, expected_position = expected[step]
    try:
        if int(observation.get("day", -1)) != 29 or int(observation.get("hour", -1)) != expected_hour:
            if route is not None:
                _a44_melon_pass(action, int(route["hand_index"]))
                _A44_MELON_ROUTE_STATE.pop(player, None)
                _a44_melon_note("guard_schedule_mismatch")
            return action

        board_size = _a44_melon_cfg(configuration, "boardSize")
        farm = observation["farms"][player]
        hand_positions = farm.get("hands", [])
        private = observation["private"]
        inventories = private["inventories"]
        hand_actions = action.get("hands")
        if not isinstance(hand_actions, list) or len(hand_actions) != len(hand_positions):
            _a44_melon_note("guard_action_shape")
            if route is not None:
                _a44_melon_pass(action, int(route["hand_index"]))
                _A44_MELON_ROUTE_STATE.pop(player, None)
            return action
        if len(inventories) < len(hand_positions) + 1:
            _a44_melon_note("guard_inventory_shape")
            if route is not None:
                _a44_melon_pass(action, int(route["hand_index"]))
                _A44_MELON_ROUTE_STATE.pop(player, None)
            return action

        if step == 713:
            if route is not None:
                _A44_MELON_ROUTE_STATE.pop(player, None)
                _a44_melon_note("guard_duplicate_trigger")
                return action
            if board_size != 10:
                _a44_melon_note("guard_board_size")
                return action
            shed_capacity = _a44_melon_cfg(configuration, "shedCapacity")
            max_orders = _a44_melon_cfg(configuration, "maxMarketOrdersPerTurn")
            if shed_capacity is None or max_orders is None or max_orders < 1:
                _a44_melon_note("guard_missing_config")
                return action
            if int(observation["market"]["prices"].get("MELON", 0)) < 100:
                _a44_melon_note("guard_quote_floor")
                return action

            access = ((4, 4), (5, 4), (4, 5), (5, 5))
            matches = []
            for i, position in enumerate(hand_positions):
                inventory = inventories[i + 1]
                if not isinstance(inventory, dict) or list(position) != [1, 4]:
                    continue
                if hand_actions[i] != ["WATER"] or int(inventory.get("MELON", 0)) < 12:
                    continue
                x, y = int(position[0]), int(position[1])
                distance = min(abs(x - sx) + abs(y - sy) for sx, sy in access)
                if distance <= 3:
                    matches.append(i)
            if len(matches) != 1:
                _a44_melon_note("guard_nonunique_trigger" if len(matches) > 1 else "guard_no_match_trigger")
                return action

            hand_index = matches[0]
            inventory = inventories[hand_index + 1]
            shed = private.get("shed")
            if not isinstance(shed, dict):
                _a44_melon_note("guard_missing_shed")
                return action
            if shed_capacity < sum(int(v) for v in shed.values()) + sum(int(v) for v in inventory.values()):
                _a44_melon_note("guard_initial_capacity")
                return action
            hand_actions[hand_index] = ["EAST"]
            _A44_MELON_ROUTE_STATE[player] = {"hand_index": hand_index, "next_step": 714}
            _a44_melon_note("activated")
            return action

        # Continuations require the latch created only by the full step713 selector.
        if route is None:
            return action
        hand_index = int(route["hand_index"])
        if (
            board_size != 10 or hand_index < 0 or hand_index >= len(hand_positions)
            or hand_index + 1 >= len(inventories)
            or list(hand_positions[hand_index]) != expected_position
            or inventories[hand_index + 1] != {"MELON": 12, "FERTILIZER": 1}
        ):
            _a44_melon_pass(action, hand_index)
            _A44_MELON_ROUTE_STATE.pop(player, None)
            _a44_melon_note("guard_continuation_state")
            return action

        if step in (714, 715):
            hand_actions[hand_index] = ["EAST"]
            route["next_step"] = step + 1
            return action

        # Step716: exact projected position/inventory, with capacity/order safety.
        shed = private.get("shed")
        if not isinstance(shed, dict):
            _a44_melon_pass(action, hand_index)
            _A44_MELON_ROUTE_STATE.pop(player, None)
            _a44_melon_note("guard_missing_shed_step716")
            return action
        if board_size != 10:
            _a44_melon_pass(action, hand_index)
            _A44_MELON_ROUTE_STATE.pop(player, None)
            _a44_melon_note("guard_missing_board_size_step716")
            return action

        inventory = inventories[hand_index + 1]
        shed_capacity = _a44_melon_cfg(configuration, "shedCapacity")
        max_orders = _a44_melon_cfg(configuration, "maxMarketOrdersPerTurn")
        shed_count = sum(int(v) for v in shed.values())
        drop_count = sum(int(v) for v in inventory.values())
        own_units = [action.get("farmer", [])] + hand_actions
        competing_deposit = any(
            j != hand_index + 1 and isinstance(unit, list) and unit and unit[0] in ("DROP", "PLACE")
            for j, unit in enumerate(own_units)
        )
        room_for_drop = (
            shed_capacity is not None and shed_capacity >= 0
            and shed_count + drop_count <= shed_capacity
        )
        if not room_for_drop or competing_deposit:
            hand_actions[hand_index] = ["PASS"]
            _A44_MELON_ROUTE_STATE.pop(player, None)
            _a44_melon_note("guard_pass_competing_deposit" if competing_deposit else "guard_pass_capacity")
            return action

        orders = action.get("market")
        order_available = (
            isinstance(orders, list) and max_orders is not None
            and max_orders >= 1 and len(orders) + 1 <= max_orders
        )
        duplicate_sell = isinstance(orders, list) and any(
            isinstance(order, list) and len(order) >= 2 and order[0] == "SELL" and order[1] == "MELON"
            for order in orders
        )
        hand_actions[hand_index] = ["DROP"]
        if order_available and not duplicate_sell:
            orders.append(["SELL", "MELON", 12])
            _a44_melon_note("drop_sell_step716")
        elif duplicate_sell:
            _a44_melon_note("guard_drop_only_duplicate_sell")
        else:
            _a44_melon_note("guard_drop_only_order_capacity")
        _A44_MELON_ROUTE_STATE.pop(player, None)
        return action
    except (KeyError, IndexError, TypeError, ValueError, OverflowError):
        if route is not None:
            _a44_melon_pass(action, int(route.get("hand_index", -1)))
            _A44_MELON_ROUTE_STATE.pop(player, None)
        _a44_melon_note("guard_exception_step" + str(step))
        return action


def agent(observation, configuration=None):
    if isinstance(observation, dict) and int(observation.get("step", -1)) == 0:
        try:
            _A44_MELON_ROUTE_STATE.pop(int(observation.get("player", -1)), None)
        except (TypeError, ValueError, OverflowError):
            pass
    action = _a44_melon_copy.deepcopy(_A44_MELON_PARENT(observation, configuration))
    return _a44_melon_delivery_apply(observation, action, configuration)


agent.telemetry = _A44_MELON_PARENT.telemetry
'''


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"a44 source SHA mismatch: {source_sha}")
    candidate_text = source_bytes.decode("utf-8") + APPEND
    compile(candidate_text, str(OUTPUT), "exec")
    OUTPUT.write_text(candidate_text, encoding="utf-8", newline="\n")
    candidate_sha = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print(f"source_sha256={source_sha}")
    print(f"candidate_path={OUTPUT}")
    print(f"candidate_sha256={candidate_sha}")


if __name__ == "__main__":
    main()
