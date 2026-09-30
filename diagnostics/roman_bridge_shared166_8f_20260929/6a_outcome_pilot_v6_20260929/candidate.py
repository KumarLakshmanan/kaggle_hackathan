"""Offline 6a + Roman adapter candidate for a frozen diagnostic pilot.

This loader composes hash-bound local artifacts. It is deliberately not a
standalone Kaggle submission and is not eligible for upload.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PARENT_SHA256 = "6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc"
DONOR_SHA256 = "fc403d05e29b1b317985f7ec77d1a3fa490c0264af8d639c3bfea899fcf1a849"
PARENT_PATH = ROOT / "diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/candidate.py"
DONOR_PATH = ROOT / "diagnostics/donor_opening_agents_20260928/candidate_shared166.py"
ADAPTER_PATH = HERE / "candidate_adapter.py"
LIVE_SNAPSHOTS_PATH = HERE / "live_step2_public_snapshots.json"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path):
    import hashlib
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if _sha(PARENT_PATH) != PARENT_SHA256:
    raise RuntimeError("6a parent hash mismatch")
if _sha(DONOR_PATH) != DONOR_SHA256:
    raise RuntimeError("shared166 donor hash mismatch")

_PARENT = _load(f"{__name__}_parent_6a", PARENT_PATH)
_DONOR = _load(f"{__name__}_donor_shared166", DONOR_PATH)
_LAYER = _load(f"{__name__}_roman_adapter_6a", ADAPTER_PATH)
_SNAPSHOT_LEDGER = json.loads(LIVE_SNAPSHOTS_PATH.read_text(encoding="utf-8"))
if (_SNAPSHOT_LEDGER.get("parent_candidate_sha256") != PARENT_SHA256
        or _SNAPSHOT_LEDGER.get("adapter_sha256") != _sha(ADAPTER_PATH)
        or _SNAPSHOT_LEDGER.get("donor_sha256") != DONOR_SHA256
        or _SNAPSHOT_LEDGER.get("fixture_id") != "live-114270587"):
    raise RuntimeError("step-2 snapshot ledger provenance mismatch")
_SNAPSHOTS = {
    int(row["candidate_seat"]): row
    for row in _SNAPSHOT_LEDGER.get("snapshots", [])
}
if set(_SNAPSHOTS) != {0, 1}:
    raise RuntimeError("step-2 snapshot ledger must bind both seats")

_RUNTIME = {}
_EXPECTED_STEP2_ACTIONS = {}


def _reset_runtime():
    _RUNTIME.clear()
    _RUNTIME.update({
        "roman_public_trigger_step1": False,
        "roman_parent_opening_guard_step1": False,
        "roman_hire_action_step1": False,
        "roman_snapshot_provenance": False,
        "roman_step2_own_guard": False,
        "roman_step2_public_guard": False,
        "roman_step2_matches_discovery": False,
        "roman_donor_calls": 0,
        "roman_donor_action_matches": False,
        "roman_parent_fallbacks": 0,
        "roman_fallback_step": -1,
        "roman_fallback_reason": "",
        "roman_cow_pickup_units_step3": 0,
        "roman_cow_pickup_workers_step3": [],
        "roman_errors": 0,
    })
    _EXPECTED_STEP2_ACTIONS.clear()


def _donor_action(observation, configuration=None):
    action = _DONOR._donor_action(observation, configuration)
    _RUNTIME["roman_donor_calls"] = int(_RUNTIME.get("roman_donor_calls", 0)) + 1
    if int(observation.get("step", -1)) == 2:
        seat = int(observation["player"])
        own = observation["farms"][seat]
        mapped = _LAYER.remap_donor_hands(action, len(own.get("hands", [])))
        _EXPECTED_STEP2_ACTIONS[seat] = mapped
    return deepcopy(action)


_ADAPTED = {
    seat: _LAYER.make_agent(_PARENT.agent, _donor_action, _SNAPSHOTS[seat])
    for seat in (0, 1)
}


def agent(observation, configuration=None):
    step = int(observation.get("step", -1))
    seat = int(observation.get("player", -1))
    if seat not in (0, 1):
        raise ValueError("expected a two-player Kaggriculture observation")
    if step == 0:
        _reset_runtime()
        agent.telemetry.clear()
    elif step == 1:
        _RUNTIME["roman_public_trigger_step1"] = bool(_LAYER._public_trigger(observation))
        _RUNTIME["roman_parent_opening_guard_step1"] = bool(
            _LAYER._expected_parent_opening_state(observation))
        _RUNTIME["roman_snapshot_provenance"] = bool(
            _LAYER._has_bound_step2_public_snapshot(_SNAPSHOTS[seat]))
    elif step == 2:
        _RUNTIME["roman_step2_own_guard"] = bool(
            _LAYER._expected_step2_merge_state(observation))
        _RUNTIME["roman_step2_public_guard"] = bool(
            _LAYER._expected_step2_public_state(observation, _SNAPSHOTS[seat]))
        _RUNTIME["roman_step2_matches_discovery"] = bool(
            observation["farms"][seat] == _SNAPSHOTS[seat].get("own_farm")
            and observation["private"] == _SNAPSHOTS[seat].get("own_private"))

    try:
        action = _ADAPTED[seat](observation, configuration)
    except Exception:
        _RUNTIME["roman_errors"] = int(_RUNTIME.get("roman_errors", 0)) + 1
        raise

    _RUNTIME.update(getattr(_ADAPTED[seat], "telemetry", {}) or {})
    if step == 1 and _RUNTIME.get("roman_public_trigger_step1"):
        _RUNTIME["roman_hire_action_step1"] = (
            action == _LAYER._fifth_hire_action(observation))
    if step == 2 and _RUNTIME.get("roman_public_trigger_step1"):
        expected = _EXPECTED_STEP2_ACTIONS.get(seat)
        _RUNTIME["roman_donor_action_matches"] = expected is not None and action == expected
    if step == 3 and _RUNTIME.get("roman_public_trigger_step1"):
        inventory = observation.get("private", {}).get("inventories", [])
        by_worker = [int(item.get("COW", 0)) for item in inventory]
        _RUNTIME["roman_cow_pickup_units_step3"] = sum(by_worker)
        _RUNTIME["roman_cow_pickup_workers_step3"] = [
            index - 1 for index, quantity in enumerate(by_worker)
            if index > 0 and quantity > 0
        ]

    agent.telemetry.update(getattr(_PARENT.agent, "telemetry", {}) or {})
    agent.telemetry.update(_RUNTIME)
    return action


agent.telemetry = {}
