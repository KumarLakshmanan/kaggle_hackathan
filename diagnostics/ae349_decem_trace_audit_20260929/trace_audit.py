"""Source-bound, both-seat trace rerun for the exact ae349 DECEM fixture."""
from __future__ import annotations

from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from diagnostics.local_target_20260928.run_lock import exclusive_run  # noqa: E402
from diagnostics.stream_replay_io_20260928.fast_game_cached import play  # noqa: E402

CANDIDATE = ROOT / "main_candidate_improved_20260929.py"
CANDIDATE_SHA = "ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb"
PANEL_DIR = ROOT / "diagnostics/combined_agent_257f_20260929/saved_panel"
MANIFEST = PANEL_DIR / "comparison_manifest.json"
MANIFEST_SHA = "b5f7be800528fb8d070caa9fbaf3493c3b934c3176a6416590d2d6a2dd3ab3fe"
REFERENCE_RESULTS = PANEL_DIR / "comparison_manifest_results.jsonl"
REFERENCE_RESULTS_SHA = "ebe9c97327a0086766f67c88213e2fe086ebfa8f89d8ba84db8f5ba918091562"
REFERENCE_RECEIPT = PANEL_DIR / "comparison_manifest_receipt.json"
REFERENCE_RECEIPT_SHA = "218297125b45a782f903b2a7aaa178597b708a53f0ffac4f196b404f7b95ce2d"
LOCK = ROOT / "diagnostics/.shared_game_run.lock"
FIXTURE_ID = "top20-01-DECEM-114267880"
EXPECTED_ENGINE = "1.32.7"

BOUND_HELPERS = {
    "fast_game_cached.py": "a57d12659af613512a61ac02aaa43d4c5ae4f4d8f2c5c02d3ed4ac6eafa2a38e",
    "cached_input.py": "e2aaefda623775c9c7d56304271c827ecd6e56cc109e5c6d8b35aeb458268aa1",
    "native_core.py": "5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795",
    "check.py": "f51b49dd2c627337136365603e4d0923c9f3e77f28bc8c77d08f608cba48e4a6",
    "run_lock.py": "6ae76386c4bfda83a5efff6c0772ad22a4480155126ac9f0ed5616ec68c0d219",
}
HELPERS = {
    "fast_game_cached.py": ROOT / "diagnostics/stream_replay_io_20260928/fast_game_cached.py",
    "cached_input.py": ROOT / "diagnostics/stream_replay_io_20260928/cached_input.py",
    "native_core.py": ROOT / "diagnostics/physical_route_rollout_20260928/native_core.py",
    "check.py": ROOT / "diagnostics/physical_route_rollout_20260928/check.py",
    "run_lock.py": ROOT / "diagnostics/local_target_20260928/run_lock.py",
}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def reference_rows() -> tuple[dict, dict]:
    require(sha(CANDIDATE) == CANDIDATE_SHA, "candidate hash changed")
    require(sha(MANIFEST) == MANIFEST_SHA, "saved-panel manifest hash changed")
    require(sha(REFERENCE_RESULTS) == REFERENCE_RESULTS_SHA, "saved result rows changed")
    require(sha(REFERENCE_RECEIPT) == REFERENCE_RECEIPT_SHA, "saved receipt hash changed")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    receipt = json.loads(REFERENCE_RECEIPT.read_text(encoding="utf-8"))
    require(manifest["candidate"]["sha256"] == CANDIDATE_SHA,
            "saved manifest does not bind exact ae349")
    require(receipt.get("status") == "complete"
            and receipt.get("completed_cases") == 102
            and receipt.get("rows_sha256") == REFERENCE_RESULTS_SHA,
            "saved reference receipt is not the complete 102-row result set")
    rows = {}
    for line in REFERENCE_RESULTS.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("fixture_id") == FIXTURE_ID:
            seat = int(row["candidate_seat"])
            require(seat not in rows, f"duplicate reference seat {seat}")
            require(row["candidate"]["source_hashes"]["candidate_agent_sha256"] == CANDIDATE_SHA,
                    f"reference row is not exact ae349 seat {seat}")
            require(row["execution_checks"]["candidate"]["passed"],
                    f"reference row is dirty in seat {seat}")
            rows[seat] = row
    require(set(rows) == {0, 1}, "missing both-seat exact-ae349 reference rows")
    cases = [case for case in manifest["cases"]
             if case["fixture"]["fixture_id"] == FIXTURE_ID]
    require(len(cases) == 2 and {int(case["candidate_seat"]) for case in cases} == {0, 1},
            "frozen manifest is missing the both-seat DECEM fixture")
    fixtures = {int(case["candidate_seat"]): case["fixture"] for case in cases}
    for fixture in fixtures.values():
        replay_raw = gzip.decompress(Path(fixture["source_replay_path"]).read_bytes())
        require(hashlib.sha256(replay_raw).hexdigest() == fixture["source_replay_sha256"],
                "uncompressed replay input changed")
        tape = json.loads(gzip.decompress(
            Path(fixture["source_action_tape_path"]).read_bytes()))["actions"]
        tape_digest = hashlib.sha256(json.dumps(
            tape, sort_keys=False, separators=(",", ":")).encode("utf-8")).hexdigest()
        require(len(tape) == 719
                and tape_digest == fixture["source_opponent_action_sha256"],
                "opponent action tape changed")
    return rows, fixtures


def main() -> None:
    from kaggle_environments import __version__ as engine_version

    require(engine_version == EXPECTED_ENGINE, f"engine version changed: {engine_version}")
    before = {"candidate": sha(CANDIDATE), **{name: sha(path) for name, path in HELPERS.items()}}
    require(before["candidate"] == CANDIDATE_SHA, "candidate hash changed before run")
    require({name: before[name] for name in BOUND_HELPERS} == BOUND_HELPERS,
            "native helper hash changed")
    references, fixtures = reference_rows()
    outputs = []
    progress = HERE / "trace_progress.jsonl"
    receipt_path = HERE / "trace_receipt.json"
    require(not progress.exists() and not receipt_path.exists(),
            "trace outputs already exist; inspect them rather than overwriting")

    with exclusive_run(LOCK):
        with progress.open("x", encoding="utf-8", newline="\n") as log:
            for seat in (0, 1):
                trace_path = HERE / f"ae349_decem_seat{seat}.jsonl.gz"
                require(not trace_path.exists(), f"trace already exists: {trace_path.name}")
                result = play(fixtures[seat], str(CANDIDATE), CANDIDATE_SHA, seat,
                              trace_path=str(trace_path))
                reference = references[seat]["candidate"]["raw"]
                fields = ("result", "candidate_reward", "opponent_reward", "margin",
                          "candidate_status", "opponent_status", "frames",
                          "candidate_errors", "candidate_telemetry")
                mismatches = {field: {"reference": reference.get(field),
                                      "trace_run": result.get(field)}
                              for field in fields if reference.get(field) != result.get(field)}
                row = {
                    "fixture_id": FIXTURE_ID,
                    "candidate_seat": seat,
                    "candidate_sha256": CANDIDATE_SHA,
                    "reference_result": references[seat]["candidate"]["result"],
                    "reference_margin": references[seat]["candidate"]["margin"],
                    "actual_result": result["result"],
                    "actual_margin": result["margin"],
                    "max_candidate_call_seconds": result["max_candidate_call_seconds"],
                    "trace_path": str(trace_path.resolve()),
                    "trace_sha256": sha(trace_path),
                    "trace_bytes": trace_path.stat().st_size,
                    "mismatches": mismatches,
                    "passed": not mismatches and result["frames"] == 720
                              and result["candidate_status"] == result["opponent_status"] == "DONE"
                              and not result["candidate_errors"],
                    "candidate_telemetry": result["candidate_telemetry"],
                }
                outputs.append(row)
                log.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")
                log.flush()
                print(json.dumps(row, ensure_ascii=True), flush=True)

    after = {"candidate": sha(CANDIDATE), **{name: sha(path) for name, path in HELPERS.items()}}
    require(after == before, "candidate or helper source changed during trace run")
    receipt = {
        "schema": "ae349-decem-trace-audit-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "complete": len(outputs) == 2,
        "passed": len(outputs) == 2 and all(row["passed"] for row in outputs),
        "diagnostic_only_fixed_tape": True,
        "engine_version": engine_version,
        "plan_sha256": sha(HERE / "PLAN.md"),
        "runner_sha256": sha(Path(__file__)),
        "candidate_sha256": CANDIDATE_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "reference_results_sha256": REFERENCE_RESULTS_SHA,
        "reference_receipt_sha256": REFERENCE_RECEIPT_SHA,
        "helper_sha256": after,
        "games": outputs,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in receipt.items() if k != "games"}, indent=2), flush=True)
    require(receipt["passed"], "trace parity or clean-completion gate failed")


if __name__ == "__main__":
    main()
