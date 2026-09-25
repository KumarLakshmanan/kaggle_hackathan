"""Observation-time sizing ablation for the incumbent late tomato project.

Run through ``route_panel_benchmark.py`` with ``--candidate-override MODE=half``
or ``MODE=omit``.  ``MODE=full`` is a pass-through control.  This file imports
the unmodified ``main.py`` and changes no shared policy or diagnostics files.

The half arm only scales the incumbent's already-requested tomato seed order
after it appears in the current action.  It services five fixed owned targets
through the incumbent's own worker state machine, while retaining its staffing
calendar and observed-stock sale requests.  The sizing and service hooks added
here read no route id, episode seed, future shop sequence, or opponent-private
state; the imported incumbent remains unchanged and supplies its own base plan.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import main as _incumbent


MODE = "half"  # full | half | omit; can be overridden by paired_benchmark
if MODE not in {"full", "half", "omit"}:
    raise ValueError(f"Unsupported MODE: {MODE!r}")

_PARENT_AGENT = _incumbent.agent
_FULL_TARGETS = [(x, y) for y in (5, 6) for x in range(5, 10)]
_HALF_TARGETS = _FULL_TARGETS[:5]
_REPORT: dict[str, Any] = {}
_CALL_STATE: dict[int, dict[str, Any]] = {}


def _reset_report() -> None:
    _REPORT.clear()
    _REPORT.update(
        mode=str(MODE),
        incumbent_calls=0,
        half_commitments=0,
        omit_gate_calls=0,
        requested_seed_units=0,
        confirmed_seed_units=0,
        requested_hires=0,
        confirmed_hires=0,
        tomato_plant_requests=0,
        confirmed_tomato_plantings=0,
        failed_tomato_plantings=0,
        tomato_sell_order_units=0,
        incompatible_labor_abstentions=0,
        hook_errors=0,
    )


_reset_report()


def _private(observation: Mapping[str, Any]) -> Mapping[str, Any]:
    value = observation.get("private", {})
    return value if isinstance(value, Mapping) else {}


def _farm(observation: Mapping[str, Any], seat: int) -> Mapping[str, Any]:
    farms = observation.get("farms", [])
    if not isinstance(farms, list) or not 0 <= seat < len(farms):
        return {}
    value = farms[seat]
    return value if isinstance(value, Mapping) else {}


def _confirm_previous(observation: Mapping[str, Any], seat: int) -> None:
    state = _CALL_STATE.setdefault(seat, {})
    private = _private(observation)
    farm = _farm(observation, seat)

    purchase = state.pop("pending_seed_purchase", None)
    if purchase:
        seeds = private.get("seeds", {}) or {}
        current = max(0, int(seeds.get("TOMATO", 0) or 0))
        gained = max(0, current - int(purchase["before"]))
        _REPORT["confirmed_seed_units"] += min(int(purchase["requested"]), gained)

    hire = state.pop("pending_hires", None)
    if hire:
        hands = len(farm.get("hands", []) or [])
        gained = max(0, hands - int(hire["before"]))
        _REPORT["confirmed_hires"] += min(int(hire["requested"]), gained)

    pending_plants = state.pop("pending_plants", [])
    board = farm.get("tiles", []) or []
    for x, y, day in pending_plants:
        tile = board[y][x] if y < len(board) and x < len(board[y]) else None
        if (
            isinstance(tile, Mapping)
            and tile.get("kind") == "PLANT"
            and tile.get("crop") == "TOMATO"
            and int(tile.get("planted_day", -1)) == day
        ):
            _REPORT["confirmed_tomato_plantings"] += 1
        else:
            _REPORT["failed_tomato_plantings"] += 1


def _instrument_action(
    observation: Mapping[str, Any], seat: int, action: Any
) -> None:
    if not isinstance(action, Mapping):
        return
    state = _CALL_STATE.setdefault(seat, {})
    farm = _farm(observation, seat)
    private = _private(observation)
    commands = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
    positions = [farm.get("farmer"), *(farm.get("hands") or [])]
    day = max(0, int(observation.get("step", 0) or 0)) // 24
    requested = []
    for actor, command in enumerate(commands):
        if (
            actor >= len(positions)
            or not isinstance(command, (list, tuple))
            or len(command) < 2
            or command[:2] != ["PLANT", "TOMATO"]
        ):
            continue
        pos = positions[actor]
        if isinstance(pos, (list, tuple)) and len(pos) >= 2:
            x, y = int(pos[0]), int(pos[1])
            requested.append((x, y, day))
    if requested:
        state.setdefault("pending_plants", []).extend(requested)
        _REPORT["tomato_plant_requests"] += len(requested)

    market = action.get("market") or []
    _REPORT["tomato_sell_order_units"] += sum(
        max(0, int(order[2]))
        for order in market
        if isinstance(order, (list, tuple))
        and len(order) >= 3
        and order[:2] == ["SELL", "TOMATO"]
    )


def _patch_half_request(original_request):
    """Wrap the incumbent request hook; scale only its live seed-buy action."""

    def sized_request(observation, action, state, native):
        before_market = list(action.get("market") or []) if isinstance(action, Mapping) else []
        result = original_request(observation, action, state, native)
        if not isinstance(result, Mapping):
            return result

        market = [list(order) if isinstance(order, (list, tuple)) else order
                  for order in (result.get("market") or [])]
        added = market[len(before_market):]
        buys = [
            order for order in added
            if isinstance(order, list)
            and len(order) >= 3
            and order[:2] == ["BUY_SEED", "TOMATO"]
            and int(order[2]) > 0
        ]
        if not buys:
            return result

        pending = state.get("pending") or {}
        # The incumbent's alternate labor solver has a distinct path certificate.
        # Do not corrupt it with this deliberately small cohort ablation.
        if pending.get("labor") is not None:
            _REPORT["incompatible_labor_abstentions"] += 1
            return result

        seat = int(observation.get("player", 0) or 0)
        call_state = _CALL_STATE.setdefault(seat, {})
        requested = max(1, (int(buys[0][2]) + 1) // 2)
        buys[0][2] = requested
        state["targets"] = list(_HALF_TARGETS)
        state["_exp_premium_sizing"] = "half"
        call_state["pending_seed_purchase"] = {
            "before": int((_private(observation).get("seeds", {}) or {}).get("TOMATO", 0) or 0),
            "requested": requested,
        }
        _REPORT["requested_seed_units"] += requested
        _REPORT["half_commitments"] += 1
        return dict(result, market=market)

    return sized_request


def _patch_half_worker(original_worker):
    """Keep crop workers' routes and all downstream work on the half cohort."""

    def sized_worker(observation, state, actor, role):
        if state.get("_exp_premium_sizing") == "half":
            targets = list(state.get("targets") or _HALF_TARGETS)
            if role.get("kind") == "fertilizer":
                role["targets"] = targets
            elif role.get("kind") == "crop":
                crop_actors = sorted(
                    index for index, worker_role in state.get("workers", {}).items()
                    if worker_role.get("kind") == "crop"
                )
                if actor in crop_actors:
                    worker_index = crop_actors.index(actor)
                    count = max(1, len(crop_actors))
                    start = len(targets) * worker_index // count
                    end = len(targets) * (worker_index + 1) // count
                    role["targets"] = targets[start:end]
        return original_worker(observation, state, actor, role)

    return sized_worker


def agent(observation: Mapping[str, Any], configuration: Any = None) -> Any:
    """Call the incumbent with the selected observation-legal sizing ablation."""
    step = int(observation.get("step", -1)) if isinstance(observation, Mapping) else -1
    seat = int(observation.get("player", 0) or 0) if isinstance(observation, Mapping) else 0
    if step == 0:
        _reset_report()
        _CALL_STATE[seat] = {}
    _REPORT["mode"] = str(MODE)
    _REPORT["incumbent_calls"] += 1
    if isinstance(observation, Mapping):
        _confirm_previous(observation, seat)

    original_qualify = _incumbent._v219_qualifies
    original_request = _incumbent._v219_request
    original_worker = _incumbent._v219_worker
    try:
        if MODE == "omit":
            def omit_qualification(_observation, _native):
                _REPORT["omit_gate_calls"] += 1
                return False

            _incumbent._v219_qualifies = omit_qualification
        elif MODE == "half":
            _incumbent._v219_request = _patch_half_request(original_request)
            _incumbent._v219_worker = _patch_half_worker(original_worker)

        action = _PARENT_AGENT(observation, configuration)
    except Exception:
        _REPORT["hook_errors"] += 1
        raise
    finally:
        _incumbent._v219_qualifies = original_qualify
        _incumbent._v219_request = original_request
        _incumbent._v219_worker = original_worker

    if isinstance(observation, Mapping):
        _instrument_action(observation, seat, action)
        # Purchases resolve after this observation's action.  The next observed
        # private seed/hand counts confirm what actually happened.
        state = _CALL_STATE.setdefault(seat, {})
        if isinstance(action, Mapping):
            orders = action.get("market") or []
            seed_qty = sum(
                int(order[2]) for order in orders
                if isinstance(order, (list, tuple))
                and len(order) >= 3
                and order[:2] == ["BUY_SEED", "TOMATO"]
                and int(order[2]) > 0
            )
            hire_qty = sum(
                1 for order in orders
                if isinstance(order, (list, tuple)) and order and order[0] == "HIRE"
            )
            if seed_qty:
                state["pending_seed_purchase"] = {
                    "before": int((_private(observation).get("seeds", {}) or {}).get("TOMATO", 0) or 0),
                    "requested": seed_qty,
                }
                # For full/omit, the incumbent may buy tomato seeds for other
                # reasons; include only the live order actually emitted.
                if MODE != "half":
                    _REPORT["requested_seed_units"] += seed_qty
            if hire_qty:
                state["pending_hires"] = {
                    "before": len(_farm(observation, seat).get("hands", []) or []),
                    "requested": hire_qty,
                }
                _REPORT["requested_hires"] += hire_qty
    return action


agent.telemetry = _REPORT
kaggle_submission_agent = agent
