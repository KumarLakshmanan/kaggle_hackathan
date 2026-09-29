from __future__ import annotations

"""One-shot sequential four-game fixed-action-tape outcome pilot."""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CANDIDATE_DIR = HERE.parent
SIXD_DIR = ROOT / "diagnostics" / "a44_goose4_smoothie_source_20260929"
MANIFEST_PATH = HERE / "outcome_manifest.json"
PREFLIGHT_PATH = HERE / "static_preflight.json"
FREEZE_RECEIPT_PATH = HERE / "freeze_receipt.json"
RUN_DIR = HERE / "run_001"
OWN_LOCK_PATH = HERE / ".outcome_run_20260929.lock"
SHARED_LOCK_PATH = ROOT / "diagnostics" / ".shared_game_run.lock"
EXPECTED_CANDIDATE_SHA = "5b4ef52d19cb8ffb310b2bb067c725810241668667a0b5b468ac09b6b9215506"
EXPECTED_6D_SHA = "6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9"
EXPECTED_A44_SHA = "a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f"
LEAF_KEY = "BRUNCH_SPOT|M8+|C>S|G+"
LEAF_ROUTE = "113332529"
RUN_ID = "a44_goose4_smoothie_pasture_terminal_4game_001"
CONTROL_FIELDS = (
    "result", "candidate_reward", "opponent_reward", "margin",
    "candidate_status", "opponent_status", "frames",
)
REQUIRED_FILES = ("run_manifest.json", "attempts.jsonl", "outcomes.jsonl", "outcome_receipt.json")
sys.path.insert(0, str(ROOT))

from diagnostics.local_target_20260928.run_lock import exclusive_run
from diagnostics.stream_replay_io_20260928.fast_game_cached import play


def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_once(path: Path, value: dict) -> None:
    data = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    with Path(path).open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def append_jsonl(path: Path, value: dict) -> None:
    data = (json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    with Path(path).open("ab") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def verify_frozen() -> tuple[dict, dict, dict]:
    manifest = read_json(MANIFEST_PATH)
    preflight = read_json(PREFLIGHT_PATH)
    receipt = read_json(FREEZE_RECEIPT_PATH)
    require(manifest.get("schema") == "a44-goose4-smoothie-pasture-terminal-outcome-manifest-v1",
            "outcome manifest schema mismatch")
    require(manifest.get("candidate", {}).get("sha256") == EXPECTED_CANDIDATE_SHA
            and sha256(CANDIDATE_DIR / "candidate.py") == EXPECTED_CANDIDATE_SHA,
            "candidate hash mismatch")
    require(manifest.get("parent_6d_candidate", {}).get("sha256") == EXPECTED_6D_SHA
            and sha256(SIXD_DIR / "candidate.py") == EXPECTED_6D_SHA,
            "exact 6d parent hash mismatch")
    require(manifest.get("baseline", {}).get("combined_candidate_sha256") == EXPECTED_6D_SHA,
            "baseline is not the exact 6d combined receipt")
    require(manifest.get("job_count") == 4 and manifest.get("workers") == 1,
            "job matrix or one-worker requirement mismatch")
    require(manifest.get("runner", {}).get("resume_allowed") is False
            and manifest.get("runner", {}).get("overwrite_allowed") is False,
            "runner policy must forbid resume and overwrite")
    require(manifest.get("runner", {}).get("shared_lock_path") == "diagnostics/.shared_game_run.lock",
            "shared game lock path mismatch")
    require(manifest.get("runner", {}).get("sha256") == sha256(HERE / "run_outcomes.py"),
            "outcome runner hash mismatch")
    require(manifest.get("runner", {}).get("builder_sha256") == sha256(HERE / "build_outcome.py"),
            "outcome builder hash mismatch")
    for path_text, digest in manifest["file_bindings"].items():
        path = Path(path_text)
        require(path.is_file() and sha256(path) == digest, f"frozen input changed: {path}")
    require(preflight.get("passed") is True and preflight.get("static_only") is True
            and preflight.get("agent_calls") == 0 and preflight.get("native_transitions") == 0,
            "static preflight did not pass without transitions")
    require(preflight.get("manifest_sha256") == sha256(MANIFEST_PATH)
            and preflight.get("runner_sha256") == sha256(HERE / "run_outcomes.py"),
            "static preflight binding mismatch")
    require(receipt.get("static_freeze_passed") is True
            and receipt.get("manifest_sha256") == sha256(MANIFEST_PATH)
            and receipt.get("preflight_sha256") == sha256(PREFLIGHT_PATH)
            and receipt.get("runner_sha256") == sha256(HERE / "run_outcomes.py"),
            "freeze receipt mismatch")
    require(receipt.get("simulator_jobs_run") == 0
            and receipt.get("native_transitions") == 0
            and receipt.get("full_game_outcomes_run") is False,
            "freeze receipt claims outcomes")

    combined_path = Path(manifest["baseline"]["path"])
    combined = read_json(combined_path)
    require(combined.get("complete") is True and combined.get("fixed_tape_only") is True
            and combined.get("candidate_sha256") == EXPECTED_6D_SHA,
            "bound 6d combined baseline is invalid")
    baselines = {(r["fixture_id"], int(r["candidate_seat"])): r for r in combined["games"]}
    require(len(baselines) == 208, "exact 6d combined baseline no longer has 208 seat rows")
    for job in manifest["jobs"]:
        base = baselines[(job["fixture_id"], int(job["seat"]))]
        expected = job["baseline_6d"]
        require({field: base.get(field) for field in CONTROL_FIELDS} == expected,
                f"6d baseline row differs from frozen plan: {job['job_id']}")
    return manifest, combined, baselines


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def evaluate_outcome(row: dict, job: dict, baseline: dict) -> dict:
    telemetry = row.get("candidate_telemetry") or {}
    target = job["expected_step72"]
    step1 = job["expected_step1_public"]
    done = (
        row.get("candidate_status") == "DONE"
        and row.get("opponent_status") == "DONE"
        and row.get("frames") == 720
    )
    telemetry_checks = {
        "observation1_requested_source": telemetry.get("pasture_guard_requested_step1") == "source",
        "observation1_selected_source": telemetry.get("pasture_guard_selected_step1") == "source",
        "observation1_hand_count": telemetry.get("pasture_guard_rival_hands_step1") == step1["rival_hands"],
        "observation1_pasture_count": telemetry.get("pasture_guard_rival_pastures_step1") == step1["rival_pastures"],
        "bridge_requested_source": telemetry.get("bridge_requested") == "source",
        "bridge_selected_source": telemetry.get("bridge_selected") == "source",
        "route_map_reset_matches_6d": telemetry.get("pasture_guard_reset_route_map_matches") is True,
        "source_branch_at_step72": telemetry.get("pasture_brunch_branch72") == target["branch"],
        "runtime_step72_key": telemetry.get("pasture_brunch_key72") == target["key"],
        "leaf_route": telemetry.get("pasture_brunch_route72", "") == target["route"],
        "leaf_active_turns": telemetry.get("pasture_brunch_turns") == target["active_turns"],
        "leaf_errors_zero": telemetry.get("pasture_brunch_errors", 0) == 0,
        "bridge_errors_zero": telemetry.get("bridge_errors", 0) == 0,
        "bridge_common_failure_zero": telemetry.get("bridge_common_failed", 0) == 0,
        "bridge_guard_refusal_zero": telemetry.get("bridge_guard_refusals", 0) == 0,
        "bridge_source_guard_failure_zero": telemetry.get("bridge_source_guard_failed", 0) == 0,
        "goose4_errors_zero": telemetry.get("a44_goose4_errors", 0) == 0,
        "smoothie_errors_zero": telemetry.get("a44_smoothie_errors", 0) == 0,
    }
    errors_empty = not row.get("candidate_errors") and not row.get("opponent_errors")
    target_outcome = (
        row.get("result") == "win"
        and float(row.get("margin", 0)) > 0
    ) if job["role"] == "THIRD" else all(
        row.get(field) == baseline.get(field) for field in CONTROL_FIELDS
    )
    return {
        "done_done_720": done,
        "candidate_and_opponent_errors_empty": errors_empty,
        "telemetry": telemetry_checks,
        "THIRD_both_seat_win_gate": target_outcome if job["role"] == "THIRD" else None,
        "ChrisTu_exact_6d_control_gate": target_outcome if job["role"] == "ChrisTu" else None,
        "passed": done and errors_empty and all(telemetry_checks.values()) and target_outcome,
    }


def run_once() -> dict:
    require(not RUN_DIR.exists(), f"run directory already exists; resume is forbidden: {RUN_DIR}")
    manifest, combined, baselines = verify_frozen()
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    require(not any((RUN_DIR / name).exists() for name in REQUIRED_FILES),
            "run output appeared before initialization")
    write_once(RUN_DIR / "run_manifest.json", {
        "run_id": RUN_ID,
        "diagnostic_only": True,
        "fixed_action_tape_only": True,
        "candidate_sha256": EXPECTED_CANDIDATE_SHA,
        "parent_6d_candidate_sha256": EXPECTED_6D_SHA,
        "outcome_manifest_sha256": sha256(MANIFEST_PATH),
        "outcome_runner_sha256": sha256(HERE / "run_outcomes.py"),
        "static_preflight_sha256": sha256(PREFLIGHT_PATH),
        "prefix_result_sha256": manifest["prefix_proof"]["result_sha256"],
        "sixd_combined_baseline_sha256": manifest["baseline"]["sha256"],
        "workers": 1,
        "resume_allowed": False,
        "shared_lock_path": str(SHARED_LOCK_PATH),
        "study_lock_path": str(OWN_LOCK_PATH),
        "jobs": manifest["jobs"],
        "outcome_gates_frozen_before_run": manifest["outcome_gates_frozen_before_run"],
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    for name in ("attempts.jsonl", "outcomes.jsonl"):
        with (RUN_DIR / name).open("xb") as stream:
            stream.flush()
            os.fsync(stream.fileno())

    candidate_path = CANDIDATE_DIR / "candidate.py"
    outcome_rows = []
    for index, job in enumerate(manifest["jobs"], start=1):
        require(not RUN_DIR.joinpath("outcome_receipt.json").exists(),
                "receipt appeared during one-shot run")
        baseline = baselines[(job["fixture_id"], int(job["seat"]))]
        fixture = dict(job["fixture"])
        fixture.update(fixture_id=job["fixture_id"], seed=int(job["seed"]))
        append_jsonl(RUN_DIR / "attempts.jsonl", {
            "event": "job_started",
            "run_id": RUN_ID,
            "job_index": index,
            "fixture_id": job["fixture_id"],
            "seat": int(job["seat"]),
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        try:
            row = play(fixture, candidate_path, EXPECTED_CANDIDATE_SHA, int(job["seat"]))
        except BaseException as exc:
            append_jsonl(RUN_DIR / "attempts.jsonl", {
                "event": "job_failed",
                "run_id": RUN_ID,
                "job_index": index,
                "fixture_id": job["fixture_id"],
                "seat": int(job["seat"]),
                "exception_type": type(exc).__name__,
                "exception": str(exc),
                "failed_at_utc": datetime.now(timezone.utc).isoformat(),
            })
            raise
        row.update(
            run_id=RUN_ID,
            job_id=job["job_id"],
            fixture_id=job["fixture_id"],
            candidate_seat=int(job["seat"]),
            panel=job["panel"],
            role=job["role"],
            candidate_sha256=EXPECTED_CANDIDATE_SHA,
            parent_6d_candidate_sha256=EXPECTED_6D_SHA,
            baseline_6d=job["baseline_6d"],
            delta_margin_vs_6d=float(row["margin"]) - float(baseline["margin"]),
        )
        row["outcome_gates"] = evaluate_outcome(row, job, baseline)
        append_jsonl(RUN_DIR / "outcomes.jsonl", row)
        append_jsonl(RUN_DIR / "attempts.jsonl", {
            "event": "job_finished",
            "run_id": RUN_ID,
            "job_index": index,
            "fixture_id": job["fixture_id"],
            "seat": int(job["seat"]),
            "result": row.get("result"),
            "margin": row.get("margin"),
            "gates_passed": row["outcome_gates"]["passed"],
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        outcome_rows.append(row)
        print("pasture_terminal_outcome", index, "/ 4", job["fixture_id"],
              job["seat"], row.get("result"), row.get("margin"),
              "gates", row["outcome_gates"]["passed"], flush=True)

    require(len(outcome_rows) == 4, "four terminal outcomes were not recorded")
    expected_keys = [(job["fixture_id"], int(job["seat"])) for job in manifest["jobs"]]
    actual_keys = [(row["fixture_id"], int(row["candidate_seat"])) for row in outcome_rows]
    require(actual_keys == expected_keys, "terminal outcomes do not match the frozen job order")
    third = [row for row in outcome_rows if row["role"] == "THIRD"]
    christu = [row for row in outcome_rows if row["role"] == "ChrisTu"]
    receipt = {
        "schema": "a44-goose4-smoothie-pasture-terminal-outcome-result-v1",
        "complete": True,
        "diagnostic_only": True,
        "fixed_action_tape_only": True,
        "promotion": False,
        "run_id": RUN_ID,
        "candidate_sha256": EXPECTED_CANDIDATE_SHA,
        "parent_6d_candidate_sha256": EXPECTED_6D_SHA,
        "outcome_manifest_sha256": sha256(MANIFEST_PATH),
        "outcome_runner_sha256": sha256(HERE / "run_outcomes.py"),
        "prefix_result_sha256": manifest["prefix_proof"]["result_sha256"],
        "sixd_combined_baseline_sha256": manifest["baseline"]["sha256"],
        "all_games_clean": all(row["outcome_gates"]["done_done_720"]
                               and row["outcome_gates"]["candidate_and_opponent_errors_empty"]
                               for row in outcome_rows),
        "THIRD_both_seats_won": len(third) == 2 and all(
            row["result"] == "win" and row["margin"] > 0 for row in third
        ),
        "ChrisTu_controls_exactly_match_6d": len(christu) == 2 and all(
            all(row[field] == row["baseline_6d"][field] for field in CONTROL_FIELDS)
            for row in christu
        ),
        "Brunch_leaf_active_only_on_THIRD": (
            all(row["candidate_telemetry"].get("pasture_brunch_route72") == LEAF_ROUTE
                for row in third)
            and all(row["candidate_telemetry"].get("pasture_brunch_route72", "") == ""
                    for row in christu)
        ),
        "all_outcome_gates_passed": all(row["outcome_gates"]["passed"] for row in outcome_rows),
        "games": [{
            "fixture_id": row["fixture_id"],
            "seat": row["candidate_seat"],
            "role": row["role"],
            "result": row["result"],
            "candidate_reward": row["candidate_reward"],
            "opponent_reward": row["opponent_reward"],
            "margin": row["margin"],
            "delta_margin_vs_6d": row["delta_margin_vs_6d"],
            "candidate_status": row["candidate_status"],
            "opponent_status": row["opponent_status"],
            "frames": row["frames"],
            "pasture_brunch_key72": row["candidate_telemetry"].get("pasture_brunch_key72"),
            "pasture_brunch_route72": row["candidate_telemetry"].get("pasture_brunch_route72", ""),
            "pasture_brunch_turns": row["candidate_telemetry"].get("pasture_brunch_turns"),
            "gates_passed": row["outcome_gates"]["passed"],
        } for row in outcome_rows],
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_once(RUN_DIR / "outcome_receipt.json", receipt)
    return receipt


def main() -> None:
    require(len(sys.argv) == 1, "this frozen one-shot runner accepts no arguments or resume mode")
    require(not RUN_DIR.exists(), f"run directory already exists; no-resume policy: {RUN_DIR}")
    require(not OWN_LOCK_PATH.exists(), f"study lock exists; stale-lock review is required: {OWN_LOCK_PATH}")
    require(not SHARED_LOCK_PATH.exists(), f"shared game lock exists: {SHARED_LOCK_PATH}")
    verify_frozen()
    with exclusive_run(OWN_LOCK_PATH):
        with exclusive_run(SHARED_LOCK_PATH):
            require(not RUN_DIR.exists(), f"run directory appeared while waiting for locks: {RUN_DIR}")
            result = run_once()
    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)
    if not result["all_outcome_gates_passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
