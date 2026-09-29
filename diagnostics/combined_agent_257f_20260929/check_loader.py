"""Static-preflight and direct/Kaggle file-loader parity checker.

This tool is operational evidence only. ``--static`` parses the candidate as
AST and validates frozen fixture/input bindings without importing or executing
the candidate. ``--run`` performs the eight explicitly bound local games after
the caller has authorized them. It does not upload anything.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import ExitStack
from datetime import datetime, timezone
import gzip
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import sys
import traceback
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PANEL = ROOT / "diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/panel.json"
PANEL_SHA256 = "fee3b1d5f93cd295c28dd8d0c04ea672806dbb55e2b59999853a9f969c0fb90d"
ENGINE_VERSION = "1.32.7"
ROLE_BY_FIXTURE = {
    "live-114218866": "target_pensukesan",
    "live-114249897": "control_dieter",
}
SHARED_LOCK = ROOT / "diagnostics/.shared_game_run.lock"
BAD_STATUSES = {"ERROR", "INVALID", "TIMEOUT"}
OUTPUT_NAMES = (
    "manifest.json",
    "runs.jsonl",
    "action_traces.jsonl",
    "outcomes.jsonl",
    "receipt.json",
    "failure.json",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(Path(path).read_bytes())


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False)


def json_sha(value: Any) -> str:
    return sha_bytes(canonical_json(value).encode("utf-8"))


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)


def source_final_callable(candidate: Path) -> str:
    """Return the final top-level callable definition without executing source."""
    source = candidate.read_bytes().decode("utf-8-sig")
    tree = ast.parse(source, filename=str(candidate))
    callable_defs = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    require(callable_defs, "candidate contains no top-level callable definition")
    final_node = callable_defs[-1]
    require(isinstance(final_node, (ast.FunctionDef, ast.AsyncFunctionDef)),
            f"AST final callable {final_node.name!r} is not a function definition")
    return final_node.name


def fixture_binding(fixture: dict[str, Any]) -> tuple[Any, ...]:
    fields = (
        "fixture_id", "seed", "source_replay_path", "source_replay_sha256",
        "source_action_tape_path", "source_opponent_action_sha256",
    )
    return tuple(fixture.get(name) for name in fields)


def add_file_binding(bindings: dict[str, str], path: Path, label: str) -> Path:
    resolved = Path(path).resolve(strict=True)
    bindings[str(resolved)] = sha(resolved)
    return resolved


def verify_static(candidate_arg: str, expected_sha: str, output_arg: str) -> dict[str, Any]:
    candidate = Path(candidate_arg).expanduser().resolve(strict=True)
    output = Path(output_arg).expanduser()
    if not output.is_absolute():
        output = ROOT / output
    output = output.resolve()
    expected_sha = expected_sha.lower()
    require(len(expected_sha) == 64 and all(c in "0123456789abcdef" for c in expected_sha),
            "--sha256 must be 64 hexadecimal characters")
    require(candidate.is_file(), f"candidate is not a file: {candidate}")
    require(candidate != (ROOT / "main.py").resolve(),
            "loader check must use the standalone candidate, not root main.py")
    actual_candidate_sha = sha(candidate)
    require(actual_candidate_sha == expected_sha,
            f"candidate hash mismatch: expected {expected_sha}, found {actual_candidate_sha}")
    final_callable = source_final_callable(candidate)

    require(PANEL.is_file(), f"frozen source panel missing: {PANEL}")
    panel_sha = sha(PANEL)
    require(panel_sha == PANEL_SHA256, "frozen source panel hash mismatch")
    panel = read_json(PANEL)
    panel_rows: dict[tuple[str, int], dict[str, Any]] = {}
    for collection in ("games", "controls"):
        for row in panel.get(collection, []):
            fixture = row.get("fixture", {})
            fixture_id = fixture.get("fixture_id")
            if fixture_id not in ROLE_BY_FIXTURE:
                continue
            seat = int(row.get("candidate_seat", row.get("seat", -1)))
            key = (fixture_id, seat)
            require(key not in panel_rows, f"duplicate frozen fixture seat: {key}")
            panel_rows[key] = row
    expected_keys = {
        (fixture_id, seat)
        for fixture_id in ROLE_BY_FIXTURE
        for seat in (0, 1)
    }
    require(set(panel_rows) == expected_keys,
            f"panel must bind both seats of exactly target/control: {sorted(panel_rows)}")

    bindings: dict[str, str] = {}
    add_file_binding(bindings, candidate, "candidate")
    add_file_binding(bindings, PANEL, "source panel")
    add_file_binding(bindings, Path(__file__), "checker")
    jobs: list[dict[str, Any]] = []
    for fixture_id, seat in sorted(expected_keys):
        row = panel_rows[(fixture_id, seat)]
        fixture = dict(row["fixture"])
        role = ROLE_BY_FIXTURE[fixture_id]
        require(int(fixture["seed"]) > 0, f"invalid fixture seed: {fixture_id}")
        tape_path = add_file_binding(bindings, Path(fixture["source_action_tape_path"]), "action tape")
        replay_path = add_file_binding(bindings, Path(fixture["source_replay_path"]), "source replay")
        trace_path = add_file_binding(bindings, Path(row["trace_path"]), "panel trace")
        replay_content_sha = sha_bytes(gzip.decompress(replay_path.read_bytes()))
        require(replay_content_sha == fixture["source_replay_sha256"],
                f"source replay hash mismatch: {fixture_id}")
        require(sha(trace_path) == row["trace_sha256"],
                f"panel trace hash mismatch: {fixture_id} seat {seat}")
        tape_actions = json.loads(gzip.decompress(tape_path.read_bytes()))["actions"]
        require(len(tape_actions) == 719,
                f"opponent tape is not 719 actions: {fixture_id}: {len(tape_actions)}")
        tape_hashes = {
            json_sha(tape_actions),
            sha_bytes(json.dumps(tape_actions, sort_keys=False, separators=(",", ":"),
                                 ensure_ascii=True, allow_nan=False).encode("utf-8")),
        }
        require(fixture["source_opponent_action_sha256"] in tape_hashes,
                f"source opponent action digest mismatch: {fixture_id}")
        jobs.append({
            "fixture_id": fixture_id,
            "role": role,
            "candidate_seat": seat,
            "panel_label": row.get("panel"),
            "fixture": fixture,
            "trace_path": str(trace_path),
            "trace_sha256": row["trace_sha256"],
            "tape_file_sha256": sha(tape_path),
            "replay_file_sha256": sha(replay_path),
            "replay_content_sha256": replay_content_sha,
        })

    require(len(jobs) == 4, "loader scope must contain exactly four fixture-seat cases")
    require({job["role"] for job in jobs} == {"target_pensukesan", "control_dieter"},
            "target/control role bindings changed")
    return {
        "candidate_path": str(candidate),
        "candidate_sha256": actual_candidate_sha,
        "expected_sha256": expected_sha,
        "ast_final_callable": final_callable,
        "output_path": str(output),
        "output_exists": output.exists(),
        "source_panel_path": str(PANEL.resolve()),
        "source_panel_sha256": panel_sha,
        "jobs": jobs,
        "bindings": bindings,
    }


def runtime_bindings(candidate: Path, static: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    """Import only the local engine/harness, never the candidate, for run metadata."""
    import paired_benchmark
    import kaggle_environments
    import kaggle_environments.agent as kaggle_agent
    import kaggle_environments.core as kaggle_core

    require(paired_benchmark.engine_version == ENGINE_VERSION,
            f"engine version changed: {paired_benchmark.engine_version}")
    bindings = dict(static["bindings"])
    for path in (
        Path(paired_benchmark.__file__),
        ROOT / "raw_route_agent.py",
        ROOT / "diagnostics/local_target_20260928/run_lock.py",
        Path(kaggle_environments.__file__),
        Path(kaggle_agent.__file__),
        Path(kaggle_core.__file__),
    ):
        add_file_binding(bindings, path, "runtime helper")
    package_root = Path(kaggle_environments.__file__).resolve().parent
    for relative in (
        "utils.py",
        "envs/kaggriculture/kaggriculture.py",
        "envs/kaggriculture/kaggriculture.json",
    ):
        path = package_root / relative
        add_file_binding(bindings, path, "engine/game input")
    runtime = {
        "python_executable": str(Path(sys.executable).resolve()),
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "engine_version": paired_benchmark.engine_version,
        "paired_benchmark_path": str(Path(paired_benchmark.__file__).resolve()),
        "kaggle_agent_path": str(Path(kaggle_agent.__file__).resolve()),
        "kaggle_core_path": str(Path(kaggle_core.__file__).resolve()),
    }
    return bindings, runtime


def telemetry_from(function: Any, module: Any = None) -> dict[str, Any] | None:
    telemetry = getattr(function, "telemetry", None)
    if not isinstance(telemetry, dict) and module is not None:
        policy_function = getattr(module, "agent", None)
        telemetry = getattr(policy_function, "telemetry", None)
        if not isinstance(telemetry, dict):
            telemetry = getattr(module, "telemetry", None)
    if not isinstance(telemetry, dict):
        namespace = getattr(function, "__globals__", {})
        if isinstance(namespace, dict):
            telemetry = namespace.get("telemetry")
            if not isinstance(telemetry, dict):
                telemetry = getattr(namespace.get("agent"), "telemetry", None)
    if not isinstance(telemetry, dict):
        return None
    # Enforce serializability and produce a detached JSON-safe snapshot.
    return json.loads(canonical_json(telemetry))


def telemetry_errors(telemetry: dict[str, Any]) -> dict[str, Any]:
    return {
        str(key): value
        for key, value in telemetry.items()
        if ("error" in str(key).lower() or "collision" in str(key).lower())
        and value not in (0, False, None, "", [], {})
    }


def state_observation(state: Any) -> Any:
    return value(state, "observation", {}) or {}


def run_one(job: dict[str, Any], mode: str, candidate: Path,
            entrypoint: str) -> tuple[dict[str, Any], list[Any]]:
    from paired_benchmark import _load_agent, _load_module, TimedAgent, _timing_dict, make

    seat = int(job["candidate_seat"])
    fixture = job["fixture"]
    tape_path = Path(fixture["source_action_tape_path"])
    tape_actions = json.loads(gzip.decompress(tape_path.read_bytes()))["actions"]
    expected_tape_hashes = {json_sha(tape_actions)}
    expected_tape_hashes.add(sha_bytes(json.dumps(
        tape_actions, sort_keys=False, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")))
    require(fixture["source_opponent_action_sha256"] in expected_tape_hashes,
            f"bound tape changed before execution: {job['fixture_id']}")
    opponent, opponent_timed = _load_agent("rawroute:" + str(tape_path), "loader_audit_rival")
    module = None
    candidate_timed = None
    captured_file_callables: list[Any] = []
    kaggle_agent_module = None
    original_get_last_callable = None
    try:
        if mode == "direct":
            module = _load_module(candidate, "loader_audit_candidate")
            # The direct arm invokes the module's policy function when present.
            # The file arm separately verifies Kaggle's actual final callable,
            # which may be a thin named wrapper around this policy function.
            actual_direct_callable = getattr(module, "agent", None)
            if not callable(actual_direct_callable):
                actual_direct_callable = getattr(module, entrypoint, None)
            require(callable(actual_direct_callable),
                    "direct module has neither callable agent nor final entrypoint")

            def invoke(observation: Any, configuration: Any) -> Any:
                visible = dict(configuration)
                visible["seed"] = None
                return actual_direct_callable(observation, visible)

            candidate_timed = TimedAgent(invoke)
            candidate_arg: Any = candidate_timed
            callable_for_telemetry = actual_direct_callable
        else:
            import kaggle_environments.agent as kaggle_agent_module
            original_get_last_callable = kaggle_agent_module.get_last_callable
            expected_candidate_path = str(candidate.resolve())

            def capture_loader_callable(raw: str, fallback: Any = None,
                                        path: str | None = None) -> Any:
                actual = original_get_last_callable(raw, fallback=fallback, path=path)
                if path is not None:
                    try:
                        same_path = str(Path(path).resolve()) == expected_candidate_path
                    except OSError:
                        same_path = False
                    if same_path:
                        captured_file_callables.append(actual)
                return actual

            kaggle_agent_module.get_last_callable = capture_loader_callable
            candidate_arg = str(candidate.resolve())
            callable_for_telemetry = None

        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": fixture["seed"]},
                   debug=False)
        agents = [candidate_arg, opponent] if seat == 0 else [opponent, candidate_arg]
        try:
            env.run(agents)
        finally:
            if kaggle_agent_module is not None and original_get_last_callable is not None:
                kaggle_agent_module.get_last_callable = original_get_last_callable
                kaggle_agent_module = None

        if mode == "file":
            require(len(captured_file_callables) == 1,
                    f"Kaggle loader captured {len(captured_file_callables)} candidate callables")
            callable_for_telemetry = captured_file_callables[0]
            require(getattr(callable_for_telemetry, "__name__", None) == entrypoint,
                    f"Kaggle final callable mismatch: {getattr(callable_for_telemetry, '__name__', None)!r}")
            code = getattr(callable_for_telemetry, "__code__", None)
            require(code is not None and Path(code.co_filename).resolve() == candidate.resolve(),
                    "Kaggle loader callable was not defined by the bound candidate source")
        require(callable_for_telemetry is not None,
                "candidate callable was not available for telemetry capture")

        final = env.steps[-1]
        rewards = [float(value(state, "reward", 0.0) or 0.0) for state in final]
        statuses = [str(value(state, "status", "UNKNOWN")) for state in final]
        native_status_errors = [
            {"frame": frame_index, "player": player,
             "status": str(value(state, "status", "UNKNOWN"))}
            for frame_index, frame in enumerate(env.steps)
            for player, state in enumerate(frame)
            if str(value(state, "status", "UNKNOWN")) in BAD_STATUSES
        ]
        stderr_events: list[dict[str, Any]] = []
        duration_records: dict[int, list[dict[str, Any]]] = {0: [], 1: []}
        malformed_duration_records: list[dict[str, Any]] = []
        for log_index, frame_logs in enumerate(env.logs):
            for player in (0, 1):
                if len(frame_logs) <= player or not isinstance(frame_logs[player], dict):
                    continue
                log = frame_logs[player]
                if str(log.get("stderr", "")).strip():
                    stderr_events.append({"log_index": log_index, "player": player,
                                          "stderr": str(log["stderr"])})
                if "duration" in log:
                    try:
                        duration = float(log["duration"])
                        require(math.isfinite(duration) and duration >= 0,
                                f"invalid native duration in log {log_index}, player {player}")
                        duration_records[player].append({
                            "log_index": log_index,
                            "duration_seconds": duration,
                        })
                    except Exception as error:
                        malformed_duration_records.append({
                            "log_index": log_index, "player": player,
                            "duration": repr(log.get("duration")), "error": str(error),
                        })

        actions = [
            [frame[player].action for player in (0, 1)]
            for frame in env.steps[1:]
        ]
        require(len(actions) == 719, f"native action frame count is {len(actions)}, expected 719")
        require(len(env.steps) == 720, f"native frame count is {len(env.steps)}, expected 720")
        require(statuses == ["DONE", "DONE"], f"final native statuses are {statuses}")
        require(not native_status_errors, f"native status errors: {native_status_errors[:4]}")
        require(not stderr_events, f"native stderr events: {stderr_events[:4]}")
        require(not malformed_duration_records,
                f"malformed native duration records: {malformed_duration_records[:4]}")
        call_counts = {player: len(duration_records[player]) for player in (0, 1)}
        require(call_counts == {0: 719, 1: 719},
                f"native duration-log call counts are {call_counts}, expected 719 per player")

        overage_trace: list[float] = []
        for frame_index, frame in enumerate(env.steps):
            remaining = value(state_observation(frame[seat]), "remainingOverageTime", None)
            require(remaining is not None,
                    f"native remainingOverageTime missing at frame {frame_index}")
            remaining = float(remaining)
            require(math.isfinite(remaining),
                    f"non-finite native remainingOverageTime at frame {frame_index}")
            overage_trace.append(remaining)
        require(min(overage_trace) >= 0,
                f"negative native remainingOverageTime: {min(overage_trace)}")

        timeout = float(value(env.configuration, "actTimeout", 0.0) or 0.0)
        require(timeout > 0, f"native actTimeout is invalid: {timeout}")
        candidate_durations = duration_records[seat]
        max_native = max(candidate_durations, key=lambda item: item["duration_seconds"])
        max_record = max_native["duration_seconds"]
        max_log_index = int(max_native["log_index"])
        # reset contributes logs[0]; logs[1] is action step 0. Preserve the
        # actual pre-call overage and timeout alongside the native duration.
        action_step = max(0, min(max_log_index - 1, len(overage_trace) - 1))
        available_at_max = timeout + overage_trace[action_step]
        require(max_record <= available_at_max + 0.00001,
                f"native max call {max_record:.6f}s exceeds available {available_at_max:.6f}s")

        telemetry = telemetry_from(callable_for_telemetry, module)
        require(isinstance(telemetry, dict), "candidate telemetry was not captured as a dictionary")
        found_telemetry_errors = telemetry_errors(telemetry)
        require(not found_telemetry_errors,
                f"candidate telemetry reports errors/collisions: {found_telemetry_errors}")
        if mode == "direct":
            direct_timing = _timing_dict(candidate_timed)
            require(direct_timing is not None and direct_timing["calls"] == 719,
                    f"direct wrapper call count mismatch: {direct_timing}")
        else:
            direct_timing = None

        result = {
            "mode": mode,
            "fixture_id": job["fixture_id"],
            "role": job["role"],
            "candidate_seat": seat,
            "seed": fixture["seed"],
            "candidate_sha256": sha(candidate),
            "rewards_by_player": rewards,
            "result": ("win" if rewards[seat] > rewards[1-seat]
                       else "loss" if rewards[seat] < rewards[1-seat] else "draw"),
            "candidate_reward": rewards[seat],
            "opponent_reward": rewards[1-seat],
            "statuses_by_player": statuses,
            "frames": len(env.steps),
            "native_log_entries": len(env.logs),
            "native_duration_record_count_by_player": [call_counts[0], call_counts[1]],
            "native_action_calls_by_player": [call_counts[0], call_counts[1]],
            "candidate_native_duration_records": candidate_durations,
            "candidate_native_max_duration_seconds": max_record,
            "candidate_native_max_duration_log_index": max_log_index,
            "native_act_timeout_seconds": timeout,
            "candidate_remaining_overage_start_seconds": overage_trace[0],
            "candidate_remaining_overage_min_seconds": min(overage_trace),
            "candidate_remaining_overage_end_seconds": overage_trace[-1],
            "candidate_remaining_overage_trace": overage_trace,
            "native_overage_spent_from_start_to_min_seconds": overage_trace[0] - min(overage_trace),
            "available_seconds_at_max_native_call": available_at_max,
            "native_status_errors": native_status_errors,
            "native_stderr_events": stderr_events,
            "telemetry": telemetry,
            "telemetry_sha256": json_sha(telemetry),
            "telemetry_errors": found_telemetry_errors,
            "direct_wrapper_timing": direct_timing,
            "all_719_action_frames_present": len(actions) == 719,
            "actions_sha256": json_sha(actions),
        }
        return result, actions
    finally:
        if kaggle_agent_module is not None and original_get_last_callable is not None:
            kaggle_agent_module.get_last_callable = original_get_last_callable
        if module is not None:
            sys.modules.pop(module.__name__, None)
        if opponent_timed is not None and opponent_timed.module_name:
            sys.modules.pop(opponent_timed.module_name, None)


def write_json_exclusive(path: Path, data: Any) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def append_jsonl(path: Path, data: Any) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(canonical_json(data) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def run_all(static: dict[str, Any]) -> dict[str, Any]:
    candidate = Path(static["candidate_path"])
    output = Path(static["output_path"])
    require(not output.exists(), f"refusing existing output path: {output}")
    runtime_file_bindings, runtime = runtime_bindings(candidate, static)
    expected_candidate_sha = static["candidate_sha256"]
    require(sha(candidate) == expected_candidate_sha,
            "candidate changed after static preflight")

    from diagnostics.local_target_20260928.run_lock import exclusive_run

    with exclusive_run(SHARED_LOCK):
        require(not output.exists(), f"refusing existing output path: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.mkdir()
        try:
            manifest = {
                "schema": "combined-agent-local-file-loader-v1",
                "operational_only": True,
                "research_promotion": False,
                "candidate_path": str(candidate),
                "candidate_sha256": expected_candidate_sha,
                "candidate_ast_final_callable": static["ast_final_callable"],
                "source_panel_path": static["source_panel_path"],
                "source_panel_sha256": static["source_panel_sha256"],
                "target_fixture": "live-114218866",
                "control_fixture": "live-114249897",
                "fixture_seats": 4,
                "native_game_runs_planned": 8,
                "modes": ["direct", "file"],
                "required_parity": ["all 719 actions for both players", "both rewards", "candidate telemetry"],
                "required_native_cleanliness": ["DONE/DONE", "720 frames", "719 duration logs per player",
                                                "no ERROR/INVALID/TIMEOUT", "no stderr", "nonnegative overage"],
                "output_files": list(OUTPUT_NAMES),
                "runtime": runtime,
                "jobs": static["jobs"],
                "bindings": runtime_file_bindings,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            manifest_path = output / "manifest.json"
            write_json_exclusive(manifest_path, manifest)
            manifest_sha = sha(manifest_path)
            runs_path = output / "runs.jsonl"
            traces_path = output / "action_traces.jsonl"
            outcomes_path = output / "outcomes.jsonl"
            # Create exclusively before starting any game, so no old evidence
            # can be appended to or overwritten.
            for path in (runs_path, traces_path, outcomes_path):
                with path.open("x", encoding="utf-8", newline="\n"):
                    pass

            all_runs: dict[tuple[str, int], dict[str, tuple[dict[str, Any], list[Any]]]] = {}
            for job in static["jobs"]:
                key = (job["fixture_id"], int(job["candidate_seat"]))
                all_runs[key] = {}
                for mode in ("direct", "file"):
                    for bound_path, bound_sha in runtime_file_bindings.items():
                        require(sha(Path(bound_path)) == bound_sha,
                                f"bound input changed before {mode} run: {bound_path}")
                    result, actions = run_one(job, mode, candidate,
                                              static["ast_final_callable"])
                    require(sha(candidate) == expected_candidate_sha,
                            "candidate source changed during loader check")
                    all_runs[key][mode] = (result, actions)
                    append_jsonl(runs_path, result)
                    append_jsonl(traces_path, {
                        "fixture_id": job["fixture_id"],
                        "role": job["role"],
                        "candidate_seat": job["candidate_seat"],
                        "mode": mode,
                        "candidate_sha256": expected_candidate_sha,
                        "actions": actions,
                        "actions_sha256": json_sha(actions),
                    })
                    print(json.dumps({"mode_complete": True, "fixture_id": job["fixture_id"],
                                      "role": job["role"], "candidate_seat": job["candidate_seat"],
                                      "frames": result["frames"],
                                      "duration_calls": result["native_duration_record_count_by_player"],
                                      "minimum_overage_seconds": result["candidate_remaining_overage_min_seconds"]}),
                          flush=True)

                direct, direct_actions = all_runs[key]["direct"]
                file_result, file_actions = all_runs[key]["file"]
                require(direct_actions == file_actions,
                        f"direct/file action mismatch for all 719 frames: {key}")
                require(direct["rewards_by_player"] == file_result["rewards_by_player"],
                        f"direct/file reward mismatch: {key}")
                require(direct["telemetry"] == file_result["telemetry"],
                        f"direct/file candidate telemetry mismatch: {key}")
                require(direct["statuses_by_player"] == file_result["statuses_by_player"]
                        and direct["frames"] == file_result["frames"] == 720,
                        f"direct/file completion mismatch: {key}")
                outcome = {
                    "fixture_id": key[0],
                    "role": job["role"],
                    "candidate_seat": key[1],
                    "seed": job["fixture"]["seed"],
                    "candidate_sha256": expected_candidate_sha,
                    "direct_result": direct["result"],
                    "file_result": file_result["result"],
                    "candidate_reward": direct["candidate_reward"],
                    "opponent_reward": direct["opponent_reward"],
                    "all_719_action_frames_both_players_equal": True,
                    "direct_actions_sha256": direct["actions_sha256"],
                    "file_actions_sha256": file_result["actions_sha256"],
                    "rewards_equal": True,
                    "telemetry_equal": True,
                    "telemetry_sha256": direct["telemetry_sha256"],
                    "native_done_done_720_both_modes": True,
                    "native_duration_records_719_per_player_both_modes": True,
                    "no_status_or_stderr_or_telemetry_errors_both_modes": True,
                    "direct_min_overage_seconds": direct["candidate_remaining_overage_min_seconds"],
                    "file_min_overage_seconds": file_result["candidate_remaining_overage_min_seconds"],
                }
                append_jsonl(outcomes_path, outcome)

            require(len(all_runs) == 4, f"completed fixture-seat count changed: {len(all_runs)}")
            for bound_path, bound_sha in runtime_file_bindings.items():
                require(sha(Path(bound_path)) == bound_sha,
                        f"bound input changed during loader check: {bound_path}")
            require(sha(candidate) == expected_candidate_sha,
                    "candidate source changed during loader check")
            receipt = {
                "schema": "combined-agent-local-file-loader-receipt-v1",
                "passed": True,
                "operational_only": True,
                "research_promotion": False,
                "candidate_sha256": expected_candidate_sha,
                "manifest_sha256": manifest_sha,
                "source_panel_sha256": static["source_panel_sha256"],
                "fixture_seats": 4,
                "native_game_runs": 8,
                "all_direct_file_actions_rewards_telemetry_equal": True,
                "all_runs_done_done_720": True,
                "all_runs_719_duration_logs_per_player": True,
                "all_runs_no_native_status_stderr_or_telemetry_errors": True,
                "all_runs_nonnegative_actual_native_overage": True,
                "completed_at_utc": datetime.now(timezone.utc).isoformat(),
                "outputs": {name: str(output / name) for name in OUTPUT_NAMES},
            }
            write_json_exclusive(output / "receipt.json", receipt)
            return receipt
        except BaseException as error:
            failure_path = output / "failure.json"
            if not failure_path.exists():
                write_json_exclusive(failure_path, {
                    "schema": "combined-agent-local-file-loader-failure-v1",
                    "candidate_sha256": expected_candidate_sha,
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "traceback": traceback.format_exc(),
                    "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                })
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, help="standalone candidate source path")
    parser.add_argument("--sha256", required=True, help="frozen candidate SHA-256")
    parser.add_argument("--output", required=True, help="new output directory; existing paths are refused")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--static", action="store_true", help="AST and input binding preflight only")
    modes.add_argument("--run", action="store_true", help="run the frozen eight-game direct/file check")
    args = parser.parse_args()
    static = verify_static(args.candidate, args.sha256, args.output)
    if args.static:
        print(json.dumps({
            "static_preflight_passed": True,
            "candidate_path": static["candidate_path"],
            "candidate_sha256": static["candidate_sha256"],
            "ast_final_callable": static["ast_final_callable"],
            "checker_sha256": static["bindings"][str(Path(__file__).resolve())],
            "source_panel_sha256": static["source_panel_sha256"],
            "fixture_seats": len(static["jobs"]),
            "native_game_runs_planned": 8,
            "native_game_runs_executed": 0,
            "output_exists": static["output_exists"],
            "operational_only": True,
        }, indent=2))
        return
    receipt = run_all(static)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
