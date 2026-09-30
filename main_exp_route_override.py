"""Validation-only route override harness for the transparent main engine.

The wrapper changes only the route selected at the day-6 shop lookup.  It is
intended for controlled replay experiments; it is not production code and it
never submits anything.  Configure the experiment with:

    KAGGRICULTURE_OVERRIDE_PAIR="YARN_STORE,ICE_CREAM_SHOP"
    KAGGRICULTURE_OVERRIDE_ROUTE=0
    KAGGRICULTURE_DISABLE_TERMINAL=1
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("route_override_base", ROOT / "main.py")
if spec is None or spec.loader is None:
    raise RuntimeError("could not load main.py")
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)


def _configure() -> None:
    pair_text = os.environ.get("KAGGRICULTURE_OVERRIDE_PAIR", "").strip()
    route_text = os.environ.get("KAGGRICULTURE_OVERRIDE_ROUTE", "").strip()
    max_other_money_text = os.environ.get(
        "KAGGRICULTURE_OVERRIDE_MAX_OTHER_MONEY", ""
    ).strip()
    max_other_money = (
        float(max_other_money_text) if max_other_money_text else None
    )
    fallback_route_text = os.environ.get(
        "KAGGRICULTURE_OVERRIDE_FALLBACK_ROUTE", ""
    ).strip()
    fallback_route = int(fallback_route_text) if fallback_route_text else None
    if pair_text and route_text:
        pair = tuple(part.strip() for part in pair_text.split(","))
        if len(pair) != 2:
            raise ValueError("KAGGRICULTURE_OVERRIDE_PAIR must contain two shop names")
        route = int(route_text)
        if route not in base._ROUTES:
            raise ValueError(f"unknown route {route}; available={sorted(base._ROUTES)}")
        # main.py carries several self-contained public agents.  The final
        # stack can call the outer engine, the v49 embedded engine, or the
        # Haide/rank41 embedded engine, so patch every live copy for a valid
        # route experiment.
        namespaces = [base.__dict__]
        for name in ("_V49_EMBEDDED_NAMESPACE", "_V51_HAIDE_NAMESPACE", "_V52_RANK41_NAMESPACE"):
            namespace = getattr(base, name, None)
            if isinstance(namespace, dict):
                namespaces.append(namespace)
        seen = set()
        for namespace in namespaces:
            impl = namespace.get("_IMPL")
            if impl is None or id(impl) in seen:
                continue
            seen.add(id(impl))
            if isinstance(namespace.get("_R108_SHOP_ROUTES"), dict):
                namespace["_R108_SHOP_ROUTES"][pair] = route
            if isinstance(namespace.get("_R110_OLD_SHOPS"), dict):
                namespace["_R110_OLD_SHOPS"][pair] = route
            original_router = impl.chassis.router

            def forced_router(observation, step, state, *, _original=original_router):
                selected = _original(observation, step, state)
                if int(step) >= 144:
                    town = observation.get("town", {}) if isinstance(observation, dict) else {}
                    shops = tuple((town.get("unlocked_shops", []) or [])[:2])
                    if shops == pair:
                        if max_other_money is not None:
                            farms = observation.get("farms", []) if isinstance(observation, dict) else []
                            player = int(observation.get("player", 0) or 0) if isinstance(observation, dict) else 0
                            other_index = 1 - player
                            other_farm = farms[other_index] if 0 <= other_index < len(farms) else {}
                            if isinstance(other_farm, dict):
                                other_money = other_farm.get("money", 0.0)
                            else:
                                other_money = getattr(other_farm, "money", 0.0)
                            if os.environ.get("KAGGRICULTURE_DEBUG_ROUTE") == "1":
                                debug_path = os.environ.get("KAGGRICULTURE_DEBUG_FILE", "")
                                message = (
                                    f"ROUTE_DECISION step={step} player={player} "
                                    f"other_index={other_index} other_money={other_money!r} "
                                    f"selected={selected} override={route}"
                                )
                                if debug_path:
                                    with open(debug_path, "a", encoding="utf-8") as handle:
                                        handle.write(message + "\n")
                            if float(other_money or 0.0) > max_other_money:
                                if fallback_route is not None:
                                    state["day6"] = True
                                    state["route"] = fallback_route
                                    return fallback_route
                                return selected
                        state["day6"] = True
                        state["route"] = route
                        return route
                return selected

            impl.chassis.router = forced_router
    if os.environ.get("KAGGRICULTURE_DISABLE_TERMINAL", "") == "1":
        base._PLANNER_NS["plan_terminal"] = lambda *args, **kwargs: {
            "accepted": False,
            "reason": "disabled by validation harness",
            "simulations": 0,
        }


_configure()
_base_agent = base.agent


if os.environ.get("KAGGRICULTURE_DEBUG_ROUTE") == "1":
    _original_act = base._IMPL.chassis.act

    def _debug_act(observation, configuration=None):
        step = int(observation.get("step", -1)) if isinstance(observation, dict) else -1
        if step in (0, 144):
            debug_path = os.environ.get("KAGGRICULTURE_DEBUG_FILE", "")
            message = f"ACT_DEBUG step={step} before={base._IMPL.chassis.players}"
            if debug_path:
                with open(debug_path, "a", encoding="utf-8") as handle:
                    handle.write(message + "\n")
        result = _original_act(observation, configuration)
        if step in (0, 144):
            debug_path = os.environ.get("KAGGRICULTURE_DEBUG_FILE", "")
            message = f"ACT_DEBUG step={step} after={base._IMPL.chassis.players}"
            if debug_path:
                with open(debug_path, "a", encoding="utf-8") as handle:
                    handle.write(message + "\n")
        return result

    base._IMPL.chassis.act = _debug_act


def agent(observation, configuration=None):
    if os.environ.get("KAGGRICULTURE_DEBUG_ROUTE") == "1":
        try:
            step = int(observation.get("step", -1))
            if step in (0, 144):
                message = (
                    "AGENT_DEBUG "
                    f"step={step} router={getattr(base._IMPL.chassis.router, '__name__', '?')} "
                    f"shops={observation.get('town', {}).get('unlocked_shops', []) if isinstance(observation, dict) else '?'} "
                    f"route_state={base._IMPL.chassis.players}"
                )
                print(message, flush=True)
                debug_path = os.environ.get("KAGGRICULTURE_DEBUG_FILE", "")
                if debug_path:
                    with open(debug_path, "a", encoding="utf-8") as handle:
                        handle.write(message + "\n")
        except Exception as exc:
            print(f"AGENT_DEBUG error={exc!r}", flush=True)
    result = _base_agent(observation, configuration)
    debug_path = os.environ.get("KAGGRICULTURE_DEBUG_ACTION_FILE", "")
    if debug_path:
        try:
            step = int(observation.get("step", -1))
            if step in (144, 145):
                with open(debug_path, "a", encoding="utf-8") as handle:
                    handle.write(json.dumps({"step": step, "action": result}, sort_keys=True) + "\n")
        except Exception:
            pass
    return result
