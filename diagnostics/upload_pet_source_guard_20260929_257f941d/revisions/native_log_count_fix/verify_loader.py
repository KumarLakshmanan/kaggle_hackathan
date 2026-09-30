"""Guarded-candidate local direct/file loader parity check.

The package builder refuses to create bindings until the guarded 102-row
preservation receipt is complete and passed. This checker does no Kaggle or
upload operations. Games require the explicit --run flag.
"""
from __future__ import annotations

from datetime import datetime, timezone
import gc
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MANIFEST_PATH = HERE / "package_manifest.json"
FREEZE_RECEIPT = HERE / "package_freeze_receipt.json"
OUTPUT = HERE / "loader_parity.json"
FAILURE = HERE / "loader_failure.json"
OWN_LOCK = HERE / "loader.lock"
SHARED_LOCK = ROOT / "diagnostics/.shared_game_run.lock"
CANDIDATE = HERE / "main.py"

# Values are sourced from the build-time manifest. The manifest is itself
# reviewed and its digest is recorded in package_freeze_receipt.json.
PACKAGE_CONFIG = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
SOURCE_CANDIDATE = Path(PACKAGE_CONFIG["candidate_source_path"])
SOURCE_PANEL = Path(PACKAGE_CONFIG["source_panel_path"])
PRESERVATION_MANIFEST = Path(PACKAGE_CONFIG["preservation_manifest_path"])
PRESERVATION_RECEIPT = Path(PACKAGE_CONFIG["preservation_receipt_path"])
PRESERVATION_OUTCOMES = Path(PACKAGE_CONFIG["preservation_outcomes_path"])
HISTORICAL_EBF_RECEIPT = Path(PACKAGE_CONFIG["historical_ebf_receipt_path"])
ROOT_MAIN = Path(PACKAGE_CONFIG["root_main_path"])
CANDIDATE_SHA = PACKAGE_CONFIG["candidate_sha256"]
PARENT_SHA = PACKAGE_CONFIG["candidate_parent_sha256"]
ROOT_MAIN_SHA = PACKAGE_CONFIG["root_main_sha256"]
PANEL_SHA = PACKAGE_CONFIG["source_panel_sha256"]
PRESERVATION_MANIFEST_SHA = PACKAGE_CONFIG["preservation_manifest_sha256"]
PRESERVATION_RECEIPT_SHA = PACKAGE_CONFIG["preservation_receipt_sha256"]
PRESERVATION_OUTCOMES_SHA = PACKAGE_CONFIG["preservation_outcomes_sha256"]
ENTRYPOINT = PACKAGE_CONFIG["expected_entrypoint"]
ENGINE_VERSION = PACKAGE_CONFIG["engine_version"]
SELECTED = {item["fixture_id"] for item in PACKAGE_CONFIG.get("jobs", [])}
FROZEN_FIXTURE_IDS = {
    "live-114260122",
    "live-114274897",
    "top20-20-Densike-114270616",
}
EXPECTED_KEYS = {
    (item["fixture_id"], int(item["candidate_seat"]))
    for item in PACKAGE_CONFIG.get("jobs", [])
}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def require(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def check_pet_guard(telemetry, key):
    branch = telemetry.get("a44_pet_market_gate_branch72")
    require(branch == telemetry.get("bridge_selected"),
            f"step-72 recorded bridge branch differs from actual selection: {key}")
    require(branch in {"source", "shared150", "shared151"},
            f"unrecognized bridge branch at step 72: {key}: {branch!r}")
    computed = (
        branch == "source"
        and telemetry.get("a44_pet_market_gate_key72") == "PET_CAFE|M8+|C>S|G0"
        and int(telemetry.get("a44_pet_market_gate_rival_melon72", -1)) == 12
        and int(telemetry.get("a44_pet_market_gate_wheat_stock72", -1)) == 9975
    )
    require(telemetry.get("a44_pet_market_gate_active72") is computed,
            f"guard activation differs from recorded public fields: {key}")
    require(telemetry.get("a44_pet_market_gate_route72") == ("113517834" if computed else ""),
            f"Pet route differs from guard state: {key}")
    require(int(telemetry.get("a44_pet_market_gate_turns", -1)) == (647 if computed else 0),
            f"Pet call count differs from guard state: {key}")
    require(int(telemetry.get("a44_pet_market_gate_errors", -1)) == 0,
            f"Pet guard reported errors: {key}")
    if key[0] == "live-114260122":
        require(computed, f"Pet target did not activate on source branch: {key}")
    else:
        require(not computed, f"Pet guard unexpectedly activated on inactive row: {key}")
    if key[0] == "live-114274897":
        require(telemetry.get("iso_pasture_leaf_route72") == "113332529"
                and int(telemetry.get("iso_pasture_leaf_turns", -1)) == 647,
                f"Brunch pasture route changed on the pasture row: {key}")
    if key[0] == "top20-20-Densike-114270616":
        require(telemetry.get("iso_pasture_leaf_route72") == "",
                f"inactive top20 control activated the pasture leaf: {key}")


def verify_bindings():
    manifest = read_json(MANIFEST_PATH)
    require(manifest == PACKAGE_CONFIG, "package manifest changed after checker initialization")
    require(manifest.get("schema") == "pet-source-guard-upload-loader-v1", "wrong package manifest schema")
    require(manifest.get("operational_only") is True, "package is not labeled operational-only")
    require(manifest.get("research_promotion") is False, "loader package must not claim research promotion")
    require(manifest.get("candidate_sha256") == CANDIDATE_SHA, "manifest candidate mismatch")
    require(manifest.get("root_main_sha256") == ROOT_MAIN_SHA, "manifest root main mismatch")
    require(manifest.get("expected_entrypoint") == ENTRYPOINT, "manifest callable mismatch")
    require(manifest.get("engine_version") == ENGINE_VERSION, "manifest engine version mismatch")
    require(len(EXPECTED_KEYS) == int(manifest.get("job_count", -1)) == 6,
            "loader scope must contain exactly six seat jobs")
    require(SELECTED == FROZEN_FIXTURE_IDS, "frozen loader fixture set changed")
    require(EXPECTED_KEYS == {
        (fixture_id, seat) for fixture_id in FROZEN_FIXTURE_IDS for seat in (0, 1)
    }, "loader must cover both seats for all three fixtures")
    require(manifest.get("native_game_runs_planned") == 12,
            "loader scope must contain twelve direct/file runs")
    runtime = manifest.get("runtime", {})
    require(str(Path(sys.executable).resolve()) == str(Path(runtime.get("python_executable", "")).resolve()),
            "Python executable differs from frozen runtime")
    require(".".join(map(str, sys.version_info[:3])) == runtime.get("python_version"),
            "Python version differs from frozen runtime")
    for item in manifest.get("files", []):
        path = Path(item["path"])
        require(path.is_file(), f"bound file is missing: {path}")
        require(sha(path) == item["sha256"], f"bound file hash changed: {path}")

    require(sha(CANDIDATE) == CANDIDATE_SHA, "package main.py hash mismatch")
    require(sha(SOURCE_CANDIDATE) == CANDIDATE_SHA, "guard source candidate hash mismatch")
    require(sha(Path(manifest["root_backup_path"])) == CANDIDATE_SHA, "root backup hash mismatch")
    require(sha(ROOT_MAIN) == ROOT_MAIN_SHA, "root main changed")
    require(sha(SOURCE_PANEL) == PANEL_SHA, "frozen source panel hash mismatch")
    require(sha(PRESERVATION_MANIFEST) == PRESERVATION_MANIFEST_SHA,
            "preservation manifest hash mismatch")
    require(sha(PRESERVATION_RECEIPT) == PRESERVATION_RECEIPT_SHA,
            "preservation receipt hash mismatch")
    require(sha(PRESERVATION_OUTCOMES) == PRESERVATION_OUTCOMES_SHA,
            "preservation outcomes hash mismatch")

    raw = CANDIDATE.read_bytes()
    compile(raw, str(CANDIDATE), "exec")
    from kaggle_environments.agent import get_last_callable
    loaded_name = get_last_callable(raw.decode("utf-8"), path=str(CANDIDATE)).__name__
    require(loaded_name == ENTRYPOINT, f"unexpected final callable: {loaded_name}")

    preservation_manifest = read_json(PRESERVATION_MANIFEST)
    require(preservation_manifest.get("candidate_sha256") == CANDIDATE_SHA,
            "preservation manifest candidate mismatch")
    require(preservation_manifest.get("planned_games") == 102,
            "preservation manifest job count changed")
    require(preservation_manifest.get("fixed_tape_only") is True
            and preservation_manifest.get("preservation_only") is True,
            "preservation manifest scope changed")
    require(preservation_manifest.get("runner_sha256") ==
            sha(PRESERVATION_MANIFEST.parent / "verify_preservation.py"),
            "preservation runner hash differs from its frozen manifest")
    for path, digest in preservation_manifest.get("bindings", {}).items():
        require(sha(Path(path)) == digest, f"preservation manifest input changed: {path}")

    receipt = read_json(PRESERVATION_RECEIPT)
    require(receipt.get("candidate_sha256") == CANDIDATE_SHA,
            "preservation receipt candidate mismatch")
    require(receipt.get("parent_candidate_sha256") == PARENT_SHA,
            "preservation receipt parent mismatch")
    require(receipt.get("manifest_sha256") == PRESERVATION_MANIFEST_SHA,
            "preservation receipt does not bind the frozen preservation manifest")
    require(receipt.get("complete") is True and receipt.get("passed") is True,
            "preservation receipt must be complete and passed")
    require(receipt.get("fixed_tape_only") is True and receipt.get("preservation_only") is True,
            "preservation receipt scope changed")
    require(receipt.get("research_promotion") is False,
            "preservation result must not claim research promotion")
    require(receipt.get("winning_sweeps") == {"loss30": 27, "top20": 19},
            "preservation sweep gate differs from frozen criteria")
    receipt_rows = {}
    all_rows = receipt.get("games", [])
    require(len(all_rows) == 102, "preservation receipt must contain all 102 rows")
    require(all(row.get("passed") is True and all(row.get("checks", {}).values()) for row in all_rows),
            "preservation receipt contains a failed row or check")
    for row in all_rows:
        key = (row["fixture_id"], int(row["candidate_seat"]))
        require(key not in receipt_rows, f"duplicate preservation row: {key}")
        receipt_rows[key] = row

    panel = read_json(SOURCE_PANEL)
    panel_rows = {}
    for row in panel.get("games", []) + panel.get("controls", []):
        seat = row.get("candidate_seat", row.get("seat"))
        key = (row["fixture_id"], int(seat))
        if row["fixture_id"] in SELECTED:
            require(key not in panel_rows, f"duplicate source panel row: {key}")
            panel_rows[key] = row
    require(set(panel_rows) == EXPECTED_KEYS, "selected source panel rows are incomplete")
    require(EXPECTED_KEYS <= set(receipt_rows), "preservation receipt lacks selected seat rows")

    jobs = []
    for key in sorted(EXPECTED_KEYS):
        panel_row = panel_rows[key]
        preserved = receipt_rows[key]
        actual = preserved["actual"]
        fixture = panel_row["fixture"]
        require(preserved["panel"] == panel_row.get("panel"), f"preservation panel label changed: {key}")
        require(actual.get("candidate_sha256") == CANDIDATE_SHA, f"preserved candidate mismatch: {key}")
        require(actual.get("candidate_status") == actual.get("opponent_status") == "DONE",
                f"preserved status mismatch: {key}")
        require(actual.get("frames") == 720 and not actual.get("candidate_errors"),
                f"preserved game is dirty: {key}")
        telemetry = actual.get("candidate_telemetry", {})
        check_pet_guard(telemetry, key)
        expected = {
            "candidate_reward": actual["candidate_reward"],
            "opponent_reward": actual["opponent_reward"],
            "result": actual["result"],
            "candidate_status": actual["candidate_status"],
            "opponent_status": actual["opponent_status"],
            "frames": actual["frames"],
            "candidate_telemetry": telemetry,
        }
        jobs.append({
            "fixture_id": key[0],
            "candidate_seat": key[1],
            "fixture": fixture,
            "source_panel": panel_row.get("panel"),
            "preservation_row_sha256": json_sha(preserved),
            "expected": expected,
        })

    manifest_jobs = {
        (item["fixture_id"], int(item["candidate_seat"])): item
        for item in manifest.get("jobs", [])
    }
    require(set(manifest_jobs) == EXPECTED_KEYS, "manifest selected jobs are incomplete")
    for job in jobs:
        key = (job["fixture_id"], job["candidate_seat"])
        frozen = manifest_jobs[key]
        fixture = job["fixture"]
        require(frozen["seed"] == fixture["seed"], f"manifest seed mismatch: {key}")
        require(frozen["source_panel"] == job["source_panel"], f"manifest panel mismatch: {key}")
        require(frozen["source_action_tape_path"] == fixture["source_action_tape_path"],
                f"manifest tape path mismatch: {key}")
        require(frozen["source_opponent_action_sha256"] == fixture["source_opponent_action_sha256"],
                f"manifest tape digest mismatch: {key}")
        require(frozen["source_replay_path"] == fixture["source_replay_path"],
                f"manifest replay path mismatch: {key}")
        require(frozen["source_replay_sha256"] == fixture["source_replay_sha256"],
                f"manifest replay digest mismatch: {key}")
        require(frozen["trace_path"] == panel_rows[key]["trace_path"],
                f"manifest trace path mismatch: {key}")
        require(frozen["trace_sha256"] == panel_rows[key]["trace_sha256"],
                f"manifest trace digest mismatch: {key}")
        require(frozen["preservation_row_sha256"] == job["preservation_row_sha256"],
                f"manifest preservation row mismatch: {key}")
        require(frozen["expected"] == job["expected"], f"manifest expected values mismatch: {key}")
    return manifest, jobs, loaded_name


def run(job, mode):
    from paired_benchmark import (
        _load_agent, _load_module, TimedAgent, _timing_dict, make, engine_version,
    )
    from diagnostics.opening_probe_v2_20260928.qualify import errors

    require(engine_version == ENGINE_VERSION, f"runtime engine version changed: {engine_version}")
    seat = int(job["candidate_seat"])
    fixture = job["fixture"]
    tape_path = Path(fixture["source_action_tape_path"])
    tape_actions = json.loads(gzip.decompress(tape_path.read_bytes()))["actions"]
    tape_hashes = {
            hashlib.sha256(json.dumps(tape_actions, sort_keys=sort, separators=(",", ":")).encode("utf-8")).hexdigest()
        for sort in (False, True)
    }
    require(fixture["source_opponent_action_sha256"] in tape_hashes,
            f"opponent tape does not match frozen fixture: {job['fixture_id']} seat {seat}")
    opponent, opponent_timed = _load_agent("rawroute:" + str(tape_path), "pet_guard_loader_rival")
    module = None
    try:
        if mode == "file":
            candidate = str(CANDIDATE)
        else:
            module = _load_module(CANDIDATE, "pet_guard_loader_candidate")

            def call(observation, configuration):
                visible = dict(configuration)
                visible["seed"] = None
                return module.agent(observation, visible)

            candidate = TimedAgent(call)
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": fixture["seed"]}, debug=False)
        env.run([candidate, opponent] if seat == 0 else [opponent, candidate])
        final = env.steps[-1]
        bad_native_statuses = [
            {"step": step, "player": player, "status": state.status}
            for step, frame in enumerate(env.steps)
            for player, state in enumerate(frame)
            if state.status in {"ERROR", "INVALID", "TIMEOUT"}
        ]
        stderr_events = [
            {"step": step, "player": player, "stderr": str(log.get("stderr", ""))}
            for step, frame_logs in enumerate(env.logs)
            for player, log in enumerate(frame_logs)
            if str(log.get("stderr", "")).strip()
        ]
        result = {
            "mode": mode,
            "fixture_id": job["fixture_id"],
            "seat": seat,
            "seed": fixture["seed"],
            "rewards": [float(state.reward) for state in final],
            "statuses": [state.status for state in final],
            "frames": len(env.steps),
            "native_action_calls": len(env.logs),
            "native_status_errors": bad_native_statuses,
            "native_stderr_events": stderr_events,
            "actions": [[frame[player].action for player in (0, 1)] for frame in env.steps[1:]],
            "minimum_remaining_overage_seconds": min(
                float(frame[seat].observation.remainingOverageTime) for frame in env.steps
            ),
        }
        expected = job["expected"]
        require(result["statuses"] == ["DONE", "DONE"],
                f"native status failure: {job['fixture_id']} seat {seat}")
        require(result["frames"] == 720, f"native frame count failure: {job['fixture_id']} seat {seat}")
        require(result["native_action_calls"] == 719,
                f"native action call count failure: {job['fixture_id']} seat {seat}")
        require(not result["native_status_errors"],
                f"native ERROR/INVALID/TIMEOUT: {job['fixture_id']} seat {seat}")
        require(not result["native_stderr_events"], f"native stderr: {job['fixture_id']} seat {seat}")
        require(len(result["actions"]) == 719, f"expected 719 action frames: {job['fixture_id']} seat {seat}")
        require(result["minimum_remaining_overage_seconds"] >= 0,
                f"negative remaining runtime budget: {job['fixture_id']} seat {seat}")
        require(result["rewards"][seat] == expected["candidate_reward"],
                f"candidate reward differs from preservation receipt: {job['fixture_id']} seat {seat}")
        require(result["rewards"][1 - seat] == expected["opponent_reward"],
                f"opponent reward differs from preservation receipt: {job['fixture_id']} seat {seat}")
        if module is not None:
            timing = _timing_dict(candidate)
            runtime_budget = float(env.configuration.actTimeout) + float(
                env.steps[int(timing["max_step"])][seat].observation.remainingOverageTime
            )
            policy_errors = errors(module)
            telemetry = dict(getattr(module.agent, "telemetry", {}) or {})
            require(not policy_errors,
                    f"candidate policy errors: {job['fixture_id']} seat {seat}: {policy_errors}")
            require(telemetry == expected["candidate_telemetry"],
                    f"direct telemetry differs from preservation receipt: {job['fixture_id']} seat {seat}")
            check_pet_guard(telemetry, (job["fixture_id"], seat))
            telemetry_errors = {
                key: value for key, value in telemetry.items()
                if ("error" in key.lower() or "collision" in key.lower())
                and value not in (0, False, None, "")
            }
            require(not telemetry_errors,
                    f"candidate telemetry errors: {job['fixture_id']} seat {seat}: {telemetry_errors}")
            require(timing["max_ms"] < runtime_budget * 1000,
                    f"candidate exceeded native time budget: {job['fixture_id']} seat {seat}")
            result.update(timing=timing, runtime_budget_seconds=runtime_budget,
                          policy_errors=policy_errors, telemetry=telemetry,
                          telemetry_sha256=json_sha(telemetry))
        return result
    finally:
        if module is not None:
            sys.modules.pop(module.__name__, None)
        if opponent_timed is not None and opponent_timed.module_name:
            sys.modules.pop(opponent_timed.module_name, None)
        gc.collect()


def main():
    if "--static" in sys.argv:
        manifest, jobs, loaded_name = verify_bindings()
        print(json.dumps({
            "static_bindings_passed": True,
            "candidate_sha256": CANDIDATE_SHA,
            "preservation_receipt_sha256": PRESERVATION_RECEIPT_SHA,
            "selected_fixture_seats": len(jobs),
            "loader_games_executed": 0,
            "loaded_name": loaded_name,
            "research_promotion": False,
        }, indent=2))
        return
    require(sys.argv[1:] == ["--run"], "use --static for zero-game checks or --run after root approval")
    require(not OUTPUT.exists() and not FAILURE.exists(),
            "prior output exists; inspect it without rerunning")
    manifest, jobs, loaded_name = verify_bindings()
    from diagnostics.local_target_20260928.run_lock import exclusive_run

    report_rows = []
    with exclusive_run(SHARED_LOCK):
        with exclusive_run(OWN_LOCK):
            for job in jobs:
                direct = run(job, "direct")
                file_result = run(job, "file")
                require(direct["rewards"] == file_result["rewards"],
                        f"direct/file reward mismatch: {job['fixture_id']} seat {job['candidate_seat']}")
                require(direct["actions"] == file_result["actions"],
                        f"direct/file action mismatch: {job['fixture_id']} seat {job['candidate_seat']}")
                action_sha = hashlib.sha256(json.dumps(
                    file_result["actions"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
                ).encode("utf-8")).hexdigest()
                report_rows.append({
                    "fixture_id": job["fixture_id"],
                    "seat": job["candidate_seat"],
                    "seed": job["fixture"]["seed"],
                    "candidate_sha256": CANDIDATE_SHA,
                    "source_opponent_action_sha256": job["fixture"]["source_opponent_action_sha256"],
                    "all_719_actions_both_players_equal": True,
                    "actions_sha256": action_sha,
                    "direct": {key: value for key, value in direct.items() if key != "actions"},
                    "file": {key: value for key, value in file_result.items() if key != "actions"},
                })
                gc.collect()
            require(sha(CANDIDATE) == CANDIDATE_SHA, "candidate changed during loader verification")
            require(sha(ROOT_MAIN) == ROOT_MAIN_SHA, "root main changed during loader verification")
            report = {
                "schema": "pet-source-guard-local-direct-file-loader-v1",
                "passed": True,
                "operational_only": True,
                "research_promotion": False,
                "candidate_sha256": CANDIDATE_SHA,
                "root_main_sha256": ROOT_MAIN_SHA,
                "package_manifest_sha256": sha(MANIFEST_PATH),
                "preservation_receipt_sha256": PRESERVATION_RECEIPT_SHA,
                "preservation_status": "passed",
                "research_status": "not_promoted_by_loader_result",
                "loaded_name": loaded_name,
                "engine_version": ENGINE_VERSION,
                "fixture_seats": len(jobs),
                "native_game_runs": len(jobs) * 2,
                "all_runs_done_done_720": True,
                "all_runs_719_actions_and_no_native_errors": True,
                "all_runs_no_policy_or_telemetry_errors": True,
                "all_direct_file_719_action_pairs_equal": True,
                "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                "rows": report_rows,
                "qualification_note": "Operational file-loader result only; does not establish reactive research promotion or leaderboard gain.",
            }
            with OUTPUT.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(report, stream, indent=2, ensure_ascii=True)
                stream.write("\n")
    print(json.dumps({key: value for key, value in report.items() if key != "rows"}, indent=2))


if __name__ == "__main__":
    main()
