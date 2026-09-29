"""Source-bound paired comparison runner; root launches it after freezing cases.

This file deliberately does not choose a candidate, fixtures, seeds, or opponents.
Each run requires an explicit SHA-256 for the frozen comparison manifest.
"""
from __future__ import annotations

from contextlib import ExitStack
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from diagnostics.local_target_20260928.run_lock import exclusive_run

BASELINE_SHA256 = "257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55"
REFERENCE_RECEIPT_SHA256 = "4086a1ebd23431efedcbd178a7e5367cc1e84d8999b1843a4e62d891aa5f2997"
SCHEMA = "combined-agent-comparison-v1"
PHASES = {"pilot", "saved_panel", "reactive"}
POINTS = {"win": 1.0, "draw": 0.5, "loss": 0.0}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def bound_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve(strict=True)


def result_points(result: str) -> float:
    require(result in POINTS, f"unknown result label: {result!r}")
    return POINTS[result]


FIXTURE_BINDING_FIELDS = (
    "fixture_id", "seed", "source_replay_path", "source_replay_sha256",
    "source_action_tape_path", "source_opponent_action_sha256",
)


def fixture_binding(fixture: dict) -> tuple:
    return tuple(fixture.get(field) for field in FIXTURE_BINDING_FIELDS)


def source_panel_index(panel: dict) -> dict:
    index = {}
    for collection, default_group in (("games", None), ("controls", "pet_public_win_control")):
        for source_row in panel.get(collection, []):
            fixture = source_row["fixture"]
            seat = int(source_row.get("candidate_seat", source_row.get("seat")))
            key = (fixture["fixture_id"], seat)
            group = source_row.get("panel", default_group)
            require(group is not None, f"source panel row has no group: {key}")
            require(key not in index, f"duplicate source panel identity: {key}")
            index[key] = {"group": group, "fixture": fixture, "row": source_row}
    return index


def verify_source_panel(manifest: dict) -> tuple[dict, Path, str]:
    bound = manifest.get("source_panel")
    require(isinstance(bound, dict), "fixed-replay manifest must bind source_panel path and SHA-256")
    panel_path = bound_path(bound["path"])
    panel_sha = bound["sha256"].lower()
    require(sha(panel_path) == panel_sha, "bound source panel hash mismatch")
    panel = json.loads(panel_path.read_text(encoding="utf-8-sig"))
    index = source_panel_index(panel)
    for case in manifest["cases"]:
        fixture = case["fixture"]
        key = (fixture["fixture_id"], int(case["candidate_seat"]))
        require(key in index, f"case is absent from bound source panel: {key}")
        source = index[key]
        require(fixture_binding(fixture) == fixture_binding(source["fixture"]),
                f"fixture/replay/tape binding differs from source panel: {key}")
        if manifest["phase"] == "saved_panel":
            require(case["group"] == source["group"],
                    f"case group differs from bound source panel: {key}")
    return panel, panel_path, panel_sha


def apply_baseline_reference(manifest: dict, panel_index: dict) -> dict | None:
    reference = manifest.get("baseline_reference")
    if reference is None:
        return None
    require(manifest["phase"] == "saved_panel",
            "baseline_reference is supported only for saved_panel")
    receipt_path = bound_path(reference["receipt_path"])
    receipt_sha = reference["receipt_sha256"].lower()
    require(receipt_sha == REFERENCE_RECEIPT_SHA256,
            "baseline reference must be the frozen exact-257 preservation receipt")
    require(sha(receipt_path) == receipt_sha, "baseline preservation receipt hash mismatch")
    source_panel = manifest["_source_panel_path"]
    panel_path = bound_path(reference["panel_path"])
    panel_sha = reference["panel_sha256"].lower()
    require(panel_path == source_panel and panel_sha == manifest["_source_panel_sha256"],
            "baseline reference panel must equal the manifest's bound source panel")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    require(receipt.get("candidate_sha256") == BASELINE_SHA256
            and receipt.get("complete") is True and receipt.get("passed") is True
            and receipt.get("fixed_tape_only") is True
            and receipt.get("preservation_only") is True,
            "baseline reference is not a completed passing fixed-tape exact-257 receipt")
    receipt_rows = {}
    games = receipt.get("games", [])
    require(len(games) == 102, "baseline reference must contain exactly 102 outcomes")
    for saved in games:
        key = (saved["fixture_id"], int(saved["candidate_seat"]))
        require(key not in receipt_rows, f"duplicate baseline reference row: {key}")
        require(saved.get("passed") is True
                and all(saved.get("checks", {}).values()),
                f"baseline reference row/check failed: {key}")
        receipt_rows[key] = saved

    for case in manifest["cases"]:
        fixture = case["fixture"]
        key = (fixture["fixture_id"], int(case["candidate_seat"]))
        require(key in receipt_rows, f"case is absent from exact-257 baseline receipt: {key}")
        saved = receipt_rows[key]
        actual = saved["actual"]
        panel_source = panel_index[key]
        expected_receipt_group = ("public_win_control" if panel_source["group"] == "pet_public_win_control"
                                  else panel_source["group"])
        require(saved.get("panel") == expected_receipt_group,
                f"receipt group differs from reference source panel: {key}")
        require(fixture_binding(fixture) == fixture_binding(panel_source["fixture"]),
                f"case source replay/tape differs from reference panel before baseline use: {key}")
        require(actual.get("fixture_id") == key[0]
                and int(actual.get("candidate_seat", -1)) == key[1]
                and actual.get("candidate_sha256") == BASELINE_SHA256,
                f"baseline actual identity/hash mismatch: {key}")
        checks = check_clean_result(actual, f"baseline-reference {key}")
        require(checks["passed"], f"baseline reference has a dirty native result: {key}: {checks}")
        case["_baseline_reference_actual"] = actual
    reference["receipt_path"] = str(receipt_path)
    reference["panel_path"] = str(panel_path)
    reference["receipt_sha256"] = receipt_sha
    reference["panel_sha256"] = panel_sha
    reference["_receipt_rows"] = len(games)
    return receipt


def check_clean_result(raw: dict, label: str) -> dict:
    telemetry_errors = {}
    for telemetry_name in ("candidate_telemetry", "opponent_telemetry"):
        telemetry = raw.get(telemetry_name) or {}
        found = {
            str(key): value for key, value in telemetry.items()
            if ("error" in str(key).lower() or "collision" in str(key).lower())
            and value not in (0, False, None, "")
        }
        if found:
            telemetry_errors[telemetry_name] = found
    checks = {
        "done_done": raw.get("candidate_status") == "DONE" and raw.get("opponent_status") == "DONE",
        "frames_720": raw.get("frames") == 720,
        "candidate_telemetry_present": isinstance(raw.get("candidate_telemetry"), dict),
        "candidate_policy_errors_empty": not raw.get("candidate_errors"),
        "opponent_policy_errors_empty": not raw.get("opponent_errors"),
        "telemetry_errors_empty": not telemetry_errors,
        "native_status_errors_empty": not raw.get("native_status_errors", []),
        "native_stderr_empty": not raw.get("native_stderr_events", []),
        "native_overage_nonnegative": (
            raw.get("minimum_remaining_overage_seconds") is None
            or raw.get("minimum_remaining_overage_seconds") >= 0
        ),
    }
    checks["passed"] = all(checks.values())
    if not checks["passed"]:
        checks["telemetry_errors"] = telemetry_errors
    return checks


def execution_sources(phase: str) -> dict[str, str]:
    sources = {
        "runner": Path(__file__).resolve(),
        "run_lock": ROOT / "diagnostics/local_target_20260928/run_lock.py",
    }
    if phase == "reactive":
        sources.update({
            "qualify": ROOT / "diagnostics/combined_agent_257f_20260929/qualify_native_diagnostics.py",
            "paired_benchmark": ROOT / "paired_benchmark.py",
        })
    else:
        sources.update({
            "fast_game_cached": ROOT / "diagnostics/stream_replay_io_20260928/fast_game_cached.py",
            "cached_input": ROOT / "diagnostics/stream_replay_io_20260928/cached_input.py",
            "native_core": ROOT / "diagnostics/physical_route_rollout_20260928/native_core.py",
            "native_check": ROOT / "diagnostics/physical_route_rollout_20260928/check.py",
        })
    return {name: sha(path) for name, path in sources.items()}


def arm_result(raw: dict) -> dict:
    return {
        "result": raw["result"],
        "candidate_reward": float(raw["candidate_reward"]),
        "opponent_reward": float(raw["opponent_reward"]),
        "margin": float(raw["margin"]),
        "candidate_status": raw.get("candidate_status"),
        "opponent_status": raw.get("opponent_status"),
        "frames": raw.get("frames"),
        "candidate_errors": raw.get("candidate_errors", {}),
        "opponent_errors": raw.get("opponent_errors", {}),
        "candidate_telemetry": raw.get("candidate_telemetry", {}),
        "opponent_telemetry": raw.get("opponent_telemetry"),
        "runtime": {
            "wall_seconds": raw.get("wall_seconds"),
            "candidate_call_seconds": raw.get("candidate_call_seconds"),
            "max_candidate_call_seconds": raw.get("max_candidate_call_seconds"),
            "candidate_timing": raw.get("candidate_timing"),
            "opponent_timing": raw.get("opponent_timing"),
            "minimum_remaining_overage_seconds": raw.get("minimum_remaining_overage_seconds"),
        },
        # Keep all harness-native fields, including telemetry/capture/source fields.
        "raw": raw,
    }


def validate_manifest(path: Path, expected_sha: str) -> dict:
    raw = path.read_bytes()
    require(sha_bytes(raw) == expected_sha.lower(), "manifest SHA-256 mismatch")
    manifest = json.loads(raw.decode("utf-8-sig"))
    require(manifest.get("schema") == SCHEMA, "wrong comparison manifest schema")
    phase = manifest.get("phase")
    require(phase in PHASES, f"unsupported phase: {phase!r}")
    baseline = manifest["baseline"]
    candidate = manifest["candidate"]
    for label, arm in (("baseline", baseline), ("candidate", candidate)):
        require(isinstance(arm.get("label"), str) and arm["label"],
                f"{label} needs a descriptive label")
        arm_path = bound_path(arm["path"])
        arm_digest = arm["sha256"].lower()
        require(sha(arm_path) == arm_digest, f"{label} source hash mismatch")
        arm["path"] = str(arm_path)
        arm["sha256"] = arm_digest
    require(baseline["sha256"] == BASELINE_SHA256,
            "baseline must be the exact uploaded 257f941d agent")
    require(candidate["sha256"] != baseline["sha256"],
            "candidate must differ from uploaded 257f941d")
    require(Path(candidate["path"]) != Path(baseline["path"]),
            "candidate and baseline paths must differ")
    cases = manifest.get("cases")
    require(isinstance(cases, list) and cases, "manifest has no cases")
    ids = [case.get("case_id") for case in cases]
    require(all(isinstance(case_id, str) and case_id for case_id in ids),
            "every case needs a nonempty case_id")
    require(len(ids) == len(set(ids)), "duplicate case_id")
    require(all(isinstance(case.get("group"), str) and case["group"] for case in cases),
            "every case needs a group label")

    if phase in {"pilot", "saved_panel"}:
        keys = []
        groups_by_fixture = {}
        counts = {}
        for case in cases:
            group = case.get("group")
            seat = int(case["candidate_seat"])
            fixture = case["fixture"]
            require(seat in (0, 1), f"invalid seat in {case['case_id']}")
            require("fixture_id" in fixture and "seed" in fixture,
                    f"fixture identity/seed missing in {case['case_id']}")
            for field in ("source_replay_path", "source_replay_sha256",
                          "source_action_tape_path", "source_opponent_action_sha256"):
                require(field in fixture, f"fixture lacks {field}: {case['case_id']}")
            key = (fixture["fixture_id"], seat)
            keys.append(key)
            counts[group] = counts.get(group, 0) + 1
            prior = groups_by_fixture.setdefault(fixture["fixture_id"], group)
            require(prior == group, f"fixture occurs in multiple groups: {fixture['fixture_id']}")
            for field in ("source_replay_path", "source_action_tape_path"):
                require(Path(fixture[field]).is_absolute(),
                        f"cached fixture paths must retain their exact absolute spelling: {case['case_id']}")
                bound_path(fixture[field])
        require(len(keys) == len(set(keys)), "duplicate fixture-seat case")
        seats_by_fixture = {}
        for fixture_id, seat in keys:
            seats_by_fixture.setdefault(fixture_id, set()).add(seat)
        require(all(seats == {0, 1} for seats in seats_by_fixture.values()),
                "each fixed-replay fixture must include both candidate seats")
        if phase == "pilot":
            require(counts.get("target", 0) and counts.get("control", 0),
                    "pilot must include target and control cases")
            require(set(groups_by_fixture.values()) == {"target", "control"},
                    "pilot groups must be target/control only")
        else:
            require(counts == {"loss30": 60, "top20": 40, "pet_public_win_control": 2},
                    f"saved panel must be exactly 60 loss30 + 40 top20 + 2 Pet controls; got {counts}")
    else:
        require(manifest.get("fresh_native") is True
                and manifest.get("original_shop") is True,
                "reactive phase must declare fresh native original-shop games")
        require(manifest.get("baseline_reference") is None,
                "baseline_reference is supported only for saved_panel")
        seen = set()
        opponent_by_id = {}
        seat_sets = {}
        for case in cases:
            seat = int(case["candidate_seat"])
            require(seat in (0, 1), f"invalid seat in {case['case_id']}")
            require(isinstance(case.get("seed"), int), f"missing explicit seed: {case['case_id']}")
            opponent = case["opponent"]
            opponent_id = opponent["id"]
            require(isinstance(opponent_id, str) and opponent_id,
                    f"opponent needs a stable ID: {case['case_id']}")
            opponent_path = opponent["path"]
            require(not str(opponent_path).startswith("rawroute:"),
                    f"reactive comparison cannot use a fixed replay: {case['case_id']}")
            op_path = bound_path(opponent_path)
            op_digest = opponent["sha256"].lower()
            require(sha(op_path) == op_digest, f"opponent hash mismatch: {case['case_id']}")
            opponent["path"] = str(op_path)
            opponent["sha256"] = op_digest
            identity = (opponent_id, int(case["seed"]))
            key = (*identity, seat)
            require(key not in seen, f"duplicate opponent/seed/seat: {key}")
            seen.add(key)
            prior = opponent_by_id.setdefault(opponent_id, (str(op_path), op_digest))
            require(prior == (str(op_path), op_digest), f"opponent binding changes for {opponent_id}")
            seat_sets.setdefault(identity, set()).add(seat)
        require(len(opponent_by_id) >= 2, "reactive phase needs at least two distinct opponents")
        require(len(set(opponent_by_id.values())) >= 2,
                "reactive opponent IDs must bind to at least two distinct source files")
        require(all(seats == {0, 1} for seats in seat_sets.values()),
                "each reactive opponent/seed must be tested in both candidate seats")

    if phase in {"pilot", "saved_panel"}:
        source_panel, source_panel_path, source_panel_sha = verify_source_panel(manifest)
        manifest["_source_panel_path"] = source_panel_path
        manifest["_source_panel_sha256"] = source_panel_sha
        panel_index = source_panel_index(source_panel)
        baseline_reference = apply_baseline_reference(manifest, panel_index)
        manifest["_baseline_reference_rows"] = len(baseline_reference["games"]) if baseline_reference else 0

    manifest["_manifest_sha256"] = expected_sha.lower()
    return manifest


def run_fixed(case: dict, arm: dict) -> dict:
    from diagnostics.stream_replay_io_20260928.fast_game_cached import play
    return play(case["fixture"], arm["path"], arm["sha256"],
                int(case["candidate_seat"]))


def run_reactive(case: dict, arm: dict) -> dict:
    from diagnostics.combined_agent_257f_20260929.qualify_native_diagnostics import play
    opponent = case["opponent"]
    job = {
        "version": arm["label"],
        "rival": opponent["id"],
        "seed": int(case["seed"]),
        "candidate_seat": int(case["candidate_seat"]),
        "path": arm["path"],
        "candidate_sha256": arm["sha256"],
        "opponent": opponent["path"],
        "opponent_sha256": opponent["sha256"],
    }
    return play(job)


def paired_case(case: dict, manifest: dict) -> dict:
    phase = manifest["phase"]
    baseline = manifest["baseline"]
    candidate = manifest["candidate"]
    if phase == "reactive":
        before = run_reactive(case, baseline)
        after = run_reactive(case, candidate)
    else:
        before = case.get("_baseline_reference_actual")
        baseline_source = "preservation_receipt" if before is not None else "native_rerun"
        if before is None:
            before = run_fixed(case, baseline)
        after = run_fixed(case, candidate)
    if phase == "reactive":
        baseline_source = "native_rerun"
    old, new = arm_result(before), arm_result(after)
    old_checks = check_clean_result(before, "baseline")
    new_checks = check_clean_result(after, "candidate")
    fixture = case.get("fixture", {})
    source_hashes = {
        "baseline_agent_sha256": baseline["sha256"],
        "candidate_agent_sha256": candidate["sha256"],
    }
    source_paths = {
        "baseline_agent": baseline["path"],
        "candidate_agent": candidate["path"],
    }
    if phase == "reactive":
        source_hashes["opponent_agent_sha256"] = case["opponent"]["sha256"]
        source_paths["opponent_agent"] = case["opponent"]["path"]
    else:
        source_hashes.update({
            "source_panel_sha256": manifest["_source_panel_sha256"],
            "source_replay_sha256": fixture["source_replay_sha256"],
            "source_opponent_action_sha256": fixture["source_opponent_action_sha256"],
        })
        source_paths.update({
            "source_panel": str(manifest["_source_panel_path"]),
            "source_replay": fixture["source_replay_path"],
            "source_action_tape": fixture["source_action_tape_path"],
        })
    reference = manifest.get("baseline_reference")
    if baseline_source == "preservation_receipt" and reference:
        source_hashes["baseline_reference_receipt_sha256"] = reference["receipt_sha256"]
        source_hashes["baseline_reference_panel_sha256"] = reference["panel_sha256"]
        source_paths["baseline_reference_receipt"] = reference["receipt_path"]
        source_paths["baseline_reference_panel"] = reference["panel_path"]
    old["source_hashes"] = dict(source_hashes)
    new["source_hashes"] = dict(source_hashes)
    old["source_paths"] = dict(source_paths)
    new["source_paths"] = dict(source_paths)
    return {
        "case_id": case["case_id"],
        "group": case["group"],
        "fixture_id": (fixture.get("fixture_id")
                       if phase != "reactive" else case.get("fixture_id", case["case_id"])),
        "seed": (fixture.get("seed") if phase != "reactive"
                 else int(case["seed"])),
        "candidate_seat": int(case["candidate_seat"]),
        "opponent_id": case.get("opponent", {}).get("id"),
        "baseline_source": baseline_source,
        "source_hashes": source_hashes,
        "source_paths": source_paths,
        "baseline": old,
        "candidate": new,
        "execution_checks": {"baseline": old_checks, "candidate": new_checks,
                              "passed": old_checks["passed"] and new_checks["passed"]},
        "margin_delta": new["margin"] - old["margin"],
        "point_delta": result_points(new["result"]) - result_points(old["result"]),
        "same_outcome": old["result"] == new["result"],
    }


def compact_runtime(result: dict) -> str:
    runtime = result.get("runtime", {})
    labels = []
    for label, timing_key, seconds_key in (
        ("candidate", "candidate_timing", "max_candidate_call_seconds"),
        ("opponent", "opponent_timing", "max_opponent_call_seconds"),
    ):
        timing = runtime.get(timing_key) or {}
        max_ms = timing.get("max_ms")
        if max_ms is None:
            seconds = runtime.get(seconds_key)
            max_ms = round(float(seconds) * 1000, 2) if seconds is not None else None
        if max_ms is not None:
            labels.append(f"{label} {max_ms} ms")
    return "; ".join(labels)


def errors_text(result: dict) -> str:
    errors = {
        "candidate": result.get("candidate_errors") or {},
        "opponent": result.get("opponent_errors") or {},
    }
    errors = {key: value for key, value in errors.items() if value}
    return "none" if not errors else json.dumps(errors, ensure_ascii=True, sort_keys=True)


def markdown_table(manifest: dict, rows: list[dict], status: str, failure: str = "") -> str:
    kind = ("fresh native original-shop games against agents"
            if manifest["phase"] == "reactive"
            else "fixed saved-replay action tapes; preservation evidence only")
    lines = [
        f"# {manifest['phase']} paired comparison",
        "",
        f"Status: **{status}**. Candidate SHA-256: `{manifest['candidate']['sha256']}`. "
        f"Baseline: `{manifest['baseline']['sha256']}`.",
        f"Evaluation: {kind}.",
    ]
    if failure:
        lines += ["", f"Run stopped: `{failure.replace('|', '\\|')}`."]
    lines += [
        "",
        "| Case | Group / opponent | Baseline source | Seed / seat | Baseline WDL | Baseline own / rival | Baseline margin | Candidate WDL | Candidate own / rival | Candidate margin | Margin Δ | Native status / frames: baseline → candidate | Errors: baseline / candidate | Max calls: baseline / candidate |",
        "|---|---|---|---:|:---:|---:|---:|:---:|---:|---:|---:|---|---|---|",
    ]
    for row in rows:
        old, new = row["baseline"], row["candidate"]
        opp = row["opponent_id"] or "saved tape"
        lines.append(
            f"| {row['case_id']} | {row['group']} / {opp} | {row['baseline_source']} | "
            f"{row['seed']} / {row['candidate_seat']} | "
            f"{old['result']} | {old['candidate_reward']:g} / {old['opponent_reward']:g} | {old['margin']:g} | "
            f"{new['result']} | {new['candidate_reward']:g} / {new['opponent_reward']:g} | {new['margin']:g} | "
            f"{row['margin_delta']:+g} | {old['candidate_status']}/{old['opponent_status']}/{old['frames']} → "
            f"{new['candidate_status']}/{new['opponent_status']}/{new['frames']} | "
            f"{errors_text(old).replace('|', '\\|')} / {errors_text(new).replace('|', '\\|')} | "
            f"{compact_runtime(old)} / {compact_runtime(new)} |"
        )
    if rows:
        old_points = sum(result_points(row["baseline"]["result"]) for row in rows)
        new_points = sum(result_points(row["candidate"]["result"]) for row in rows)
        old_wdl = {label: sum(row["baseline"]["result"] == label for row in rows)
                   for label in ("win", "draw", "loss")}
        new_wdl = {label: sum(row["candidate"]["result"] == label for row in rows)
                   for label in ("win", "draw", "loss")}
        lines += [
            "",
            f"Rows: {len(rows)}. Baseline W-D-L: {old_wdl['win']}-{old_wdl['draw']}-{old_wdl['loss']} "
            f"({old_points:g} points); candidate W-D-L: {new_wdl['win']}-{new_wdl['draw']}-{new_wdl['loss']} "
            f"({new_points:g} points); "
            f"mean paired margin Δ: {sum(row['margin_delta'] for row in rows)/len(rows):+.2f}.",
        ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve(strict=True)
    require(manifest_path.is_relative_to(ROOT), "manifest must be inside the workspace")
    digest = args.manifest_sha256.lower()
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise SystemExit("manifest SHA-256 must be 64 lowercase/uppercase hex characters")
    manifest = validate_manifest(manifest_path, digest)
    phase = manifest["phase"]
    output_dir = manifest_path.parent
    prefix = manifest_path.stem
    outputs = {
        "jsonl": output_dir / f"{prefix}_results.jsonl",
        "receipt": output_dir / f"{prefix}_receipt.json",
        "markdown": output_dir / f"{prefix}_results.md",
    }
    require(not any(path.exists() for path in outputs.values()),
            "phase output exists; inspect it rather than overwriting/rerunning")

    rows = []
    failure = ""
    status = "complete"
    frozen_execution_sources = execution_sources(phase)
    baseline_reference = manifest.get("baseline_reference")
    with ExitStack() as locks:
        locks.enter_context(exclusive_run(ROOT / "diagnostics/.shared_game_run.lock"))
        locks.enter_context(exclusive_run(output_dir / f"{prefix}.lock"))
        with outputs["jsonl"].open("x", encoding="utf-8", newline="\n") as stream:
            try:
                for index, case in enumerate(manifest["cases"], 1):
                    require(sha(Path(manifest["baseline"]["path"])) == manifest["baseline"]["sha256"],
                            "baseline changed during run")
                    require(sha(Path(manifest["candidate"]["path"])) == manifest["candidate"]["sha256"],
                            "candidate changed during run")
                    row = paired_case(case, manifest)
                    rows.append(row)
                    stream.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")
                    stream.flush()
                    print(json.dumps({"completed": index, "total": len(manifest["cases"]),
                                      "case_id": row["case_id"],
                                      "baseline": row["baseline"]["result"],
                                      "candidate": row["candidate"]["result"],
                                      "margin_delta": row["margin_delta"]}, ensure_ascii=True), flush=True)
                    require(row["execution_checks"]["passed"],
                            f"native completion/error gate failed for {row['case_id']}; row preserved")
                require(sha(Path(manifest["baseline"]["path"])) == manifest["baseline"]["sha256"],
                        "baseline changed by run completion")
                require(sha(Path(manifest["candidate"]["path"])) == manifest["candidate"]["sha256"],
                        "candidate changed by run completion")
                require(sha(manifest_path) == digest, "frozen manifest changed during run")
                require(execution_sources(phase) == frozen_execution_sources,
                        "runner/helper source changed during run")
                if baseline_reference:
                    require(sha(Path(baseline_reference["receipt_path"])) == baseline_reference["receipt_sha256"]
                            and sha(Path(baseline_reference["panel_path"])) == baseline_reference["panel_sha256"],
                            "baseline reference input changed during run")
            except BaseException as exc:
                status = "incomplete"
                failure = f"{type(exc).__name__}: {exc}"
                rows_error = traceback.format_exc()
            else:
                rows_error = ""

    outputs["markdown"].write_text(markdown_table(manifest, rows, status, failure), encoding="utf-8", newline="\n")
    receipt = {
        "schema": "combined-agent-comparison-results-v1",
        "phase": phase,
        "status": status,
        "manifest_sha256": manifest["_manifest_sha256"],
        "manifest_path": str(manifest_path),
        "baseline": manifest["baseline"],
        "candidate": manifest["candidate"],
        "source_panel": ({"path": str(manifest["_source_panel_path"]),
                          "sha256": manifest["_source_panel_sha256"]}
                         if phase in {"pilot", "saved_panel"} else None),
        "baseline_reference": ({key: value for key, value in baseline_reference.items()
                                if not key.startswith("_")} if baseline_reference else None),
        "baseline_reference_rows_available": manifest.get("_baseline_reference_rows", 0),
        "baseline_rows_reused": sum(row["baseline_source"] == "preservation_receipt" for row in rows),
        "execution_source_sha256": frozen_execution_sources,
        "planned_cases": len(manifest["cases"]),
        "completed_cases": len(rows),
        "runner_sha256": sha(Path(__file__).resolve()),
        "rows_sha256": sha(outputs["jsonl"]),
        "markdown_sha256": sha(outputs["markdown"]),
        "failure": failure,
        "traceback": rows_error,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "diagnostic_only": True,
    }
    with outputs["receipt"].open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
    print(json.dumps(receipt, indent=2, ensure_ascii=True), flush=True)
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
