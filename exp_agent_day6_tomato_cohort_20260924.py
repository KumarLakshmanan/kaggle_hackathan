"""Bounded day-6 strawberry-to-tomato cohort sidecar for local experiments.

The parent policy is loaded from the neighboring ``main.py`` at runtime. This
sidecar changes only already-planned day-6 seed purchases/plant commands after
an observation-only trigger. Tomato seed inventory is read from the observation
before changing PLANT commands; same-turn purchases are never treated as ready.
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path
from typing import Any


MAX_COHORT_UNITS = 8
TOMATO_BASE_QUOTE = 60
TOMATO_DEMAND_SHOPS = {"PIZZA_SHOP", "FARMERS_MARKET"}
STRAWBERRY_DEMAND_SHOPS = {
    "SMOOTHIE_SHOP",
    "ICE_CREAM_SHOP",
    "BRUNCH_SPOT",
    "FARMERS_MARKET",
}

_TELEMETRY = {
    "eligible": 0,
    "seed_swaps": 0,
    "confirmed_seed_units": 0,
    "plant_commands_swapped": 0,
    "confirmed_plants": 0,
    # Units added to an existing tomato SELL order or requested by a new one;
    # actual market execution remains subject to the engine's market rules.
    "tomato_sales": 0,
    "errors": 0,
}
_STATE: dict[int, dict[str, Any]] = {}


def _load_parent_module():
    parent_path = Path(__file__).resolve().with_name("main.py")
    if not parent_path.is_file():
        raise FileNotFoundError(f"Expected parent policy at {parent_path}")
    module_name = f"{__name__}_dynamic_main"
    spec = importlib.util.spec_from_file_location(module_name, parent_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create an import spec for {parent_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    if not callable(getattr(module, "agent", None)):
        sys.modules.pop(module_name, None)
        raise AttributeError(f"{parent_path} does not expose a callable agent")
    return module


_PARENT_MODULE = _load_parent_module()
_PARENT_AGENT = _PARENT_MODULE.agent


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def _reset_telemetry() -> None:
    _STATE.clear()
    for key in _TELEMETRY:
        _TELEMETRY[key] = 0


def _tile_at(board: Any, pos: Any) -> Any:
    try:
        x, y = _int(pos[0], -1), _int(pos[1], -1)
        return board[y][x]
    except (TypeError, IndexError):
        return None


def _confirmed_tomato_site(observation: dict[str, Any], record: dict[str, Any]) -> bool:
    try:
        seat = _int(observation.get("player", 0))
        farm = (observation.get("farms") or [])[seat]
        tile = _tile_at(farm.get("tiles") or [], record["pos"])
        return (
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and tile.get("crop") == "TOMATO"
            and _int(tile.get("planted_day"), -1) == record["day"]
        )
    except (IndexError, TypeError, KeyError):
        return False


def _new_state() -> dict[str, Any]:
    return {
        "last_step": -1,
        "eligible": False,
        "seed_swap_units": 0,
        "confirmed_seed_units": 0,
        "plant_commands_swapped": 0,
        "confirmed_plant_count": 0,
        "previous_seed_balance": 0,
        "previous_converted_buy": 0,
        "previous_native_tomato_buy": False,
        "pending_tomato_plants": [],
    }


def _reconcile_previous_turn(
    observation: dict[str, Any], state: dict[str, Any], current_tomato_seeds: int
) -> None:
    if state["last_step"] < 0 or _int(observation.get("step", -1)) != state["last_step"] + 1:
        return

    confirmed_sites = [
        record
        for record in state["pending_tomato_plants"]
        if _confirmed_tomato_site(observation, record)
    ]
    all_planted = len(confirmed_sites)
    cohort_planted = sum(bool(record["swapped"]) for record in confirmed_sites)
    if cohort_planted:
        state["confirmed_plant_count"] += cohort_planted
        _TELEMETRY["confirmed_plants"] += cohort_planted

    converted_request = _int(state["previous_converted_buy"])
    if converted_request > 0 and not state["previous_native_tomato_buy"]:
        # Unit commands resolve before the market. Add confirmed TOMATO planting
        # consumption back to the observed seed delta to infer executed buys.
        net_seed_purchase = (
            current_tomato_seeds
            - _int(state["previous_seed_balance"])
            + all_planted
        )
        confirmed_buys = min(converted_request, max(0, net_seed_purchase))
        if confirmed_buys:
            state["confirmed_seed_units"] += confirmed_buys
            _TELEMETRY["confirmed_seed_units"] += confirmed_buys


def _triggered(observation: dict[str, Any]) -> bool:
    town = observation.get("town") or {}
    shops = list(town.get("unlocked_shops") or [])
    market = observation.get("market") or {}
    inventory = market.get("inventory") or {}
    quotes = market.get("prices") or {}
    tomato_instances = sum(shop in TOMATO_DEMAND_SHOPS for shop in shops[:2])
    has_strawberry_demand = any(shop in STRAWBERRY_DEMAND_SHOPS for shop in shops)
    observed_tomato_inventory = _int(inventory.get("TOMATO"), 10_000)
    observed_tomato_quote = _int(quotes.get("TOMATO"), 0)
    return (
        tomato_instances >= 2
        and not has_strawberry_demand
        and observed_tomato_inventory < 10_000
        and observed_tomato_quote > TOMATO_BASE_QUOTE
    )


def _order_cap(configuration: Any) -> int:
    cfg = configuration if isinstance(configuration, dict) else {}
    cap = _int(cfg.get("maxMarketOrdersPerTurn", 10), 10)
    return max(0, cap)


def _rewrite_seed_purchases(
    market_orders: list[list[Any]], state: dict[str, Any], order_cap: int
) -> int:
    if any(
        isinstance(order, (list, tuple))
        and len(order) >= 3
        and order[:2] == ["BUY_SEED", "TOMATO"]
        for order in market_orders
    ):
        # Keep converted purchase confirmation attributable to these swaps.
        return 0

    remaining = MAX_COHORT_UNITS - _int(state["seed_swap_units"])
    converted_total = 0
    for index, order in enumerate(market_orders):
        if remaining <= 0:
            break
        if len(order) < 3 or order[:2] != ["BUY_SEED", "STRAWBERRY"]:
            continue
        quantity = max(0, _int(order[2]))
        if quantity <= 0:
            continue
        converted = min(quantity, remaining)
        if converted < quantity and len(market_orders) >= order_cap:
            # Splitting would consume a market slot; leave this parent order intact.
            continue
        remainder = None
        if converted < quantity:
            remainder = list(order)
            remainder[2] = quantity - converted
        order[1] = "TOMATO"
        order[2] = converted
        if remainder is not None:
            market_orders.append(remainder)
        converted_total += converted
        remaining -= converted

    if converted_total:
        state["seed_swap_units"] += converted_total
        _TELEMETRY["seed_swaps"] += converted_total
    return converted_total


def _positions_and_commands(
    observation: dict[str, Any], farmer: list[Any], hands: list[list[Any]]
) -> tuple[list[Any], list[list[Any]], list[list[Any]]]:
    seat = _int(observation.get("player", 0))
    farms = observation.get("farms") or []
    farm = farms[seat] if 0 <= seat < len(farms) else {}
    positions = [farm.get("farmer")] + list(farm.get("hands") or [])
    commands = [farmer] + hands
    return positions, commands, list(farm.get("tiles") or [])


def _rewrite_plant_commands(
    observation: dict[str, Any],
    farmer: list[Any],
    hands: list[list[Any]],
    state: dict[str, Any],
    current_tomato_seeds: int,
) -> tuple[set[int], int]:
    positions, commands, board = _positions_and_commands(observation, farmer, hands)
    native_tomato_plants = sum(
        1 for command in commands if len(command) >= 2 and command[:2] == ["PLANT", "TOMATO"]
    )
    free_observed_seeds = max(0, current_tomato_seeds - native_tomato_plants)
    cohort_seed_budget = max(
        0,
        _int(state["confirmed_seed_units"])
        - _int(state["confirmed_plant_count"]),
    )
    command_budget = max(
        0, MAX_COHORT_UNITS - _int(state["plant_commands_swapped"])
    )
    used_sites: set[tuple[int, int]] = set()
    swapped_actors: set[int] = set()

    for actor, command in enumerate(commands):
        if not command or command[0] != "PLANT":
            continue
        pos = positions[actor] if actor < len(positions) else None
        try:
            site = (_int(pos[0], -1), _int(pos[1], -1))
        except (TypeError, IndexError):
            site = (-1, -1)
        if site in used_sites:
            continue
        used_sites.add(site)

        if (
            command[:2] != ["PLANT", "STRAWBERRY"]
            or free_observed_seeds <= 0
            or cohort_seed_budget <= 0
            or command_budget <= 0
            or _tile_at(board, site) is not None
        ):
            continue

        command[1] = "TOMATO"
        free_observed_seeds -= 1
        cohort_seed_budget -= 1
        command_budget -= 1
        swapped_actors.add(actor)
        state["plant_commands_swapped"] += 1
        _TELEMETRY["plant_commands_swapped"] += 1

    return swapped_actors, native_tomato_plants


def _pending_tomato_plants(
    commands: list[list[Any]],
    positions: list[Any],
    swapped_actors: set[int],
    day: int,
) -> list[dict[str, Any]]:
    pending: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for actor, command in enumerate(commands):
        if len(command) < 2 or command[:2] != ["PLANT", "TOMATO"]:
            continue
        pos = positions[actor] if actor < len(positions) else None
        try:
            site = (_int(pos[0], -1), _int(pos[1], -1))
        except (TypeError, IndexError):
            continue
        if site in seen:
            continue
        seen.add(site)
        pending.append({"pos": site, "day": day, "swapped": actor in swapped_actors})
    return pending


def _add_tomato_surplus_sale(
    market_orders: list[list[Any]],
    observation: dict[str, Any],
    configuration: Any,
) -> int:
    private = observation.get("private") or {}
    shed = private.get("shed") or {}
    tomato_stock = max(0, _int(shed.get("TOMATO")))
    existing = [
        order
        for order in market_orders
        if len(order) >= 3 and order[:2] == ["SELL", "TOMATO"]
    ]
    already_scheduled = sum(max(0, _int(order[2])) for order in existing)
    surplus = max(0, tomato_stock - already_scheduled)
    if surplus <= 0:
        return 0

    if existing:
        existing[0][2] = max(0, _int(existing[0][2])) + surplus
        return surplus

    if len(market_orders) >= _order_cap(configuration):
        return 0
    market_orders.append(["SELL", "TOMATO", surplus])
    return surplus


def agent(observation, configuration=None):
    """Call main.agent, then apply the bounded observed day-6 cohort swap."""
    step = _int(observation.get("step", -1)) if isinstance(observation, dict) else -1
    if step == 0:
        _reset_telemetry()

    try:
        parent_action = _PARENT_AGENT(observation, configuration)
    except Exception:
        _TELEMETRY["errors"] += 1
        raise

    try:
        if not isinstance(observation, dict) or not isinstance(parent_action, dict) or step < 0:
            return parent_action

        seat = _int(observation.get("player", 0))
        state = _STATE.setdefault(seat, _new_state())
        if step <= state["last_step"]:
            # Repeated same-step calls are left to the parent unchanged.
            return parent_action

        private = observation.get("private") or {}
        seeds = private.get("seeds") or {}
        current_tomato_seeds = max(0, _int(seeds.get("TOMATO")))
        _reconcile_previous_turn(observation, state, current_tomato_seeds)

        turns_per_day = 24
        if isinstance(configuration, dict):
            turns_per_day = max(1, _int(configuration.get("turnsPerDay", 24), 24))
        day = step // turns_per_day
        if day == 6 and not state["eligible"] and _triggered(observation):
            state["eligible"] = True
            _TELEMETRY["eligible"] += 1

        result = parent_action
        converted_buy = 0
        native_tomato_buy = False
        swapped_actors: set[int] = set()
        modified = False

        if state["eligible"]:
            market_orders = [
                list(order) if isinstance(order, (list, tuple)) else copy.deepcopy(order)
                for order in (parent_action.get("market") or [])
            ]
            farmer = list(parent_action.get("farmer") or ["PASS"])
            hands = [
                list(command) if isinstance(command, (list, tuple)) else ["PASS"]
                for command in (parent_action.get("hands") or [])
            ]

            native_tomato_buy = any(
                isinstance(order, (list, tuple))
                and len(order) >= 3
                and order[:2] == ["BUY_SEED", "TOMATO"]
                for order in market_orders
            )

            if day == 6:
                converted_buy = _rewrite_seed_purchases(
                    market_orders, state, _order_cap(configuration)
                )
                swapped_actors, _ = _rewrite_plant_commands(
                    observation, farmer, hands, state, current_tomato_seeds
                )
                modified = bool(converted_buy or swapped_actors)

            if day >= 6:
                added_sales = _add_tomato_surplus_sale(
                    market_orders, observation, configuration
                )
                if added_sales:
                    _TELEMETRY["tomato_sales"] += added_sales
                    modified = True

            if modified:
                result = dict(parent_action, farmer=farmer, hands=hands, market=market_orders)

            positions, commands, _ = _positions_and_commands(observation, farmer, hands)
            state["pending_tomato_plants"] = _pending_tomato_plants(
                commands, positions, swapped_actors, day
            )

        state["previous_seed_balance"] = current_tomato_seeds
        state["previous_converted_buy"] = converted_buy
        state["previous_native_tomato_buy"] = native_tomato_buy
        state["last_step"] = step
        return result
    except Exception:
        _TELEMETRY["errors"] += 1
        return parent_action


agent.telemetry = _TELEMETRY
kaggle_submission_agent = agent
