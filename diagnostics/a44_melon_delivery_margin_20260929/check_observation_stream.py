"""Stream bound a44 tapes through the candidate action mutator; no transitions run."""
from __future__ import annotations

import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MANIFEST = HERE / "manifest.json"
CANDIDATE = HERE / "candidate_a44_melon_delivery_v2.py"
SOURCE = ROOT / "diagnostics" / "adaptive_donor_pair_repair_20260928" / "candidate_combined.py"
PREDICATE = HERE / "predicate.json"
FULL_RESULTS = ROOT / "diagnostics" / "adaptive_donor_pair_repair_20260928" / "full_results.json"
EXPECTED_SOURCE_SHA256 = "a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f"
TRACE_CONFIG_ASSUMPTION = {"boardSize": 10, "shedCapacity": 100, "maxMarketOrdersPerTurn": 10}
EXPECTED_INVENTORY = {"MELON": 12, "FERTILIZER": 1}
ROUTE_POSITIONS = {714: [2, 4], 715: [3, 4], 716: [4, 4]}
SAVED_STEPS = (0, 713, 714, 715, 716, 717, 718)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_candidate():
    spec = importlib.util.spec_from_file_location("a44_melon_candidate_check", CANDIDATE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import generated candidate")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stream_trace(binding):
    path = ROOT / Path(binding["trace_path"])
    digest = sha256(path)
    if digest != binding["trace_sha256"] or digest != binding["receipt_trace_sha256"]:
        raise AssertionError(f"trace hash mismatch: {path}")
    count = 0
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("step") != count:
                raise AssertionError(f"unexpected trace step sequence: {path} at row {count}")
            count += 1
            yield row
    if count != 719:
        raise AssertionError(f"unexpected trace length {count}: {path}")


def project_hand(row, hand_index, xy):
    obs = copy.deepcopy(row["observation"])
    player = int(obs["player"])
    obs["farms"][player]["hands"][hand_index] = list(xy)
    obs["private"]["inventories"][hand_index + 1] = copy.deepcopy(EXPECTED_INVENTORY)
    return obs


def apply(module, row, observation=None, configuration=TRACE_CONFIG_ASSUMPTION):
    # The wrapper reads but does not mutate observations, so raw tape rows stay streamed.
    obs = row["observation"] if observation is None else observation
    action = copy.deepcopy(row["action"])
    return module._a44_melon_delivery_apply(obs, action, configuration)


def assert_expected_action(base, output, hand_index, expected_hand, expected_market=None):
    expected = copy.deepcopy(base)
    expected["hands"][hand_index] = expected_hand
    if expected_market is not None:
        expected["market"] = expected_market
    if output != expected:
        raise AssertionError("candidate changed output outside the specified hand/order fields")


def prepare_route(module, rows, hand_index):
    """Exercise actual call order, projecting only state changed by candidate actions."""
    module._A44_MELON_ROUTE_STATE.clear()
    if apply(module, rows[0]) != rows[0]["action"]:
        raise AssertionError("step0 latch reset must preserve the a44 action")
    row713 = rows[713]
    out713 = apply(module, row713)
    assert_expected_action(row713["action"], out713, hand_index, ["EAST"])
    for step in (714, 715):
        row = rows[step]
        projected = project_hand(row, hand_index, ROUTE_POSITIONS[step])
        out = apply(module, row, projected)
        assert_expected_action(row["action"], out, hand_index, ["EAST"])


def verify_latch_scope(module, target_rows):
    """Check step0 reset and player-key isolation without invoking the full agent."""
    seat0 = target_rows[("live-114271958", 0)]
    seat1 = target_rows[("live-114271958", 1)]
    module._A44_MELON_ROUTE_STATE.clear()
    apply(module, seat0[0])
    apply(module, seat1[0])
    out = apply(module, seat0[713])
    assert_expected_action(seat0[713]["action"], out, 5, ["EAST"])
    p0 = int(seat0[713]["observation"]["player"])
    p1 = int(seat1[0]["observation"]["player"])
    if p0 == p1 or p0 not in module._A44_MELON_ROUTE_STATE:
        raise AssertionError("test fixture did not create a distinct player-keyed latch")
    apply(module, seat1[0])
    if p0 not in module._A44_MELON_ROUTE_STATE:
        raise AssertionError("step0 for another player cleared the active player's latch")
    apply(module, seat0[0])
    if p0 in module._A44_MELON_ROUTE_STATE:
        raise AssertionError("step0 failed to clear that player's previous episode latch")
    projected714 = project_hand(seat0[714], 5, [2, 4])
    no_latch = apply(module, seat0[714], projected714)
    if no_latch != seat0[714]["action"]:
        raise AssertionError("continuation without a current-episode trigger changed the action")
    module._A44_MELON_ROUTE_STATE.clear()
    return {"step0_resets_only_own_player": True, "cross_player_latch_leak": False}


def verify_fallbacks(module, rows):
    hand_index = 5
    row716 = rows[716]
    projected716 = project_hand(row716, hand_index, [4, 4])
    base716 = copy.deepcopy(row716["action"])
    shed_count = sum(int(v) for v in projected716["private"]["shed"].values())
    drop_count = sum(EXPECTED_INVENTORY.values())

    def run_step716(config, action=None):
        prepare_route(module, rows, hand_index)
        local_action = copy.deepcopy(base716 if action is None else action)
        return module._a44_melon_delivery_apply(copy.deepcopy(projected716), local_action, config)

    cap_fail = run_step716({
        "boardSize": 10,
        "shedCapacity": shed_count + drop_count - 1,
        "maxMarketOrdersPerTurn": 10,
    })
    if cap_fail["hands"][hand_index] != ["PASS"] or cap_fail["market"] != base716["market"]:
        raise AssertionError("capacity failure must PASS and add no order")

    missing_capacity = run_step716({"boardSize": 10, "maxMarketOrdersPerTurn": 10})
    if missing_capacity["hands"][hand_index] != ["PASS"] or missing_capacity["market"] != base716["market"]:
        raise AssertionError("missing capacity must fail closed with PASS")

    competing = copy.deepcopy(base716)
    competing["hands"][0] = ["PLACE", "GOOSE"]
    comp_result = run_step716(TRACE_CONFIG_ASSUMPTION, competing)
    if comp_result["hands"][hand_index] != ["PASS"] or comp_result["market"] != competing["market"]:
        raise AssertionError("competing own PLACE must PASS and add no order")

    full_queue = copy.deepcopy(base716)
    full_queue["market"] = [["SELL", f"ITEM{i}", 1] for i in range(10)]
    queue_result = run_step716(TRACE_CONFIG_ASSUMPTION, full_queue)
    if queue_result["hands"][hand_index] != ["DROP"] or queue_result["market"] != full_queue["market"]:
        raise AssertionError("full order queue must use DROP-only fallback")

    duplicate = copy.deepcopy(base716)
    duplicate["market"] = [["SELL", "MELON", 12]]
    duplicate_result = run_step716(TRACE_CONFIG_ASSUMPTION, duplicate)
    if duplicate_result["hands"][hand_index] != ["DROP"] or duplicate_result["market"] != duplicate["market"]:
        raise AssertionError("existing MELON order must use DROP-only fallback")

    missing_order_cap = {"boardSize": 10, "shedCapacity": TRACE_CONFIG_ASSUMPTION["shedCapacity"]}
    missing_order_result = run_step716(missing_order_cap)
    if missing_order_result["hands"][hand_index] != ["DROP"] or missing_order_result["market"] != base716["market"]:
        raise AssertionError("missing order cap must not add a sale")

    row717, row718 = rows[717], rows[718]
    obs717 = copy.deepcopy(row717["observation"])
    obs717["farms"][obs717["player"]]["hands"][hand_index] = [4, 4]
    out717 = module._a44_melon_delivery_apply(obs717, copy.deepcopy(row717["action"]), TRACE_CONFIG_ASSUMPTION)
    if out717 != row717["action"] or out717["hands"][hand_index] != ["EAST"]:
        raise AssertionError("step717 fallback must preserve the incumbent EAST action")
    after_east = [5, 4]
    if after_east not in ([4, 4], [5, 4], [4, 5], [5, 5]):
        raise AssertionError("fallback EAST did not reach shed access")
    obs718 = copy.deepcopy(row718["observation"])
    obs718["farms"][obs718["player"]]["hands"][hand_index] = after_east
    out718 = module._a44_melon_delivery_apply(obs718, copy.deepcopy(row718["action"]), TRACE_CONFIG_ASSUMPTION)
    if out718 != row718["action"] or out718["hands"][hand_index] != ["DROP"]:
        raise AssertionError("step718 fallback must preserve the incumbent DROP action")

    return {
        "capacity_failure_or_competing_DROP_PLACE": "PASS; clear latch; saved EAST then DROP remains transform-only [4,4]->[5,4]",
        "missing_capacity": "PASS",
        "full_order_queue": "DROP only; no order",
        "duplicate_melon_sale": "DROP only; no duplicate order",
        "missing_order_cap": "DROP only; no order",
        "native_episode_transitions_run": False,
    }


def verify_latch_guards(module, rows):
    """Exercise latch-only continuation, mismatch clearing, and board-size guards."""
    hand_index = 5
    player = int(rows[713]["observation"]["player"])

    def start():
        module._A44_MELON_ROUTE_STATE.clear()
        out = apply(module, rows[713])
        assert_expected_action(rows[713]["action"], out, hand_index, ["EAST"])
        if module._A44_MELON_ROUTE_STATE.get(player) != {"hand_index": hand_index, "next_step": 714}:
            raise AssertionError("full step713 trigger did not create the expected latch")

    # Continuations without the full selector-created latch must remain unchanged.
    module._A44_MELON_ROUTE_STATE.clear()
    projected714 = project_hand(rows[714], hand_index, [2, 4])
    if apply(module, rows[714], projected714) != rows[714]["action"]:
        raise AssertionError("step714 changed without a step713 trigger latch")

    # A skipped expected step clears the latch and cannot resume on a later turn.
    start()
    skipped = apply(module, rows[715], project_hand(rows[715], hand_index, [3, 4]))
    if skipped != rows[715]["action"] or player in module._A44_MELON_ROUTE_STATE:
        raise AssertionError("out-of-order continuation must clear latch and preserve that base action")
    if apply(module, rows[714], projected714) != rows[714]["action"]:
        raise AssertionError("route resumed after out-of-order latch clear")

    # Wrong projected position at the expected step fails closed and clears.
    start()
    wrong_state = project_hand(rows[714], hand_index, [9, 9])
    wrong_out = apply(module, rows[714], wrong_state)
    if wrong_out["hands"][hand_index] != ["PASS"] or player in module._A44_MELON_ROUTE_STATE:
        raise AssertionError("state mismatch must PASS the latched hand and clear the latch")

    # boardSize=10 is required at the trigger and every continuation stage.
    module._A44_MELON_ROUTE_STATE.clear()
    bad_trigger = apply(module, rows[713], configuration={
        "boardSize": 9, "shedCapacity": 100, "maxMarketOrdersPerTurn": 10,
    })
    if bad_trigger != rows[713]["action"] or player in module._A44_MELON_ROUTE_STATE:
        raise AssertionError("step713 must reject boardSize other than 10")

    def advance_to(step):
        start()
        for prior in range(714, step):
            projected = project_hand(rows[prior], hand_index, ROUTE_POSITIONS[prior])
            out = apply(module, rows[prior], projected)
            assert_expected_action(rows[prior]["action"], out, hand_index, ["EAST"])

    for step in (714, 715, 716):
        advance_to(step)
        projected = project_hand(rows[step], hand_index, ROUTE_POSITIONS[step])
        bad_board = apply(module, rows[step], projected, {
            "boardSize": 9, "shedCapacity": 100, "maxMarketOrdersPerTurn": 10,
        })
        if bad_board["hands"][hand_index] != ["PASS"] or player in module._A44_MELON_ROUTE_STATE:
            raise AssertionError(f"step{step} must require boardSize=10 and clear safely")

    module._A44_MELON_ROUTE_STATE.clear()
    return {
        "continuation_requires_full_trigger_latch": True,
        "out_of_order_step_clears_latch_and_does_not_resume": True,
        "wrong_position_or_inventory_state_clears_with_PASS": True,
        "board_size_10_required_at_steps_713_714_715_716": True,
    }


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha256(SOURCE) != EXPECTED_SOURCE_SHA256:
        raise AssertionError("a44 parent source hash changed")
    if CANDIDATE.read_bytes()[:len(SOURCE.read_bytes())] != SOURCE.read_bytes():
        raise AssertionError("generated candidate does not preserve the exact a44 source prefix")
    if sha256(FULL_RESULTS) != manifest["bindings"]["full_results_sha256"]:
        raise AssertionError("a44 full-results hash mismatch")
    if sha256(PREDICATE) != manifest["frozen_predicate_file_sha256"]:
        raise AssertionError("frozen selector hash mismatch")

    module = load_candidate()
    if not callable(getattr(module, "agent", None)) or not isinstance(getattr(module.agent, "telemetry", None), dict):
        raise AssertionError("candidate artifact lacks a callable agent/telemetry entrypoint")
    activation_rows = manifest["activation_receipt"]["rows"]
    target = {(row["fixture_id"], row["seat"]): row for row in activation_rows}
    if len(target) != 4:
        raise AssertionError(f"expected four frozen activation rows, got {len(target)}")

    target_rows = {}
    target_outputs = {}
    off_trigger_outputs = 0
    raw_changes = []
    for binding in manifest["all_100_trace_bindings"]:
        key = (binding["fixture_id"], binding["seat"])
        is_target = key in target
        hand_index = target[key]["hand_index"] if is_target else None
        saved = {}
        outputs = {}
        row_count = 0
        for row in stream_trace(binding):
            row_count += 1
            step = row["step"]
            observation = project_hand(row, hand_index, ROUTE_POSITIONS[step]) if is_target and step in ROUTE_POSITIONS else None
            output = apply(module, row, observation)
            if is_target and step in (713, 714, 715, 716):
                outputs[step] = output
            if output != row["action"]:
                raw_changes.append({"fixture_id": binding["fixture_id"], "seat": binding["seat"], "step": step})
                if not (is_target and step in (713, 714, 715, 716)):
                    raise AssertionError(f"unexpected off-schedule change: {binding['fixture_id']} seat{binding['seat']} step{step}")
            elif not is_target:
                off_trigger_outputs += 1
            if is_target and step in SAVED_STEPS:
                saved[step] = row
        if row_count != 719:
            raise AssertionError(f"unexpected trace row count: {binding['fixture_id']} seat{binding['seat']} {row_count}")
        if is_target:
            target_rows[key] = saved
            target_outputs[key] = outputs
            player = int(saved[716]["observation"]["player"])
            if player in module._A44_MELON_ROUTE_STATE:
                raise AssertionError("route latch was not cleared after step716")

    expected_changed = {(key[0], key[1], step) for key in target for step in (713, 714, 716)}
    actual_changed = {(r["fixture_id"], r["seat"], r["step"]) for r in raw_changes}
    if actual_changed != expected_changed:
        raise AssertionError(f"action changes differ from planned steps: {sorted(actual_changed)}")
    if off_trigger_outputs != 96 * 719:
        raise AssertionError(f"off-trigger action parity mismatch: {off_trigger_outputs}/{96 * 719}")

    projected_receipts = []
    for key, activation in sorted(target.items()):
        rows = target_rows[key]
        outputs = target_outputs[key]
        hand = activation["hand_index"]
        if hand != 5:
            raise AssertionError(f"unexpected activated hand index: {hand}")
        assert_expected_action(rows[713]["action"], outputs[713], hand, ["EAST"])
        assert_expected_action(rows[714]["action"], outputs[714], hand, ["EAST"])
        assert_expected_action(rows[715]["action"], outputs[715], hand, ["EAST"])
        expected_market = copy.deepcopy(rows[716]["action"]["market"])
        expected_market.append(["SELL", "MELON", 12])
        assert_expected_action(rows[716]["action"], outputs[716], hand, ["DROP"], expected_market)
        if sum(order == ["SELL", "MELON", 12] for order in outputs[716]["market"]) != 1:
            raise AssertionError("step716 must add one and only one SELL MELON 12")
        projected_receipts.append({
            "fixture_id": activation["fixture_id"],
            "seat": activation["seat"],
            "player_id": rows[713]["observation"]["player"],
            "hand_index": hand,
            "projected_state_guard_sequence": {
                str(step): {"position": ROUTE_POSITIONS[step], "inventory": EXPECTED_INVENTORY}
                for step in (714, 715, 716)
            },
            "actions": {
                "713": "WATER->EAST",
                "714": "HARVEST->EAST (base action not regenerated)",
                "715": "EAST->EAST",
                "716": "EAST->DROP + one SELL MELON 12",
            },
        })

    latch_receipt = verify_latch_scope(module, target_rows)
    fallback_receipt = verify_fallbacks(module, target_rows[("live-114271958", 0)])
    guard_receipt = verify_latch_guards(module, target_rows[("live-114271958", 0)])

    route_rows = target_rows[("live-114271958", 0)]
    for label, config in (
        ("missing_config", {"boardSize": 10}),
        ("insufficient_capacity", {"boardSize": 10, "shedCapacity": 52, "maxMarketOrdersPerTurn": 10}),
    ):
        module._A44_MELON_ROUTE_STATE.clear()
        out = apply(module, route_rows[713], configuration=config)
        if out != route_rows[713]["action"] or module._A44_MELON_ROUTE_STATE:
            raise AssertionError(f"step713 must fail closed and create no latch for {label}")

    receipt = {
        "study": manifest["study"],
        "status": "passed_static_player_latch_action_transform_checks_no_outcomes",
        "candidate_sha256": sha256(CANDIDATE),
        "candidate_parent_source_sha256": sha256(SOURCE),
        "candidate_prefix_exact_match": True,
        "manifest_sha256": sha256(MANIFEST),
        "predicate_file_sha256": sha256(PREDICATE),
        "full_results_sha256": sha256(FULL_RESULTS),
        "trace_file_count_verified": len(manifest["all_100_trace_bindings"]),
        "action_changes_on_projected_target_stream": raw_changes,
        "off_trigger_trace_output_parity": {
            "seat_rows": 96,
            "steps_per_row": 719,
            "exact_action_outputs": off_trigger_outputs,
            "expected_action_outputs": 96 * 719,
            "frozen_reward_margin_gate": "exact own reward, rival reward, margin, and result equality; not run",
        },
        "target_action_transform_receipts": projected_receipts,
        "player_latch_scope_check": latch_receipt,
        "latch_guard_checks": guard_receipt,
        "fallback_action_transform_receipt": fallback_receipt,
        "configuration_note": (
            "Trace receipts omit per-game configuration. The action-transform harness assumes "
            "boardSize=10/shedCapacity=100/maxMarketOrdersPerTurn=10 only to exercise the route; runtime step713 "
            "requires actual supplied config, and later capacity/order guards fail closed."
        ),
        "scope_limit": (
            "The checker streams each bound a44 observation/action row and projects only candidate hand position "
            "and inventory at steps714–716. It calls the isolated action mutator, not the a44 parent policy or final "
            "agent entrypoint, and does not step the environment or evaluate rewards/margins. Native prefix validation "
            "on actual counterfactual states remains mandatory before any outcome run."
        ),
        "file_loader_check": {
            "imported_generated_candidate_file": True,
            "agent_entrypoint_callable": True,
            "telemetry_attribute_present": True,
            "agent_entrypoint_called": False,
        },
        "simulation_or_outcome_runs": 0,
        "telemetry_counter_scope": "cumulative per loaded module; diagnostic only and not consulted by policy",
        "telemetry_counters": dict(module._A44_MELON_COUNTERS),
    }
    output = HERE / "observation_stream_receipt.json"
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"status={receipt['status']}")
    print(f"candidate_sha256={receipt['candidate_sha256']}")
    print(f"off_trigger_outputs={off_trigger_outputs}/{96 * 719}")
    print(f"planned_target_changes={len(raw_changes)}")
    print(f"receipt={output}")


if __name__ == "__main__":
    main()
