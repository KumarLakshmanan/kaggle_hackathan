from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import copy
import gzip


sys.dont_write_bytecode = True


def _source_only_get_code(loader, fullname):
    path = Path(loader.get_filename(fullname))
    source = path.read_bytes()
    return compile(source, str(path), "exec", dont_inherit=True)


def _reject_sourceless(loader, fullname):
    raise ImportError(f"source-only pilot refuses bytecode module {fullname}")


importlib.machinery.SourceFileLoader.get_code = _source_only_get_code
importlib.machinery.SourcelessFileLoader.get_code = _reject_sourceless


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PARENT = ROOT / "diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/candidate.py"
V8_DIR = ROOT / "diagnostics/roman_bridge_shared166_8f_20260929/6a_outcome_pilot_v8_source_only_20260929"
V8_PREFIX = V8_DIR / "prefix_results.json"
PANEL_PATH = HERE / "panel.json"
MANIFEST_PATH = HERE / "frozen_manifest.json"
SHARED_LOCK = ROOT / "diagnostics/.shared_game_run.lock"
OWN_LOCK = HERE / "run.lock"
BASELINE_ROWS = HERE / "baseline_outcomes.jsonl"
CANDIDATE_ROWS = HERE / "candidate_outcomes.jsonl"
RECEIPT_PATH = HERE / "outcome_receipt.json"
RUN_MANIFEST_PATH = HERE / "run_manifest.json"
PREFIX_RESULTS_PATH = HERE / "prefix_results.json"
FIELDS = ("candidate_reward", "opponent_reward", "margin", "result",
          "candidate_status", "opponent_status", "frames")

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
import build_panel


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_once(path, value):
    raw = (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with Path(path).open("xb") as stream:
        stream.write(raw)


def verify_frozen_inputs(check_empty=True, own_lock_held=False):
    manifest = read(MANIFEST_PATH)
    panel = read(PANEL_PATH)
    if manifest.get("complete") is not True or manifest.get("resume_allowed") is not False:
        raise AssertionError("frozen manifest is incomplete or resumable")
    if panel.get("schema") != "6a-step1-hire-only-fixed-tape-pilot-v1":
        raise AssertionError("unexpected experiment panel")
    if manifest.get("candidate_sha256") != sha(HERE / "candidate.py"):
        raise AssertionError("candidate changed after freeze")
    if manifest.get("panel_sha256") != sha(PANEL_PATH):
        raise AssertionError("panel changed after freeze")
    expected = {str(Path(path).resolve()): digest
                for path, digest in manifest.get("bindings", {}).items()}
    for path, digest in expected.items():
        if sha(Path(path)) != digest:
            raise AssertionError(f"frozen input hash mismatch: {path}")
    actual = {str(path): sha(path) for path in build_panel.binding_paths(panel)}
    if expected != actual or manifest.get("binding_count") != len(expected):
        raise AssertionError("frozen binding set changed")
    if manifest.get("shared_lock_path") != str(SHARED_LOCK.resolve()):
        raise AssertionError("shared simulator lock path changed")
    if check_empty:
        existing = [name for name in build_panel.RUNTIME_OUTPUTS
                    if not (own_lock_held and name == "run.lock") and (HERE / name).exists()]
        if existing:
            raise FileExistsError(f"one-shot runner refuses partial or repeated output: {existing}")
    return manifest, panel


def clean(row):
    return (row.get("candidate_status") == "DONE"
            and row.get("opponent_status") == "DONE"
            and row.get("frames") == 720
            and row.get("candidate_errors") == {})


def fields_equal(left, right):
    return all(left.get(key) == right.get(key) for key in FIELDS)


def read_trace(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_rows(path, rows):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")
            stream.flush()


def verify_after_work(receipt, initial_manifest_sha):
    try:
        verify_frozen_inputs(check_empty=False, own_lock_held=True)
        ok = sha(MANIFEST_PATH) == initial_manifest_sha
        if not ok:
            raise AssertionError("frozen manifest changed during execution")
    except Exception as exc:
        ok = False
        receipt["post_run_hash_verification_error"] = f"{type(exc).__name__}: {exc}"
    receipt["post_run_hashes_verified"] = ok
    receipt["gate_checks"]["post_run_frozen_inputs_unchanged"] = ok
    return ok


def expected_candidate_step1(baseline_action):
    expected = json.loads(json.dumps(baseline_action))
    expected["market"].append(["HIRE"])
    return expected


def native_prefix(job, policy_path, digest, trace_path):
    from diagnostics.stream_replay_io_20260928.cached_input import load_fixture
    from diagnostics.physical_route_rollout_20260928 import native_core as core
    from diagnostics.physical_route_rollout_20260928.check import Box, state_from_frames

    fixture = job["fixture"]
    replay = load_fixture(fixture)
    configuration = dict(replay["configuration"])
    configuration["seed"] = None
    state = state_from_frames(replay["steps"][0])
    env = Box(configuration=Box(**configuration),
              info={"seed": int(fixture["seed"])}, done=False)
    tape = json.loads(gzip.decompress(
        Path(fixture["source_action_tape_path"]).read_bytes()))["actions"]
    if len(tape) != 719:
        raise AssertionError("prefix opponent tape must contain 719 actions")
    tape_hashes = [hashlib.sha256(json.dumps(tape, sort_keys=sort_key,
                                               separators=(",", ":")).encode("utf-8")).hexdigest()
                   for sort_key in (False, True)]
    if fixture["source_opponent_action_sha256"] not in tape_hashes:
        raise AssertionError("prefix opponent action tape hash mismatch")
    if sha(policy_path) != digest:
        raise AssertionError("prefix policy hash mismatch before load")
    spec = importlib.util.spec_from_file_location(
        f"hire_prefix_{job['tag']}_{Path(policy_path).stem}", policy_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prefix policy {policy_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    seat = int(job["seat"])
    with gzip.open(trace_path, "wt", encoding="utf-8") as stream:
        for step in range(4):
            observation = copy.deepcopy(dict(
                state[seat].observation, remainingOverageTime=60.0))
            action = module.agent(observation, configuration)
            stream.write(json.dumps({"step": step, "observation": observation,
                                     "action": action}, ensure_ascii=True,
                                    separators=(",", ":")) + "\n")
            if step < 3:
                state[seat].action = action
                state[1 - seat].action = copy.deepcopy(tape[step])
                core.interpreter(state, env)
                for item in state:
                    item.observation.step = step + 1
    telemetry = dict(getattr(module.agent, "telemetry", {}) or {})
    if sha(policy_path) != digest:
        raise AssertionError("prefix policy hash mismatch after run")
    return {"telemetry": telemetry, "trace_sha256": sha(trace_path)}


def native_prefix_gate(panel):
    historical = read(V8_PREFIX)
    historical_by_seat = {int(row["candidate_seat"]): row
                          for row in historical.get("results", [])}
    results = []
    for job in panel["jobs"]:
        if job["role"] != "target_loss":
            continue
        seat = int(job["seat"])
        prefix_ref = historical_by_seat[seat]
        base_path = HERE / f"prefix_parent_{job['tag']}.jsonl.gz"
        cand_path = HERE / f"prefix_candidate_{job['tag']}.jsonl.gz"
        base_runtime = native_prefix(job, PARENT, panel["parent_candidate_sha256"], base_path)
        candidate_runtime = native_prefix(job, HERE / "candidate.py",
                                          panel["candidate_sha256"], cand_path)
        baseline = read_trace(base_path)
        candidate = read_trace(cand_path)
        config = dict(__import__("diagnostics.stream_replay_io_20260928.cached_input",
                                 fromlist=["load_fixture"]).load_fixture(job["fixture"])["configuration"])
        parent_step1 = baseline[1]["action"]
        expected_step1 = expected_candidate_step1(parent_step1)
        baseline_state = baseline[2]["observation"]
        candidate_state = candidate[2]["observation"]
        baseline_own = baseline_state["farms"][seat]
        candidate_own = candidate_state["farms"][seat]
        hires_before = int(baseline[1]["observation"]["farms"][seat].get("hires_today", -1))
        multiplier = int(config.get("farmHandCostMult", 1))
        a, b = 1, 1
        for _ in range(max(0, hires_before)):
            a, b = b, a + b
        expected_cost = a * multiplier
        parent_action_sha = hashlib.sha256(json.dumps(
            parent_step1, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        candidate_action_sha = hashlib.sha256(json.dumps(
            expected_step1, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

        checks = {
            "saved_v8_prefix_source_checks": all(prefix_ref.get("source_checks", {}).values()),
            "baseline_step0_and1_match_saved_6a_prefix": all(
                baseline[step]["observation"] == prefix_ref["observations"][str(step)]
                and baseline[step]["action"] == prefix_ref["actions"][str(step)]
                for step in (0, 1)
            ),
            "candidate_step0_matches_parent": (
                candidate[0]["observation"] == baseline[0]["observation"]
                and candidate[0]["action"] == baseline[0]["action"]
            ),
            "candidate_step1_observation_matches_parent": (
                candidate[1]["observation"] == baseline[1]["observation"]
            ),
            "candidate_step1_is_parent_action_plus_trailing_hire": (
                candidate[1]["action"] == expected_step1
            ),
            "six_parent_orders_preserved_and_seven_below_cap": (
                len(parent_step1.get("market", [])) == 6
                and len(candidate[1]["action"].get("market", [])) == 7
                and len(candidate[1]["action"].get("market", []))
                    <= int(config.get("maxMarketOrdersPerTurn", 10))
            ),
            "hire_config_cost_is_five": expected_cost == 5,
            "baseline_hires_today_is_four": hires_before == 4,
            "step2_has_extra_hand_and_hire_count": (
                len(candidate_own.get("hands", [])) == len(baseline_own.get("hands", [])) + 1
                and int(candidate_own.get("hires_today", -1))
                    == int(baseline_own.get("hires_today", -1)) + 1
            ),
            "existing_hands_unchanged_and_one_new_hand_appended": (
                candidate_own.get("hands", [])[:-1] == baseline_own.get("hands", [])
                and len(candidate_own.get("hands", [])[-1]) == 2
            ),
            "step2_cash_decreased_by_exact_hire_cost": (
                float(baseline_own.get("money", 0)) - float(candidate_own.get("money", 0))
                == expected_cost
            ),
            "step2_rival_and_market_unchanged": (
                candidate_state["farms"][1 - seat] == baseline_state["farms"][1 - seat]
                and candidate_state.get("market") == baseline_state.get("market")
            ),
            "all_other_step2_observation_state_unchanged": False,
            "step2_existing_private_stock_unchanged_and_new_hand_empty": (
                candidate_state["private"].get("shed") == baseline_state["private"].get("shed")
                and candidate_state["private"].get("seeds") == baseline_state["private"].get("seeds")
                and candidate_state["private"].get("inventories", [])[:-1]
                    == baseline_state["private"].get("inventories", [])
                and candidate_state["private"].get("inventories", [])[-1] == {}
            ),
            "step2_and3_parent_actions_match_five_hand_state": all(
                len(candidate[step]["action"].get("hands", []))
                == len(candidate[step]["observation"]["farms"][seat].get("hands", [])) == 5
                for step in (2, 3)
            ),
            "step2_and3_candidate_returns_parent_actions": all(
                candidate_runtime["telemetry"].get(f"hire_parent_action_sha256_step{step}")
                == candidate_runtime["telemetry"].get(f"hire_returned_action_sha256_step{step}")
                and bool(candidate_runtime["telemetry"].get(f"hire_parent_action_sha256_step{step}"))
                for step in (2, 3)
            ),
            "candidate_triggered_exactly_once": (
                candidate_runtime["telemetry"].get("hire_trigger_checks") == 1
                and candidate_runtime["telemetry"].get("hire_opening_checks") == 1
                and candidate_runtime["telemetry"].get("hire_activations") == 1
                and candidate_runtime["telemetry"].get("hire_modifications") == 1
                and candidate_runtime["telemetry"].get("hire_step") == 1
                and candidate_runtime["telemetry"].get("hire_parent_calls") == 4
                and candidate_runtime["telemetry"].get("hire_parent_errors") == 0
            ),
            "candidate_step1_parent_action_hash_matches": (
                candidate_runtime["telemetry"].get("hire_parent_action_sha256") == parent_action_sha
                and candidate_runtime["telemetry"].get("hire_candidate_action_sha256") == candidate_action_sha
            ),
            "candidate_prefix_source_hashes_stable": (
                base_runtime["trace_sha256"] == sha(base_path)
                and candidate_runtime["trace_sha256"] == sha(cand_path)
            ),
        }
        normalized_base = copy.deepcopy(baseline_state)
        normalized_candidate = copy.deepcopy(candidate_state)
        normalized_candidate["farms"][seat]["hands"] = copy.deepcopy(
            normalized_base["farms"][seat]["hands"])
        normalized_candidate["farms"][seat]["hires_today"] = normalized_base["farms"][seat]["hires_today"]
        normalized_candidate["farms"][seat]["money"] = normalized_base["farms"][seat]["money"]
        normalized_candidate["private"]["inventories"] = copy.deepcopy(
            normalized_base["private"]["inventories"])
        checks["all_other_step2_observation_state_unchanged"] = normalized_candidate == normalized_base
        results.append({
            "fixture_id": job["fixture_id"], "seat": seat,
            "parent_trace_sha256": base_runtime["trace_sha256"],
            "candidate_trace_sha256": candidate_runtime["trace_sha256"],
            "checks": checks, "passed": all(checks.values()),
        })
        print(json.dumps({"phase": "native_prefix", "seat": seat,
                          "passed": all(checks.values()), "checks": checks},
                         ensure_ascii=True), flush=True)
    return {"complete": True, "passed": len(results) == 2 and all(x["passed"] for x in results),
            "results": results}


def paired_trace_checks(baseline_path, candidate_path, role, seat, telemetry):
    baseline = read_trace(baseline_path)
    candidate = read_trace(candidate_path)
    checks = {
        "both_traces_719_steps": len(baseline) == len(candidate) == 719,
        "baseline_trace_contiguous": [row.get("step") for row in baseline] == list(range(719)),
        "candidate_trace_contiguous": [row.get("step") for row in candidate] == list(range(719)),
    }
    if not all(checks.values()):
        return checks
    if role != "target_loss":
        checks["all_control_observations_match"] = all(
            left["observation"] == right["observation"]
            for left, right in zip(baseline, candidate)
        )
        checks["all_control_actions_match"] = all(
            left["action"] == right["action"]
            for left, right in zip(baseline, candidate)
        )
        checks["control_hire_inactive"] = not any(
            row.get("action") != base.get("action")
            for row, base in zip(candidate, baseline)
        )
        return checks

    checks["target_step0_observation_match"] = baseline[0]["observation"] == candidate[0]["observation"]
    checks["target_step0_action_match"] = baseline[0]["action"] == candidate[0]["action"]
    checks["target_step1_observation_match"] = baseline[1]["observation"] == candidate[1]["observation"]
    checks["target_parent_step1_queue_is_six_orders"] = len(baseline[1]["action"].get("market", [])) == 6
    expected = expected_candidate_step1(baseline[1]["action"])
    checks["target_step1_is_exact_parent_action_plus_one_trailing_hire"] = candidate[1]["action"] == expected
    checks["target_step1_queue_is_seven_below_ten_order_cap"] = len(candidate[1]["action"].get("market", [])) == 7
    checks["target_parent_step1_action_hash"] = (
        telemetry.get("hire_parent_action_sha256") == hashlib.sha256(
            json.dumps(baseline[1]["action"], sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
    )
    checks["target_candidate_step1_action_hash"] = (
        telemetry.get("hire_candidate_action_sha256") == hashlib.sha256(
            json.dumps(expected, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
    )
    checks["target_activation_once_at_step1"] = (
        telemetry.get("hire_trigger_checks") == 1
        and telemetry.get("hire_opening_checks") == 1
        and telemetry.get("hire_activations") == 1
        and telemetry.get("hire_modifications") == 1
        and telemetry.get("hire_step") == 1
        and telemetry.get("hire_parent_calls") == 719
        and telemetry.get("hire_parent_errors") == 0
    )
    baseline_state = baseline[2]["observation"]
    candidate_state = candidate[2]["observation"]
    own_baseline = baseline_state["farms"][seat]
    own_candidate = candidate_state["farms"][seat]
    checks["target_step2_has_one_extra_worker"] = (
        len(own_candidate.get("hands", [])) == len(own_baseline.get("hands", [])) + 1
        and int(own_candidate.get("hires_today", -1)) == int(own_baseline.get("hires_today", -1)) + 1
        and float(own_candidate.get("money", 0)) == float(own_baseline.get("money", 0)) - 5.0
    )
    checks["target_step2_rival_and_market_unchanged"] = (
        candidate_state["farms"][1 - seat] == baseline_state["farms"][1 - seat]
        and candidate_state.get("market") == baseline_state.get("market")
    )
    checks["target_parent_action_unmodified_at_steps2_and3"] = all(
        telemetry.get(f"hire_parent_action_sha256_step{step}")
        == telemetry.get(f"hire_returned_action_sha256_step{step}")
        and bool(telemetry.get(f"hire_parent_action_sha256_step{step}"))
        for step in (2, 3)
    )
    checks["target_parent_step2_and3_actions_match_hand_count"] = all(
        len(candidate[step]["action"].get("hands", []))
        == len(candidate[step]["observation"]["farms"][seat].get("hands", []))
        for step in (2, 3)
    )
    return checks


def run_once():
    manifest, panel = verify_frozen_inputs()
    initial_manifest_sha = sha(MANIFEST_PATH)
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    from diagnostics.stream_replay_io_20260928.fast_game_cached import play

    started = datetime.now(timezone.utc).isoformat()
    receipt = {
        "schema": "6a-step1-hire-only-outcome-receipt-v1",
        "complete": False,
        "passed": False,
        "diagnostic_only": True,
        "fixed_tape_only": True,
        "reactive_validation": False,
        "promotion": False,
        "candidate_sha256": manifest["candidate_sha256"],
        "parent_candidate_sha256": manifest["parent_candidate_sha256"],
        "panel_sha256": manifest["panel_sha256"],
        "frozen_manifest_sha256": sha(MANIFEST_PATH),
        "binding_count": manifest["binding_count"],
        "baseline_game_count": 0,
        "native_prefix_pair_count": 0,
        "candidate_game_count": 0,
        "game_count": 0,
        "stop_phase": None,
        "gate_checks": {},
    }

    with exclusive_run(SHARED_LOCK):
        with exclusive_run(OWN_LOCK):
            verify_frozen_inputs(own_lock_held=True)
            write_once(RUN_MANIFEST_PATH, {
                "started_at_utc": started,
                "candidate_sha256": manifest["candidate_sha256"],
                "runner_sha256": sha(HERE / "run.py"),
                "builder_sha256": sha(HERE / "build_panel.py"),
                "frozen_manifest_sha256": sha(MANIFEST_PATH),
                "panel_sha256": sha(PANEL_PATH),
                "shared_lock_path": str(SHARED_LOCK.resolve()),
                "worker_count": 1,
                "resume_allowed": False,
                "fixed_tape_only": True,
                "game_count": 12,
            })
            baselines = []
            candidates = []

            prefix_result = native_prefix_gate(panel)
            prefix_checks = {
                f"seat{row['seat']}|{name}": bool(passed)
                for row in prefix_result["results"]
                for name, passed in row["checks"].items()
            }
            write_once(PREFIX_RESULTS_PATH, prefix_result)
            receipt["native_prefix_pair_count"] = len(prefix_result["results"])
            receipt["gate_checks"].update(prefix_checks)
            receipt["native_prefix"] = prefix_result
            if not prefix_result["passed"]:
                receipt.update({
                    "complete": True,
                    "stop_phase": "native_prefix_gate",
                    "native_prefix": prefix_result,
                    "game_count": 0,
                    "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                })
                verify_after_work(receipt, initial_manifest_sha)
                write_once(RECEIPT_PATH, receipt)
                print(json.dumps({"passed": False, "stop_phase": "native_prefix_gate",
                                  "prefix_checks": prefix_checks}, ensure_ascii=True), flush=True)
                return receipt

            for job in panel["jobs"]:
                path = HERE / f"baseline_{job['tag']}.jsonl.gz"
                row = play(job["fixture"], PARENT, manifest["parent_candidate_sha256"],
                           int(job["seat"]), trace_path=path)
                saved = job["baseline_reference"]
                fields_match = fields_equal(row, saved)
                telemetry_match = row.get("candidate_telemetry") == saved.get("candidate_telemetry")
                baselines.append({
                    "fixture_id": job["fixture_id"], "seat": int(job["seat"]),
                    "tag": job["tag"], "role": job["role"], "parent": row,
                    "matches_v8_fields": fields_match,
                    "matches_v8_telemetry": telemetry_match,
                })
                print(json.dumps({"phase": "baseline", "fixture_id": job["fixture_id"],
                                  "seat": job["seat"], "result": row["result"],
                                  "margin": row["margin"], "fields_match": fields_match,
                                  "telemetry_match": telemetry_match, "clean": clean(row)},
                                 ensure_ascii=True), flush=True)

            baseline_checks = {}
            for row in baselines:
                key = f"{row['fixture_id']}|seat{row['seat']}"
                baseline = row["parent"]
                baseline_checks[f"{key}|clean"] = clean(baseline)
                baseline_checks[f"{key}|v8_fields"] = row["matches_v8_fields"]
                baseline_checks[f"{key}|v8_telemetry"] = row["matches_v8_telemetry"]
                if row["role"] == "target_loss":
                    baseline_checks[f"{key}|expected_loss"] = baseline.get("result") == "loss"
                else:
                    baseline_checks[f"{key}|expected_win"] = (
                        baseline.get("result") == "win" and float(baseline.get("margin", 0)) > 0
                    )
            write_rows(BASELINE_ROWS, baselines)
            receipt["baseline_game_count"] = len(baselines)
            receipt["gate_checks"].update(baseline_checks)
            if len(baselines) != 6 or not all(baseline_checks.values()):
                receipt.update({"complete": True, "stop_phase": "baseline_gate",
                                "parent_baselines": baselines,
                                "game_count": len(baselines),
                                "completed_at_utc": datetime.now(timezone.utc).isoformat()})
                verify_after_work(receipt, initial_manifest_sha)
                write_once(RECEIPT_PATH, receipt)
                return receipt

            for job in panel["jobs"]:
                path = HERE / f"candidate_{job['tag']}.jsonl.gz"
                row = play(job["fixture"], HERE / "candidate.py",
                           manifest["candidate_sha256"], int(job["seat"]), trace_path=path)
                baseline_row = next(item for item in baselines
                                    if item["fixture_id"] == job["fixture_id"]
                                    and int(item["seat"]) == int(job["seat"]))
                telemetry = row.get("candidate_telemetry", {})
                trace_checks = paired_trace_checks(
                    HERE / f"baseline_{job['tag']}.jsonl.gz", path,
                    job["role"], int(job["seat"]), telemetry)
                checks = {
                    "candidate_clean": clean(row),
                    "trace_checks": all(trace_checks.values()),
                }
                if job["role"] == "target_loss":
                    checks["target_win_positive_margin"] = (
                        row.get("result") == "win" and float(row.get("margin", 0)) > 0
                    )
                else:
                    checks["control_exact_fields"] = fields_equal(row, baseline_row["parent"])
                    checks["control_exact_telemetry"] = (
                        row.get("candidate_telemetry") == baseline_row["parent"].get("candidate_telemetry")
                    )
                passed = all(checks.values())
                candidates.append({
                    "fixture_id": job["fixture_id"], "seat": int(job["seat"]),
                    "tag": job["tag"], "role": job["role"], "candidate": row,
                    "paired_6a_margin_delta": float(row["margin"]) - float(baseline_row["parent"]["margin"]),
                    "paired_own_reward_delta": float(row["candidate_reward"]) - float(baseline_row["parent"]["candidate_reward"]),
                    "paired_rival_reward_delta": float(row["opponent_reward"]) - float(baseline_row["parent"]["opponent_reward"]),
                    "trace_checks": trace_checks,
                    "checks": checks,
                    "passed": passed,
                })
                print(json.dumps({"phase": "candidate", "fixture_id": job["fixture_id"],
                                  "seat": job["seat"], "result": row["result"],
                                  "margin": row["margin"],
                                  "paired_margin_delta": candidates[-1]["paired_6a_margin_delta"],
                                  "checks": checks, "trace_checks": trace_checks,
                                  "clean": clean(row)}, ensure_ascii=True), flush=True)

            write_rows(CANDIDATE_ROWS, candidates)
            receipt["candidate_game_count"] = len(candidates)
            receipt["game_count"] = len(baselines) + len(candidates)
            for row in candidates:
                for name, passed in row["checks"].items():
                    receipt["gate_checks"][f"{row['fixture_id']}|seat{row['seat']}|{name}"] = bool(passed)
            receipt.update({
                "complete": True,
                "parent_baselines": baselines,
                "candidate_games": candidates,
                "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            })
            final_hashes_ok = verify_after_work(receipt, initial_manifest_sha)
            receipt["passed"] = (
                len(candidates) == 6
                and all(row["passed"] for row in candidates)
                and final_hashes_ok
            )
            write_once(RECEIPT_PATH, receipt)
            print(json.dumps({"complete": True, "passed": receipt["passed"],
                              "game_count": receipt["game_count"],
                              "target_margins": [row["candidate"]["margin"] for row in candidates
                                                 if row["role"] == "target_loss"],
                              "gate_checks": receipt["gate_checks"]}, ensure_ascii=True), flush=True)
    return receipt


if __name__ == "__main__":
    result = run_once()
    raise SystemExit(0 if result.get("passed") else 1)
