"""Validation-only live-state task matcher for the Kaggriculture agent.

The production agent remains the decision-maker.  This wrapper changes only a
unit command that is PASS or demonstrably has no effect under the deterministic
unit-action rules embedded in main.py.  It then assigns currently actionable
work from the acting player's own farm, using visible positions and that
player's private per-unit inventory.  Market orders and all other output fields
are passed through unchanged.

The task-discovery, shortest-path, and unique-worker/task assignment pattern is
inspired by the statically inspected Harvest Pulse notebook.  No notebook code
is executed here, and this experiment never reads route hashes, seeds,
episode identifiers, or opponent identity.
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
_BASE_MODULE_NAME = f"{__name__}_base"
_SPEC = importlib.util.spec_from_file_location(_BASE_MODULE_NAME, ROOT / "main.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("could not load main.py")
_BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BASE
try:
    _SPEC.loader.exec_module(_BASE)
except Exception:
    sys.modules.pop(_SPEC.name, None)
    raise
sys.modules.pop(_SPEC.name, None)

_BASE_AGENT = getattr(_BASE, "agent", None)
_UNIT_MODEL = getattr(_BASE, "_UNIT_NS", None)
if not callable(_BASE_AGENT) or not isinstance(_UNIT_MODEL, dict):
    raise RuntimeError("main.py agent or deterministic unit model is unavailable")

_APPLY_UNIT_ACTION = _UNIT_MODEL.get("_apply_unit_action")
_FARMER_MOVES = _UNIT_MODEL.get("FARMER_MOVES", {})
_CROPS = _UNIT_MODEL.get("CROPS", {})
_ANIMALS = _UNIT_MODEL.get("ANIMALS", {})
if not callable(_APPLY_UNIT_ACTION) or not isinstance(_FARMER_MOVES, dict):
    raise RuntimeError("main.py deterministic unit-action rules are incomplete")

_MOVE_DELTAS = {
    "NORTH": (0, -1),
    "EAST": (1, 0),
    "SOUTH": (0, 1),
    "WEST": (-1, 0),
}
_TASK_ACTIONS = frozenset(
    {
        "PLANT",
        "WATER",
        "HARVEST",
        "DIG",
        "FERTILIZE",
        "FEED",
        "CARE",
        "COLLECT_FERTILIZER",
        "BUILD_COOP",
        "BUILD_PASTURE",
        "PLACE",
    }
)

_TELEMETRY = {
    "live_taskmatch_calls": 0,
    "live_taskmatch_pass_interventions": 0,
    "live_taskmatch_stale_interventions": 0,
    "live_taskmatch_assigned_tasks": 0,
    "live_taskmatch_unmatched_units": 0,
    "live_taskmatch_errors": 0,
}
_REPLACE_STALE_COMMANDS = False


def _command_tokens(command: Any) -> list[str]:
    if isinstance(command, str):
        values = command.strip().split()
    elif isinstance(command, (list, tuple)):
        values = list(command)
    else:
        return []
    return [str(value).upper() for value in values]


def _position(farm: dict[str, Any], unit_index: int) -> tuple[int, int] | None:
    raw = farm.get("farmer") if unit_index == 0 else (
        (farm.get("hands", []) or [])[unit_index - 1]
        if unit_index - 1 < len(farm.get("hands", []) or [])
        else None
    )
    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
        return None
    try:
        return int(raw[0]), int(raw[1])
    except (TypeError, ValueError, OverflowError):
        return None


def _dry_run_has_effect(
    farm: dict[str, Any],
    private: dict[str, Any],
    unit_index: int,
    command: Any,
    board_size: int,
    day: int,
    turns_per_day: int,
    shed_capacity: int,
) -> bool:
    """Use the embedded exact action semantics on clones; never mutate obs."""
    farm_copy = copy.deepcopy(farm)
    private_copy = copy.deepcopy(private)
    _APPLY_UNIT_ACTION(
        farm_copy,
        private_copy,
        unit_index,
        command,
        board_size,
        day,
        turns_per_day,
        shed_capacity,
    )
    return farm_copy != farm or private_copy != private


def _noop_reason(
    farm: dict[str, Any],
    private: dict[str, Any],
    unit_index: int,
    command: Any,
    board_size: int,
    day: int,
    turns_per_day: int,
    shed_capacity: int,
) -> str | None:
    """Return why the base command is a no-op, or None if it has an effect."""
    tokens = _command_tokens(command)
    if not tokens or tokens[0] == "PASS":
        return "pass"

    op = tokens[0]
    if op in _FARMER_MOVES and isinstance(command, list):
        pos = _position(farm, unit_index)
        delta = _MOVE_DELTAS.get(op)
        if pos is None or delta is None:
            return "stale"
        nx, ny = pos[0] + delta[0], pos[1] + delta[1]
        return None if 0 <= nx < board_size and 0 <= ny < board_size else "stale"

    return (
        None
        if _dry_run_has_effect(
            farm,
            private,
            unit_index,
            command,
            board_size,
            day,
            turns_per_day,
            shed_capacity,
        )
        else "stale"
    )


def _live_tasks(
    farm: dict[str, Any],
    day: int,
    inactive_units: list[dict[str, Any]],
    private: dict[str, Any],
    remaining_turns: int,
) -> list[dict[str, Any]]:
    """Derive one highest-value, currently feasible task per occupied tile."""
    tiles = farm.get("tiles", []) or []
    best_by_position: dict[tuple[int, int], dict[str, Any]] = {}

    def offer(x: int, y: int, command: list[Any], priority: int, required: str | None = None) -> None:
        position = (x, y)
        task = {
            "position": position,
            "command": command,
            "priority": priority,
            "required_item": required,
        }
        old = best_by_position.get(position)
        if old is None or priority > old["priority"]:
            best_by_position[position] = task

    for y, row in enumerate(tiles):
        if not isinstance(row, (list, tuple)):
            continue
        for x, tile in enumerate(row):
            if tile == "LOCKED" or not isinstance(tile, dict):
                continue

            kind = tile.get("kind")
            if kind == "WEED":
                offer(x, y, ["DIG"], 10)
                continue

            if kind == "PLANT":
                crop = str(tile.get("crop", "")).upper()
                crop_rule = _CROPS.get(crop)
                if not isinstance(crop_rule, dict):
                    continue
                try:
                    age = max(0, int(day) - int(tile.get("planted_day", day)))
                    amount = max(0, int(tile.get("yield_units", 0)))
                    max_yield = max(0, int(crop_rule.get("max_yield", 0)))
                    first_yield_day = max(0, int(crop_rule.get("first_yield_day", 0)))
                    max_yield_day = max(0, int(crop_rule.get("max_yield_day", 0)))
                    missed_days = max(0, int(tile.get("consecutive_unwatered", 0)))
                except (TypeError, ValueError, OverflowError):
                    continue

                if not tile.get("watered_today", False):
                    if missed_days >= 1:
                        # Two missed daily refreshes kill the plant; watering
                        # after one missed day is the time-critical repair.
                        offer(x, y, ["WATER"], 120)
                    elif not bool(crop_rule.get("ongoing", False)):
                        window_start = (max_yield_day + 1) // 2
                        fertilized = int(tile.get("fertilized_until_day", -1)) >= day
                        bonus = 2 if fertilized else 1
                        if (
                            window_start <= age <= max_yield_day
                            and min(max_yield, amount + bonus) > amount
                        ):
                            # Keep a one-time crop growing when watering now
                            # increases its yield; the next turn can harvest.
                            offer(x, y, ["WATER"], 85)

                if amount > 0 and age >= first_yield_day:
                    harvest_priority = 95 if max_yield > 0 and amount >= max_yield else 75
                    offer(x, y, ["HARVEST"], harvest_priority)
                continue

            animal = str(tile.get("animal", "")).upper()
            if animal not in _ANIMALS:
                continue

            animal_rule = _ANIMALS[animal]
            try:
                held = max(0, int(tile.get("yield_units", 0)))
                max_held = max(0, int(animal_rule.get("max_held", 0)))
                missed_feed_days = max(0, int(tile.get("consecutive_unfed", 0)))
            except (TypeError, ValueError, OverflowError):
                continue

            if not tile.get("fed_today", False):
                can_reach_with_wheat = any(
                    int(_inventory_for(private, unit["unit_index"]).get("WHEAT", 0)) > 0
                    and unit["position"] is not None
                    and _route(unit["position"], (x, y))[0] + 1 <= remaining_turns
                    for unit in inactive_units
                )
                if can_reach_with_wheat:
                    offer(x, y, ["FEED"], 115 if missed_feed_days >= 1 else 70, "WHEAT")
            if held > 0:
                harvest_priority = 100 if max_held > 0 and held >= max_held else 80
                offer(x, y, ["HARVEST"], harvest_priority)
            if tile.get("fed_today", False) and not tile.get("cared_today", False):
                offer(x, y, ["CARE"], 40)
            if tile.get("fertilizer_available", False):
                offer(x, y, ["COLLECT_FERTILIZER"], 25)

    return sorted(
        best_by_position.values(),
        key=lambda task: (
            task["position"][1],
            task["position"][0],
            task["command"][0],
        ),
    )


def _route(source: tuple[int, int], target: tuple[int, int]) -> tuple[int, list[str] | None]:
    """A shortest monotone route; all in-board tiles, including LOCKED, pass."""
    dx = target[0] - source[0]
    dy = target[1] - source[1]
    distance = abs(dx) + abs(dy)
    if distance == 0:
        return 0, None
    if dx > 0:
        return distance, ["EAST"]
    if dx < 0:
        return distance, ["WEST"]
    if dy > 0:
        return distance, ["SOUTH"]
    return distance, ["NORTH"]


def _inventory_for(private: dict[str, Any], unit_index: int) -> dict[str, Any]:
    inventories = private.get("inventories", []) or []
    if unit_index >= len(inventories) or not isinstance(inventories[unit_index], dict):
        return {}
    return inventories[unit_index]


def _reserve_tasks(
    farm: dict[str, Any],
    task_positions: set[tuple[int, int]],
    unit_rows: list[dict[str, Any]],
    width: int,
    height: int,
) -> set[tuple[int, int]]:
    """Avoid duplicating a valid unit already acting on or moving onto a task."""
    reserved: set[tuple[int, int]] = set()
    for unit in unit_rows:
        if unit["reason"] is not None:
            continue
        position = unit["position"]
        if position is None:
            continue
        op = unit["tokens"][0] if unit["tokens"] else ""
        if op in _TASK_ACTIONS and position in task_positions:
            reserved.add(position)
        delta = _MOVE_DELTAS.get(op)
        if delta is not None:
            destination = (position[0] + delta[0], position[1] + delta[1])
            if (
                0 <= destination[0] < width
                and 0 <= destination[1] < height
                and destination in task_positions
            ):
                reserved.add(destination)
    return reserved


def _assign(
    inactive_units: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    private: dict[str, Any],
    width: int,
    height: int,
    remaining_turns: int,
) -> dict[int, list[str]]:
    """Minimum-cost unique task assignment, maximizing useful urgency first."""
    worker_count = len(inactive_units)
    if worker_count == 0 or not tasks:
        return {}

    pairs: dict[tuple[int, int], tuple[int, list[str]]] = {}
    for task_index, task in enumerate(tasks):
        target = task["position"]
        for worker_index, unit in enumerate(inactive_units):
            source = unit["position"]
            if source is None:
                continue
            required_item = task.get("required_item")
            if required_item and int(_inventory_for(private, unit["unit_index"]).get(required_item, 0)) <= 0:
                continue
            distance, first_move = _route(source, target)
            # Arrival and execution must fit before today's unit reset.
            if distance + 1 > remaining_turns:
                continue
            command = task["command"] if distance == 0 else first_move
            if command is None:
                continue
            tie = target[1] * width + target[0]
            cost = -int(task["priority"]) * 10000 + distance * 100 + tie
            pairs[(worker_index, task_index)] = (cost, command)

    if not pairs:
        return {}

    if worker_count <= 10:
        # Bitmask dynamic programming mirrors the donor's global assignment,
        # while restricting it to workers whose original command is a no-op.
        empty = tuple([-1] * worker_count)
        states: dict[int, tuple[int, tuple[int, ...]]] = {0: (0, empty)}
        for task_index in range(len(tasks)):
            updated = dict(states)
            for mask, (total_cost, assignment) in states.items():
                for worker_index in range(worker_count):
                    if mask & (1 << worker_index):
                        continue
                    pair = pairs.get((worker_index, task_index))
                    if pair is None:
                        continue
                    next_mask = mask | (1 << worker_index)
                    next_cost = total_cost + pair[0]
                    chosen = list(assignment)
                    chosen[worker_index] = task_index
                    next_assignment = tuple(chosen)
                    current = updated.get(next_mask)
                    if current is None or (next_cost, next_assignment) < current:
                        updated[next_mask] = (next_cost, next_assignment)
            states = updated
        _, (_, best_assignment) = min(
            states.items(),
            key=lambda item: (
                item[1][0],
                -item[0].bit_count(),
                item[1][1],
            ),
        )
        result = {}
        for worker_index, task_index in enumerate(best_assignment):
            pair = pairs.get((worker_index, task_index)) if task_index >= 0 else None
            if pair is not None:
                result[inactive_units[worker_index]["unit_index"]] = list(pair[1])
        return result

    # Unusually large hired crews use a bounded deterministic greedy fallback.
    edges = sorted(
        (
            cost,
            worker_index,
            task_index,
            command,
        )
        for (worker_index, task_index), (cost, command) in pairs.items()
    )
    used_workers: set[int] = set()
    used_tasks: set[int] = set()
    result = {}
    for _, worker_index, task_index, command in edges:
        if worker_index in used_workers or task_index in used_tasks:
            continue
        used_workers.add(worker_index)
        used_tasks.add(task_index)
        result[inactive_units[worker_index]["unit_index"]] = list(command)
    return result


def _replacement_actions(
    action: dict[str, Any],
    observation: dict[str, Any],
    configuration: Any,
) -> tuple[dict[str, Any], int, int, int]:
    farms = observation.get("farms", []) or []
    player = int(observation.get("player", 0))
    if player < 0 or player >= len(farms) or not isinstance(farms[player], dict):
        return action, 0, 0, 0
    farm = farms[player]
    private = observation.get("private", {}) or {}
    if not isinstance(private, dict):
        return action, 0, 0, 0

    tiles = farm.get("tiles", []) or []
    if not isinstance(tiles, (list, tuple)) or not tiles:
        return action, 0, 0, 0
    height = len(tiles)
    width = max((len(row) for row in tiles if isinstance(row, (list, tuple))), default=0)
    config = configuration if isinstance(configuration, dict) else {}
    board_size = int(config.get("boardSize", height))
    turns_per_day = max(1, int(config.get("turnsPerDay", 24)))
    shed_capacity = max(0, int(config.get("shedCapacity", 100)))
    day = max(0, int(observation.get("day", 0)))
    hour = max(0, int(observation.get("hour", int(observation.get("step", 0)) % turns_per_day)))
    remaining_turns = max(0, turns_per_day - hour)

    raw_hands = action.get("hands", [])
    if not isinstance(raw_hands, (list, tuple)):
        raise TypeError("main agent returned non-list hands actions")
    raw_hands = list(raw_hands)
    farm_hands = list(farm.get("hands", []) or [])
    unit_count = 1 + len(farm_hands)
    unit_rows: list[dict[str, Any]] = []
    for unit_index in range(unit_count):
        if unit_index == 0:
            command = action.get("farmer", ["PASS"])
        else:
            hand_index = unit_index - 1
            command = raw_hands[hand_index] if hand_index < len(raw_hands) else ["PASS"]
        reason = _noop_reason(
            farm,
            private,
            unit_index,
            command,
            board_size,
            day,
            turns_per_day,
            shed_capacity,
        )
        unit_rows.append(
            {
                "unit_index": unit_index,
                "command": command,
                "tokens": _command_tokens(command),
                "reason": reason,
                "position": _position(farm, unit_index),
            }
        )

    # The initial smoke showed that replacing stale-but-intentional commands
    # can disrupt the scheduled plan.  Keep this ablation conservative: only
    # explicit PASS actions are eligible unless a future experiment enables
    # stale-command replacement after separate evidence.
    inactive_units = [
        unit
        for unit in unit_rows
        if unit["reason"] == "pass"
        or (_REPLACE_STALE_COMMANDS and unit["reason"] == "stale")
    ]
    if not inactive_units or remaining_turns <= 0:
        return action, 0, 0, len(inactive_units)

    tasks = _live_tasks(farm, day, inactive_units, private, remaining_turns)
    task_positions = {task["position"] for task in tasks}
    reserved = _reserve_tasks(farm, task_positions, unit_rows, width, height)
    tasks = [task for task in tasks if task["position"] not in reserved]
    replacements = _assign(
        inactive_units,
        tasks,
        private,
        width,
        height,
        remaining_turns,
    )
    if not replacements:
        return action, 0, 0, len(inactive_units)

    changed = dict(action)
    stale_count = 0
    pass_count = 0
    updated_hands = list(raw_hands)
    for unit_index, command in replacements.items():
        unit = unit_rows[unit_index]
        if unit["reason"] == "pass":
            pass_count += 1
        else:
            stale_count += 1
        if unit_index == 0:
            changed["farmer"] = list(command)
        else:
            hand_index = unit_index - 1
            while len(updated_hands) <= hand_index:
                updated_hands.append(["PASS"])
            updated_hands[hand_index] = list(command)
    if replacements and "hands" in action:
        changed["hands"] = updated_hands
    elif replacements and len(replacements) > 0 and len(unit_rows) > 1:
        changed["hands"] = updated_hands
    # No market order or unrelated action field is modified.
    return changed, pass_count, stale_count, len(inactive_units) - len(replacements)


def agent(observation: dict[str, Any], configuration: Any = None) -> Any:
    try:
        if int(observation.get("step", -1)) == 0:
            for key in _TELEMETRY:
                _TELEMETRY[key] = 0
    except (AttributeError, TypeError, ValueError, OverflowError):
        pass

    base_action = _BASE_AGENT(observation, configuration)
    _TELEMETRY["live_taskmatch_calls"] += 1
    if not isinstance(base_action, dict) or not isinstance(observation, dict):
        _TELEMETRY["live_taskmatch_errors"] += 1
        return base_action

    try:
        updated, pass_count, stale_count, unmatched_count = _replacement_actions(
            base_action,
            observation,
            configuration,
        )
    except Exception:
        # Fail closed: keep main.py's complete original action, especially its
        # market orders and safety-layer decisions.
        _TELEMETRY["live_taskmatch_errors"] += 1
        return base_action

    _TELEMETRY["live_taskmatch_pass_interventions"] += pass_count
    _TELEMETRY["live_taskmatch_stale_interventions"] += stale_count
    _TELEMETRY["live_taskmatch_assigned_tasks"] += pass_count + stale_count
    _TELEMETRY["live_taskmatch_unmatched_units"] += unmatched_count
    return updated


agent.telemetry = _TELEMETRY
