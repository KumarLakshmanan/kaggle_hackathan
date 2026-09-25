"""Day-26 service-supply experiment against the unchanged main.py policy.

The route's day-26 main farmer has two FEED commands after a one-unit wheat
pickup.  At day-25 close, reserve enough wheat for the simultaneous first
morning pickups; at the pickup, give the main farmer the two units its own
published schedule requires.  All inputs are the current observation, the
parent's returned action, and the parent's own action tape.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_PARENT_PATH = Path(__file__).resolve().with_name("main.py")
_PARENT_NAME = __name__ + "_unchanged_main"
_PARENT_SPEC = importlib.util.spec_from_file_location(_PARENT_NAME, _PARENT_PATH)
if _PARENT_SPEC is None or _PARENT_SPEC.loader is None:
    raise RuntimeError("Cannot load unchanged main.py")
_PARENT = importlib.util.module_from_spec(_PARENT_SPEC)
sys.modules[_PARENT_NAME] = _PARENT
_PARENT_SPEC.loader.exec_module(_PARENT)

_REPORT = {
    "service_float_buys": 0,
    "service_float_units": 0,
    "service_pickups": 0,
    "service_pickup_units": 0,
    "service_errors": 0,
}
_FLOAT_ARMED: dict[int, int] = {}


def _route(seat: int, step: int):
    native = _PARENT._IMPL.chassis.players.get(seat)
    if native is None:
        return None
    route_id = 2 if step >= 648 else native["route"]
    return _PARENT._IMPL.chassis.routes[route_id]


def _amount(command: list) -> int:
    return int(command[2]) if len(command) > 2 else 1


def _morning_need(tape: list, morning: int) -> tuple[int, int]:
    first = tape[morning + 1]
    lead = first.get("farmer") or []
    if lead[:2] != ["PICKUP", "WHEAT"]:
        return 0, 0
    feeds = sum(
        (tape[t].get("farmer") or [None])[0] == "FEED"
        for t in range(morning + 1, morning + 24)
    )
    lead_need = max(_amount(lead), feeds)
    other = sum(
        _amount(command)
        for command in first.get("hands", [])
        if command[:2] == ["PICKUP", "WHEAT"]
    )
    return lead_need, other


def _service_action(observation: dict, action: dict) -> dict:
    step = int(observation["step"])
    seat = int(observation["player"])
    if step not in (623, 625) or not isinstance(action, dict):
        return action
    tape = _route(seat, step)
    if tape is None:
        return action
    lead_need, tape_other = _morning_need(tape, 624)
    if lead_need <= 1:
        return action

    private = observation["private"]
    shed = private["shed"]
    if step == 623:
        # Market orders execute before the midnight depot transfer.  Only
        # enlarge an existing wheat buy, preserving every market queue slot.
        market = [list(order) for order in action.get("market", [])]
        buys = [i for i, order in enumerate(market) if order[:2] == ["BUY_PRODUCT", "WHEAT"]]
        if len(buys) != 1 or any(command and command[0] == "FEED" for command in
                                 [action.get("farmer")] + list(action.get("hands") or [])):
            return action
        wheat = int(shed.get("WHEAT", 0))
        wheat += sum(int(inv.get("WHEAT", 0)) for inv in private["inventories"])
        wheat += sum(_amount(order) for order in market if order[:2] == ["BUY_PRODUCT", "WHEAT"])
        wheat -= sum(_amount(order) for order in market if order[:2] == ["SELL", "WHEAT"])
        deficit = max(0, lead_need + tape_other - wheat)
        if deficit != 1:
            return action
        total_stock = sum(int(q) for q in shed.values())
        total_stock += sum(sum(int(q) for q in inv.values()) for inv in private["inventories"])
        total_stock += sum(_amount(order) for order in market if order[:2] == ["BUY_PRODUCT", "WHEAT"])
        if total_stock + deficit > 100:
            return action
        farm = observation["farms"][seat]
        quote = int(observation["market"]["prices"].get("WHEAT", 100))
        if float(farm["money"]) < 100 + 2 * quote:
            return action
        market[buys[0]][2] += deficit
        _FLOAT_ARMED[seat] = step
        _REPORT["service_float_buys"] += 1
        _REPORT["service_float_units"] += deficit
        return dict(action, market=market)

    farmer = list(action.get("farmer") or [])
    if _FLOAT_ARMED.get(seat) != 623:
        return action
    if farmer[:2] != ["PICKUP", "WHEAT"]:
        return action
    carried = int(private["inventories"][0].get("WHEAT", 0))
    wanted = max(0, lead_need - carried)
    if wanted <= _amount(farmer):
        return action
    others = sum(
        _amount(command)
        for command in action.get("hands", [])
        if command[:2] == ["PICKUP", "WHEAT"]
    )
    if int(shed.get("WHEAT", 0)) < wanted + others:
        return action
    _REPORT["service_pickups"] += 1
    _REPORT["service_pickup_units"] += wanted - _amount(farmer)
    return dict(action, farmer=["PICKUP", "WHEAT", wanted])


def agent(observation, configuration=None):
    if int(observation.get("step", -1)) == 0:
        _FLOAT_ARMED.clear()
        for key in _REPORT:
            _REPORT[key] = 0
    action = _PARENT.agent(observation, configuration)
    try:
        if configuration is not None and (
            int(configuration.get("turnsPerDay", 24)) != 24
            or int(configuration.get("shedCapacity", 100)) != 100
        ):
            return action
        return _service_action(observation, action)
    except (KeyError, IndexError, TypeError, ValueError):
        _REPORT["service_errors"] += 1
        return action


agent.telemetry = _REPORT
