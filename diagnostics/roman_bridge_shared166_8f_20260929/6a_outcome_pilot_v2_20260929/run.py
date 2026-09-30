from __future__ import annotations

from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import build_panel


PANEL_PATH = HERE / "panel.json"
MANIFEST_PATH = HERE / "frozen_manifest.json"
PARENT = build_panel.PARENT
CANDIDATE = HERE / "candidate.py"
ADAPTER = HERE / "candidate_adapter.py"
DONOR = build_panel.DONOR
PREFIX_RUNNER = build_panel.PREFIX_RUNNER
PREFIX_FREEZE = build_panel.PREFIX_FREEZE
PREFIX_SNAPSHOTS = build_panel.PREFIX_SNAPSHOTS
BASELINE_ROWS = HERE / "baseline_outcomes.jsonl"
PREFIX_RESULTS = HERE / "prefix_results.json"
DISCOVERY_RESULTS = HERE / "snapshot_discovery.json"
VALIDATION_RESULTS = HERE / "snapshot_validation.json"
LIVE_SNAPSHOTS = HERE / "live_step2_public_snapshots.json"
OUTCOME_ROWS = HERE / "outcomes.jsonl"
RECEIPT = HERE / "outcome_receipt.json"
RUN_MANIFEST = HERE / "run_manifest.json"
OWN_LOCK = HERE / "run.lock"
SHARED_LOCK = ROOT / "diagnostics/.shared_game_run.lock"
PARENT_SHA = build_panel.PARENT_SHA
DONOR_SHA = build_panel.DONOR_SHA
FIELDS = ("result", "candidate_reward", "opponent_reward", "margin",
          "candidate_status", "opponent_status", "frames")


def sha(path: Path) -> str:
    return build_panel.sha(path)


def read(path: Path):
    return build_panel.read(path)


def write_once(path: Path, value):
    build_panel.write_once(path, value)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def verify_frozen_inputs(check_empty=True, own_lock_held=False):
    panel = read(PANEL_PATH)
    expected_panel = build_panel.build_panel_data()
    require(panel == expected_panel, "frozen panel differs from re-derived jobs")
    manifest = read(MANIFEST_PATH)
    expected_bindings = {str(path): sha(path) for path in build_panel.binding_paths(panel)}
    require(manifest.get("complete") is True
            and manifest.get("diagnostic_only") is True
            and manifest.get("fixed_tape_only") is True
            and manifest.get("reactive_validation") is False
            and manifest.get("promotion") is False,
            "manifest scope changed")
    require(manifest.get("candidate_sha256") == sha(CANDIDATE), "candidate hash mismatch")
    require(manifest.get("candidate_adapter_sha256") == sha(ADAPTER), "adapter hash mismatch")
    require(manifest.get("parent_candidate_sha256") == PARENT_SHA == sha(PARENT), "parent hash mismatch")
    require(manifest.get("donor_sha256") == DONOR_SHA == sha(DONOR), "donor hash mismatch")
    require(manifest.get("panel_sha256") == sha(PANEL_PATH), "panel hash mismatch")
    require(manifest.get("bindings") == expected_bindings, "binding set or input hash changed")
    require(manifest.get("binding_count") == len(expected_bindings), "binding count mismatch")
    require(manifest.get("shared_lock_path") == str(SHARED_LOCK), "shared lock path changed")
    if check_empty:
        existing = [name for name in build_panel.RUNTIME_OUTPUTS
                    if not (own_lock_held and name == "run.lock") and (HERE / name).exists()]
        require(not existing, f"one-shot runner refuses existing or partial outputs: {existing}")
    return manifest, panel


def clean_game(game):
    return (game.get("candidate_status") == "DONE"
            and game.get("opponent_status") == "DONE"
            and game.get("frames") == 720
            and not game.get("candidate_errors"))


def compare_fields(left, right):
    return {field: left.get(field) == right.get(field) for field in FIELDS}


def load_prefix_probe():
    spec = importlib.util.spec_from_file_location("roman_prefix_probe_rebound_6a", PREFIX_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load prefix helper {PREFIX_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    # Rebind its tested helper functions to current 6a and the freshly hashed adapter.
    module.V5_CANDIDATE = PARENT
    module.V5_SHA = PARENT_SHA
    module.ADAPTER = ADAPTER
    module.DONOR = DONOR
    module.DONOR_SHA = DONOR_SHA
    return module


def baseline_gate(rows, panel):
    by_key = {(row["fixture_id"], int(row["seat"])): row for row in rows}
    checks = {}
    for job in panel["jobs"]:
        key = (job["fixture_id"], int(job["seat"]))
        row = by_key[key]
        checks[f"{key[0]}|seat{key[1]}|clean"] = clean_game(row["parent"])
        if key[0] == build_panel.TARGET_ID:
            checks[f"{key[0]}|seat{key[1]}|parent_loss"] = row["parent"].get("result") == "loss"
        else:
            checks[f"{key[0]}|seat{key[1]}|parent_win"] = (
                row["parent"].get("result") == "win"
                and float(row["parent"].get("margin", 0)) > 0)
        saved = job.get("saved_6a_reference")
        if saved is not None:
            checks[f"{key[0]}|seat{key[1]}|matches_saved_6a"] = (
                all(compare_fields(row["parent"], saved).values())
                and row["parent"].get("candidate_telemetry") == saved.get("candidate_telemetry")
            )
    return checks


def snapshot_reference_checks(discoveries, reference_ledger):
    reference_by_seat = {int(row["candidate_seat"]): row
                         for row in reference_ledger.get("snapshots", [])}
    value_fields = ("own_farm", "own_private", "rival_farm", "market", "observation2_sha256")
    checks = {}
    for discovery in discoveries:
        seat = int(discovery["candidate_seat"])
        actual = discovery["snapshot"]
        reference = reference_by_seat.get(seat, {})
        for field in value_fields:
            checks[f"seat{seat}|{field}_matches_v5_reference"] = actual.get(field) == reference.get(field)
    return checks


def telemetry_errors(telemetry):
    return {key: value for key, value in (telemetry or {}).items()
            if ("error" in key.lower() or "collision" in key.lower())
            and value not in (0, False, None, "")}


def target_trace_checks(trace_path, seat, snapshot, validation):
    rows = {}
    with gzip.open(trace_path, "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            step = int(row["step"])
            if step <= 3:
                rows[step] = row
            if len(rows) == 4:
                break
    checks = {
        "trace_has_steps_0_to_3": set(rows) == {0, 1, 2, 3},
    }
    if checks["trace_has_steps_0_to_3"]:
        import importlib.util as _iu
        spec = _iu.spec_from_file_location("roman_trace_adapter", ADAPTER)
        module = _iu.module_from_spec(spec)
        spec.loader.exec_module(module)
        probe = load_prefix_probe()
        checks.update({
            "step1_hire_matches_contract": rows[1]["action"] == module._fifth_hire_action(rows[1]["observation"]),
            "step2_remap_matches_validated_action": rows[2]["action"] == validation.get("step2_action"),
            "step2_snapshot_observation_matches": (
                probe.digest_json(probe.comparable_observation(rows[2]["observation"]))
                == snapshot.get("observation2_sha256")),
        })
        inventory = rows[3]["observation"].get("private", {}).get("inventories", [])
        cows = [int(item.get("COW", 0)) for item in inventory]
        workers = [index - 1 for index, quantity in enumerate(cows)
                   if index > 0 and quantity > 0]
        checks["post_step2_two_cows_on_expected_workers"] = sum(cows) == 2 and workers == [3, 4]
    return checks


def write_jsonl(path, rows):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")
            stream.flush()


def run_once():
    manifest, panel = verify_frozen_inputs()
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    from diagnostics.stream_replay_io_20260928.fast_game_cached import play

    started = datetime.now(timezone.utc).isoformat()
    parent_results = []
    candidate_results = []
    gate_receipt = {
        "schema": "roman-shared166-current-6a-outcome-pilot-v1",
        "complete": False,
        "diagnostic_only": True,
        "fixed_tape_only": True,
        "reactive_validation": False,
        "promotion": False,
        "candidate_sha256": manifest["candidate_sha256"],
        "candidate_adapter_sha256": manifest["candidate_adapter_sha256"],
        "parent_candidate_sha256": PARENT_SHA,
        "donor_sha256": DONOR_SHA,
        "panel_sha256": manifest["panel_sha256"],
        "baseline_game_count": 0,
        "candidate_game_count": 0,
        "game_count": 0,
        "passed": False,
        "stop_phase": None,
        "gate_checks": {},
    }

    with exclusive_run(SHARED_LOCK):
        with exclusive_run(OWN_LOCK):
            verify_frozen_inputs(own_lock_held=True)
            write_once(RUN_MANIFEST, {
                "started_at_utc": started,
                "candidate_sha256": manifest["candidate_sha256"],
                "parent_candidate_sha256": PARENT_SHA,
                "candidate_adapter_sha256": manifest["candidate_adapter_sha256"],
                "donor_sha256": DONOR_SHA,
                "panel_sha256": manifest["panel_sha256"],
                "shared_lock_path": str(SHARED_LOCK),
                "worker_count": 1,
                "resume_allowed": False,
                "fixed_tape_only": True,
                "full_game_count": panel["full_game_count"],
            })

            # Establish direct 6a baselines on every target/control seat first.
            for job in panel["jobs"]:
                seat = int(job["seat"])
                parent = play(job["fixture"], PARENT, PARENT_SHA, seat)
                saved = job.get("saved_6a_reference")
                row = {
                    "fixture_id": job["fixture_id"], "seat": seat, "role": job["role"],
                    "parent_candidate_sha256": PARENT_SHA,
                    "parent": parent,
                    "matches_saved_6a_fields": (all(compare_fields(parent, saved).values())
                                                if saved is not None else None),
                    "matches_saved_6a_telemetry": (parent.get("candidate_telemetry") == saved.get("candidate_telemetry")
                                                    if saved is not None else None),
                }
                parent_results.append(row)
                with BASELINE_ROWS.open("a" if BASELINE_ROWS.exists() else "x",
                                        encoding="utf-8", newline="\n") as stream:
                    stream.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")
                    stream.flush()
                print(json.dumps({"phase": "baseline", "fixture_id": job["fixture_id"],
                                  "seat": seat, "result": parent["result"],
                                  "margin": parent["margin"], "clean": clean_game(parent)}), flush=True)

            baseline_checks = baseline_gate(parent_results, panel)
            gate_receipt["baseline_game_count"] = len(parent_results)
            gate_receipt["gate_checks"].update(baseline_checks)
            if not all(baseline_checks.values()):
                gate_receipt.update({
                    "complete": True,
                    "game_count": len(parent_results),
                    "stop_phase": "baseline_gate",
                    "parent_baselines": parent_results,
                    "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                })
                write_once(RECEIPT, gate_receipt)
                print(json.dumps({"passed": False, "stop_phase": "baseline_gate",
                                  "baseline_games": len(parent_results)}, indent=2), flush=True)
                return gate_receipt

            # Re-run both 6a opening prefixes before discovering either adapter snapshot.
            probe = load_prefix_probe()
            prefix_manifest = read(PREFIX_FREEZE)
            prefix_jobs = sorted(prefix_manifest["jobs"], key=lambda job: int(job["candidate_seat"]))
            prefix_rows = [probe.run_v5_prefix(job, f"6a_baseline_seat{int(job['candidate_seat'])}")
                           for job in prefix_jobs]
            prefix_checks = {
                f"seat{int(row['candidate_seat'])}|6a_prefix_matches_source": row.get("opening_matches_source") is True
                and all(row.get("source_checks", {}).values())
                for row in prefix_rows
            }
            write_once(PREFIX_RESULTS, {
                "parent_candidate_sha256": PARENT_SHA,
                "historical_source_parent_sha256": prefix_manifest["parent_candidate_sha256"],
                "results": prefix_rows,
                "checks": prefix_checks,
                "passed": len(prefix_rows) == 2 and all(prefix_checks.values()),
            })
            gate_receipt["gate_checks"].update(prefix_checks)
            if len(prefix_rows) != 2 or not all(prefix_checks.values()):
                gate_receipt.update({
                    "complete": True,
                    "game_count": len(parent_results),
                    "stop_phase": "6a_prefix_gate",
                    "parent_baselines": parent_results,
                    "prefix_results": prefix_rows,
                    "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                })
                write_once(RECEIPT, gate_receipt)
                return gate_receipt

            # Discover both current-6a snapshots before validating either one.
            adapter_sha = manifest["candidate_adapter_sha256"]
            discoveries = [probe.discover_adapter_snapshot(job, adapter_sha, row)
                           for job, row in zip(prefix_jobs, prefix_rows)]
            discovery_checks = {}
            for discovery in discoveries:
                seat = int(discovery["candidate_seat"])
                for name, passed in discovery.get("checks", {}).items():
                    discovery_checks[f"seat{seat}|{name}"] = bool(passed)
            reference_ledger = read(PREFIX_SNAPSHOTS)
            reference_checks = snapshot_reference_checks(discoveries, reference_ledger)
            discovery_checks.update(reference_checks)
            write_once(DISCOVERY_RESULTS, {
                "parent_candidate_sha256": PARENT_SHA,
                "adapter_sha256": adapter_sha,
                "donor_sha256": DONOR_SHA,
                "discoveries": discoveries,
                "checks": discovery_checks,
                "passed": len(discoveries) == 2 and all(discovery_checks.values()),
            })
            gate_receipt["gate_checks"].update(discovery_checks)
            if len(discoveries) != 2 or not all(discovery_checks.values()):
                gate_receipt.update({
                    "complete": True,
                    "game_count": len(parent_results),
                    "stop_phase": "snapshot_discovery",
                    "parent_baselines": parent_results,
                    "prefix_results": prefix_rows,
                    "snapshot_discovery": discoveries,
                    "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                })
                write_once(RECEIPT, gate_receipt)
                return gate_receipt

            # Only after both discoveries pass do both fresh replays validate/inject snapshots.
            validation = [probe.validate_adapter_snapshot(job, discovery["snapshot"],
                                                           discovery, adapter_sha)
                          for job, discovery in zip(prefix_jobs, discoveries)]
            validation_checks = {}
            for result in validation:
                seat = int(result["candidate_seat"])
                for name, passed in result.get("checks", {}).items():
                    validation_checks[f"seat{seat}|{name}"] = bool(passed)
            write_once(VALIDATION_RESULTS, {
                "parent_candidate_sha256": PARENT_SHA,
                "adapter_sha256": adapter_sha,
                "donor_sha256": DONOR_SHA,
                "validations": validation,
                "checks": validation_checks,
                "passed": len(validation) == 2 and all(validation_checks.values()),
            })
            gate_receipt["gate_checks"].update(validation_checks)
            if len(validation) != 2 or not all(validation_checks.values()):
                gate_receipt.update({
                    "complete": True,
                    "game_count": len(parent_results),
                    "stop_phase": "snapshot_validation",
                    "parent_baselines": parent_results,
                    "prefix_results": prefix_rows,
                    "snapshot_discovery": discoveries,
                    "snapshot_validation": validation,
                    "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                })
                write_once(RECEIPT, gate_receipt)
                return gate_receipt

            live_ledger = {
                "schema": "roman-shared166-current-6a-live-step2-snapshots-v1",
                "parent_candidate_sha256": PARENT_SHA,
                "adapter_sha256": adapter_sha,
                "donor_sha256": DONOR_SHA,
                "fixture_id": build_panel.TARGET_ID,
                "source_replay_sha256": prefix_jobs[0]["fixture"]["source_replay_sha256"],
                "opponent_tape_file_sha256": prefix_jobs[0]["opponent_tape_file_sha256"],
                "opponent_tape_payload_sha256": prefix_jobs[0]["opponent_tape_payload_sha256"],
                "snapshots": [],
            }
            for discovery in discoveries:
                snapshot = dict(discovery["snapshot"])
                snapshot["parent_candidate_sha256"] = PARENT_SHA
                snapshot["adapter_sha256"] = adapter_sha
                snapshot["donor_sha256"] = DONOR_SHA
                live_ledger["snapshots"].append(snapshot)
            write_once(LIVE_SNAPSHOTS, live_ledger)

            # Run the six current candidate games only after all prefix gates pass.
            by_validation = {int(row["candidate_seat"]): row for row in validation}
            for job in panel["jobs"]:
                seat = int(job["seat"])
                trace_path = None
                expected_step2 = None
                if job["fixture_id"] == build_panel.TARGET_ID:
                    trace_path = HERE / f"target_seat{seat}_trace.jsonl.gz"
                    expected_step2 = by_validation[seat].get("step2_action")
                candidate = play(job["fixture"], CANDIDATE, manifest["candidate_sha256"],
                                 seat, trace_path=trace_path)
                baseline = next(row["parent"] for row in parent_results
                                if row["fixture_id"] == job["fixture_id"]
                                and int(row["seat"]) == seat)
                telemetry = candidate.get("candidate_telemetry") or {}
                parent_telemetry = baseline.get("candidate_telemetry") or {}
                roman_telemetry = {key: value for key, value in telemetry.items()
                                   if key.startswith("roman_")}
                base_telemetry = {key: value for key, value in telemetry.items()
                                  if not key.startswith("roman_")}
                checks = {
                    "candidate_clean_done_done_720": clean_game(candidate),
                    "roman_errors_zero": telemetry_errors(roman_telemetry) == {}
                        and roman_telemetry.get("roman_errors") == 0,
                }
                controls_exact = None
                target_win = None
                trace_checks = {}
                if job["fixture_id"] == build_panel.TARGET_ID:
                    checks.update({
                        "roman_triggered": roman_telemetry.get("roman_public_trigger_step1") is True,
                        "parent_opening_guard": roman_telemetry.get("roman_parent_opening_guard_step1") is True,
                        "fifth_hire_action": roman_telemetry.get("roman_hire_action_step1") is True,
                        "snapshot_provenance": roman_telemetry.get("roman_snapshot_provenance") is True,
                        "step2_own_guard": roman_telemetry.get("roman_step2_own_guard") is True,
                        "step2_public_guard": roman_telemetry.get("roman_step2_public_guard") is True,
                        "step2_matches_discovery": roman_telemetry.get("roman_step2_matches_discovery") is True,
                        "donor_calls": int(roman_telemetry.get("roman_donor_calls", 0)) > 0,
                        "remapped_action_matches": roman_telemetry.get("roman_donor_action_matches") is True,
                        "cow_pickup_units": roman_telemetry.get("roman_cow_pickup_units_step3") == 2,
                        "cow_pickup_workers": roman_telemetry.get("roman_cow_pickup_workers_step3") == [3, 4],
                    })
                    trace_checks = target_trace_checks(trace_path, seat,
                                                      next(row for row in live_ledger["snapshots"]
                                                           if int(row["candidate_seat"]) == seat),
                                                      by_validation[seat])
                    checks.update(trace_checks)
                    target_win = (candidate.get("result") == "win"
                                  and float(candidate.get("margin", 0)) > 0
                                  and baseline.get("result") == "loss")
                    checks["target_win_over_6a_loss"] = target_win
                else:
                    checks.update({
                        "roman_trigger_inactive": roman_telemetry.get("roman_public_trigger_step1") is False,
                        "no_roman_hire": roman_telemetry.get("roman_hire_action_step1") is False,
                        "no_donor_calls": int(roman_telemetry.get("roman_donor_calls", 0)) == 0,
                        "base_telemetry_exact": base_telemetry == parent_telemetry,
                    })
                    equal = compare_fields(candidate, baseline)
                    controls_exact = all(equal.values())
                    checks["control_exact_to_6a"] = controls_exact
                    checks["control_remains_win"] = candidate.get("result") == "win"

                row = {
                    "fixture_id": job["fixture_id"], "seat": seat, "role": job["role"],
                    "candidate_sha256": manifest["candidate_sha256"],
                    "parent_candidate_sha256": PARENT_SHA,
                    "candidate": candidate,
                    "parent": baseline,
                    "candidate_roman_telemetry": roman_telemetry,
                    "candidate_base_telemetry_matches_parent": base_telemetry == parent_telemetry,
                    "field_equality_to_parent": compare_fields(candidate, baseline),
                    "target_win_over_parent": target_win,
                    "control_exact_to_parent": controls_exact,
                    "trace_checks": trace_checks,
                    "checks": checks,
                    "passed": all(checks.values()),
                    "trace_sha256": sha(trace_path) if trace_path else None,
                }
                candidate_results.append(row)
                with OUTCOME_ROWS.open("a" if OUTCOME_ROWS.exists() else "x",
                                       encoding="utf-8", newline="\n") as stream:
                    stream.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")
                    stream.flush()
                print(json.dumps({"phase": "candidate", "fixture_id": job["fixture_id"],
                                  "seat": seat, "result": candidate["result"],
                                  "margin": candidate["margin"], "checks_passed": all(checks.values())}),
                             flush=True)

            target_rows = [row for row in candidate_results if row["fixture_id"] == build_panel.TARGET_ID]
            control_rows = [row for row in candidate_results if row["fixture_id"] in build_panel.CONTROL_IDS]
            gate_receipt.update({
                "complete": len(parent_results) == 6 and len(candidate_results) == 6,
                "baseline_game_count": len(parent_results),
                "candidate_game_count": len(candidate_results),
                "game_count": len(parent_results) + len(candidate_results),
                "target_seats": len(target_rows),
                "target_both_seats_win": len(target_rows) == 2 and all(row["target_win_over_parent"] for row in target_rows),
                "control_seats": len(control_rows),
                "all_controls_exact_and_wins": len(control_rows) == 4 and all(
                    row["control_exact_to_parent"] and row["checks"].get("control_remains_win")
                    for row in control_rows),
                "clean_candidate_games": len(candidate_results) == 6 and all(
                    row["checks"].get("candidate_clean_done_done_720") for row in candidate_results),
                "candidate_gates_all": len(candidate_results) == 6 and all(row["passed"] for row in candidate_results),
                "parent_baselines": parent_results,
                "prefix_results": prefix_rows,
                "snapshot_discovery": discoveries,
                "snapshot_reference_checks": reference_checks,
                "snapshot_validation": validation,
                "candidate_games": candidate_results,
                "passed": len(candidate_results) == 6 and all(row["passed"] for row in candidate_results),
                "stop_phase": None,
                "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            })
            write_once(RECEIPT, gate_receipt)
            print(json.dumps({key: value for key, value in gate_receipt.items()
                              if key not in ("parent_baselines", "prefix_results", "snapshot_discovery",
                                             "snapshot_validation", "candidate_games", "gate_checks")},
                             indent=2), flush=True)
    return gate_receipt


if __name__ == "__main__":
    verify_frozen_inputs()
    result = run_once()
    if not result.get("passed"):
        raise SystemExit(1)
