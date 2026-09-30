"""Offline 6a wrapper adding one guarded hire while preserving its full turn."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import types


ROOT = Path(__file__).resolve().parents[2]
PARENT_PATH = ROOT / "diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/candidate.py"
PARENT_SHA256 = "6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc"


def _load_source_only(name: str, path: Path):
    path = Path(path)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PARENT_SHA256:
        raise RuntimeError("6a parent source hash mismatch")
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


_PARENT = _load_source_only(f"{__name__}_parent_6a", PARENT_PATH)
_RUNTIME = {}


def _canonical_sha(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _farm_pair(observation):
    player = int(observation["player"])
    if player not in (0, 1) or len(observation.get("farms", [])) != 2:
        raise ValueError("expected a two-player Kaggriculture observation")
    return observation["farms"][player], observation["farms"][1 - player]


def _target_trigger(observation):
    if int(observation.get("step", -1)) != 1:
        return False
    _, rival = _farm_pair(observation)
    return rival.get("farmer") == [4, 3] and len(rival.get("hands", [])) == 3


_EXPECTED_SHED = {
    "CARROT": 0, "COW": 2, "EGG": 0, "FERTILIZER": 0, "GOOSE": 0,
    "MELON": 0, "MILK": 0, "SHEEP": 2, "STRAWBERRY": 0,
    "TOMATO": 0, "WHEAT": 6, "WOOL": 0,
}
_EXPECTED_SEEDS = {
    "CARROT": 0, "MELON": 0, "STRAWBERRY": 0, "TOMATO": 0, "WHEAT": 0,
}


def _opening_guard(observation):
    own, _ = _farm_pair(observation)
    private = observation.get("private", {})
    return (
        own.get("farmer") == [4, 4]
        and len(own.get("hands", [])) == 4
        and int(own.get("hires_today", -1)) == 4
        and float(own.get("money", 0)) == 1088.0
        and private.get("shed") == _EXPECTED_SHED
        and private.get("seeds") == _EXPECTED_SEEDS
        and private.get("inventories") == [{}] * 5
    )


def _fibonacci(index):
    a, b = 1, 1
    for _ in range(max(0, int(index))):
        a, b = b, a + b
    return a


def _safe_to_append_hire(observation, action, configuration):
    own, _ = _farm_pair(observation)
    market = action.get("market") if isinstance(action, dict) else None
    if not isinstance(market, list) or any(
        isinstance(command, list) and command and command[0] == "HIRE"
        for command in market
    ):
        return False
    config = configuration or {}
    max_orders = max(1, int(config.get("maxMarketOrdersPerTurn", 10)))
    hire_multiplier = int(config.get("farmHandCostMult", 1))
    next_hire_cost = _fibonacci(own.get("hires_today", 0)) * hire_multiplier
    return (
        len(market) + 1 <= max_orders
        and hire_multiplier > 0
        and float(own.get("money", 0)) >= next_hire_cost
    )


def _reset():
    _RUNTIME.clear()
    _RUNTIME.update({
        "hire_parent_calls": 0,
        "hire_parent_errors": 0,
        "hire_trigger_checks": 0,
        "hire_opening_checks": 0,
        "hire_activations": 0,
        "hire_modifications": 0,
        "hire_step": -1,
        "hire_parent_action_sha256": "",
        "hire_candidate_action_sha256": "",
        "hire_parent_action_sha256_step2": "",
        "hire_returned_action_sha256_step2": "",
        "hire_parent_action_sha256_step3": "",
        "hire_returned_action_sha256_step3": "",
    })


def agent(observation, configuration=None):
    step = int(observation.get("step", -1))
    if step == 0:
        _reset()
    try:
        parent_action = _PARENT.agent(observation, configuration)
        _RUNTIME["hire_parent_calls"] += 1
    except Exception:
        _RUNTIME["hire_parent_errors"] += 1
        raise

    action = parent_action
    if step == 1:
        trigger = bool(_target_trigger(observation))
        opening = bool(_opening_guard(observation))
        _RUNTIME["hire_trigger_checks"] = int(trigger)
        _RUNTIME["hire_opening_checks"] = int(opening)
        if trigger and opening and _safe_to_append_hire(observation, parent_action, configuration):
            action = json.loads(json.dumps(parent_action))
            action["market"].append(["HIRE"])
            _RUNTIME["hire_activations"] += 1
            _RUNTIME["hire_modifications"] += 1
            _RUNTIME["hire_step"] = step
            _RUNTIME["hire_parent_action_sha256"] = _canonical_sha(parent_action)
            _RUNTIME["hire_candidate_action_sha256"] = _canonical_sha(action)

    if _RUNTIME["hire_modifications"] and step in (2, 3):
        step_suffix = str(step)
        _RUNTIME[f"hire_parent_action_sha256_step{step_suffix}"] = _canonical_sha(parent_action)
        _RUNTIME[f"hire_returned_action_sha256_step{step_suffix}"] = _canonical_sha(action)

    parent_telemetry = getattr(_PARENT.agent, "telemetry", {}) or {}
    agent.telemetry.clear()
    agent.telemetry.update(parent_telemetry)
    if _RUNTIME["hire_modifications"]:
        agent.telemetry.update(_RUNTIME)
    return action


agent.telemetry = {}
