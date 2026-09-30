"""Freeze loader bindings only after the guarded preservation receipt passes.

This builder is static: it validates existing receipts, hashes inputs, compiles
the candidate/checker and runs verify_bindings(); it never runs a game.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GUARD = ROOT / "diagnostics/pet_source_guard_20260929"
BASE = ROOT / "diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929"
OLD_UPLOAD = ROOT / "diagnostics/upload_pet_market_20260929_ebfbe6e9"
OLD_PACKAGE_MANIFEST = OLD_UPLOAD / "package_manifest.json"
PRESERVATION_MANIFEST = GUARD / "preservation_manifest.json"
PRESERVATION_RECEIPT = GUARD / "preservation_receipt.json"
PRESERVATION_OUTCOMES = GUARD / "preservation_outcomes.jsonl"
PRESERVATION_RUNNER = GUARD / "verify_preservation.py"
SOURCE_PANEL = BASE / "panel.json"
SOURCE_CANDIDATE = GUARD / "candidate.py"
HISTORICAL_EBF_RECEIPT = BASE / "outcome_receipt.json"
RESEARCH_RECEIPT = ROOT / "diagnostics/a44_ghost_kwa_piice_petmarket114260_reactive_20260929/outcome_receipt.json"
ROOT_MAIN = ROOT / "main.py"
ROOT_BACKUP = ROOT / "main_candidate_pet_source_guard_20260929_257f941d.py"
MANIFEST_PATH = HERE / "package_manifest.json"
FREEZE_RECEIPT = HERE / "package_freeze_receipt.json"
EXPECTED_CANDIDATE_SHA = "257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55"
EXPECTED_PARENT_SHA = "ebfbe6e91008cf39d1929d52a60e3cb140d2b1cffdd3fac8e06c122eb9876bbe"
EXPECTED_ROOT_MAIN_SHA = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"
EXPECTED_RESEARCH_RECEIPT_SHA = "86d70abbf809baf29c6227141036624131856bed40b7f04664f13ba7093693c9"
EXPECTED_FIXTURES = {
    "live-114260122",
    "live-114274897",
    "top20-20-Densike-114270616",
}
FIELDS = (
    "candidate_reward", "opponent_reward", "result", "candidate_status",
    "opponent_status", "frames", "candidate_telemetry",
)


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_sha(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")).hexdigest()


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def require(condition: bool, message: str):
    if not condition:
        raise RuntimeError(message)


def add_file(files: dict[str, str], path: Path, expected: str | None = None):
    path = Path(path).resolve(strict=True)
    digest = sha(path)
    if expected is not None:
        require(digest == expected, f"hash mismatch for {path}: {digest}")
    key = str(path)
    prior = files.get(key)
    require(prior in (None, digest), f"conflicting file binding for {key}")
    files[key] = digest


def check_pet_guard(telemetry, key):
    branch = telemetry.get("a44_pet_market_gate_branch72")
    require(branch == telemetry.get("bridge_selected"),
            f"actual step-72 bridge field mismatch for {key}")
    require(branch in {"source", "shared150", "shared151"},
            f"unrecognized step-72 bridge branch for {key}: {branch!r}")
    active = (
        branch == "source"
        and telemetry.get("a44_pet_market_gate_key72") == "PET_CAFE|M8+|C>S|G0"
        and int(telemetry.get("a44_pet_market_gate_rival_melon72", -1)) == 12
        and int(telemetry.get("a44_pet_market_gate_wheat_stock72", -1)) == 9975
    )
    require(telemetry.get("a44_pet_market_gate_active72") is active,
            f"step-72 guard does not match branch/public fields for {key}")
    require(telemetry.get("a44_pet_market_gate_route72") == ("113517834" if active else ""),
            f"Pet route effect does not match activation for {key}")
    require(int(telemetry.get("a44_pet_market_gate_turns", -1)) == (647 if active else 0),
            f"Pet call count does not match activation for {key}")
    require(int(telemetry.get("a44_pet_market_gate_errors", -1)) == 0,
            f"Pet gate error counter is nonzero for {key}")
    if key[0] == "live-114260122":
        require(active, f"Pet target is not active on the frozen source branch: {key}")
    else:
        require(not active, f"Pet guard unexpectedly activates on an inactive row: {key}")
    if key[0] == "live-114274897":
        require(telemetry.get("iso_pasture_leaf_route72") == "113332529"
                and int(telemetry.get("iso_pasture_leaf_turns", -1)) == 647,
                f"Brunch route telemetry changed on pasture target: {key}")
    if key[0] == "top20-20-Densike-114270616":
        require(telemetry.get("iso_pasture_leaf_route72") == "",
                f"top20 control activated the pasture leaf: {key}")


def main():
    require(not MANIFEST_PATH.exists(), "package manifest already exists; inspect it without rebuilding")
    require(not FREEZE_RECEIPT.exists(), "package freeze receipt already exists; inspect it without rebuilding")
    require(not (HERE / "loader_parity.json").exists() and not (HERE / "loader_failure.json").exists(),
            "loader output already exists; inspect it without rebuilding")

    require(sha(SOURCE_CANDIDATE) == EXPECTED_CANDIDATE_SHA, "guard source hash mismatch")
    require(sha(HERE / "main.py") == EXPECTED_CANDIDATE_SHA, "package main.py mismatch")
    require(sha(ROOT_BACKUP) == EXPECTED_CANDIDATE_SHA, "requested root backup mismatch")
    require(sha(ROOT_MAIN) == EXPECTED_ROOT_MAIN_SHA, "root main hash changed")
    require(sha(RESEARCH_RECEIPT) == EXPECTED_RESEARCH_RECEIPT_SHA,
            "parent reactive research receipt changed")

    frozen = read_json(PRESERVATION_MANIFEST)
    require(frozen.get("candidate_sha256") == EXPECTED_CANDIDATE_SHA,
            "preservation manifest candidate mismatch")
    require(frozen.get("planned_games") == 102
            and frozen.get("fixed_tape_only") is True
            and frozen.get("preservation_only") is True,
            "preservation manifest scope mismatch")
    require(frozen.get("runner_sha256") == sha(PRESERVATION_RUNNER),
            "preservation runner differs from its frozen manifest")
    for path, digest in frozen.get("bindings", {}).items():
        require(sha(Path(path)) == digest, f"preservation manifest input changed: {path}")
    require(frozen["bindings"].get(str(SOURCE_CANDIDATE.resolve())) == EXPECTED_CANDIDATE_SHA,
            "preservation manifest does not bind the guarded candidate")

    preserved = read_json(PRESERVATION_RECEIPT)
    preservation_manifest_sha = sha(PRESERVATION_MANIFEST)
    preservation_receipt_sha = sha(PRESERVATION_RECEIPT)
    preservation_outcomes_sha = sha(PRESERVATION_OUTCOMES)
    require(preserved.get("candidate_sha256") == EXPECTED_CANDIDATE_SHA,
            "preservation receipt candidate mismatch")
    require(preserved.get("parent_candidate_sha256") == EXPECTED_PARENT_SHA,
            "preservation receipt parent mismatch")
    require(preserved.get("manifest_sha256") == preservation_manifest_sha,
            "preservation receipt does not bind preservation manifest")
    require(preserved.get("complete") is True and preserved.get("passed") is True,
            "preservation receipt must be complete and passed before package freeze")
    require(preserved.get("fixed_tape_only") is True and preserved.get("preservation_only") is True
            and preserved.get("research_promotion") is False,
            "preservation receipt scope or promotion label changed")
    require(preserved.get("winning_sweeps") == {"loss30": 27, "top20": 19},
            "preservation sweep counts differ from frozen requirement")
    preservation_rows = preserved.get("games", [])
    require(len(preservation_rows) == 102, "preservation receipt must contain all 102 jobs")
    require(all(row.get("passed") is True and all(row.get("checks", {}).values())
                for row in preservation_rows),
            "preservation receipt has a failed row/check")

    source_panel = read_json(SOURCE_PANEL)
    panel_rows = {}
    for row in source_panel.get("games", []) + source_panel.get("controls", []):
        seat = row.get("candidate_seat", row.get("seat"))
        key = (row["fixture_id"], int(seat))
        if key[0] in EXPECTED_FIXTURES:
            require(key not in panel_rows, f"duplicate frozen panel row: {key}")
            panel_rows[key] = row
    expected_keys = {
        (fixture_id, seat) for fixture_id in EXPECTED_FIXTURES for seat in (0, 1)
    }
    require(set(panel_rows) == expected_keys, "frozen source panel lacks one of the six selected rows")

    preserved_by_key = {}
    for row in preservation_rows:
        key = (row["fixture_id"], int(row["candidate_seat"]))
        require(key not in preserved_by_key, f"duplicate preservation row: {key}")
        preserved_by_key[key] = row
    require(expected_keys <= set(preserved_by_key), "preservation receipt lacks selected rows")

    old_package = read_json(OLD_PACKAGE_MANIFEST)
    require(old_package.get("candidate_sha256") == EXPECTED_PARENT_SHA,
            "historical EBF package does not match guarded parent")
    require(old_package.get("source_panel_sha256") == sha(SOURCE_PANEL),
            "source panel differs from historical EBF package binding")
    require(old_package.get("source_outcome_receipt_sha256") == sha(HISTORICAL_EBF_RECEIPT),
            "historical EBF receipt binding changed")
    require(sha(RESEARCH_RECEIPT) == EXPECTED_RESEARCH_RECEIPT_SHA,
            "reactive research reference hash changed")
    research = read_json(RESEARCH_RECEIPT)
    require(research.get("complete") is True and research.get("passed") is False
            and research.get("promotion") is False,
            "parent reactive result no longer records the known failed research screen")

    jobs = []
    for key in sorted(expected_keys):
        panel_row = panel_rows[key]
        preserved_row = preserved_by_key[key]
        actual = preserved_row["actual"]
        require(preserved_row.get("panel") == panel_row.get("panel"),
                f"preservation panel label differs from the frozen source panel: {key}")
        require(actual.get("candidate_sha256") == EXPECTED_CANDIDATE_SHA,
                f"preserved result candidate mismatch: {key}")
        require(actual.get("candidate_status") == actual.get("opponent_status") == "DONE"
                and actual.get("frames") == 720 and not actual.get("candidate_errors"),
                f"selected preservation result is not clean: {key}")
        telemetry = actual.get("candidate_telemetry", {})
        check_pet_guard(telemetry, key)
        expected = {field: actual[field] if field != "candidate_telemetry" else telemetry for field in FIELDS}
        fixture = panel_row["fixture"]
        job = {
            "fixture_id": key[0],
            "candidate_seat": key[1],
            "fixture": fixture,
            "source_panel": panel_row.get("panel"),
            "preservation_row_sha256": json_sha(preserved_row),
            "expected": expected,
        }
        jobs.append(job)

    from kaggle_environments.agent import get_last_callable
    candidate_bytes = (HERE / "main.py").read_bytes()
    compile(candidate_bytes, str(HERE / "main.py"), "exec")
    entrypoint = get_last_callable(candidate_bytes.decode("utf-8"), path=str(HERE / "main.py")).__name__
    require(entrypoint == "kaggle_a44_pet_market_gate_entrypoint",
            f"unexpected candidate entrypoint: {entrypoint}")

    # Inherit the exact engine, local helpers and frozen fixture inputs from
    # the completed EBF loader package, then add this candidate's preservation
    # evidence and package files. Root's separate upload_once.py is excluded.
    files: dict[str, str] = {}
    old_upload_root = OLD_UPLOAD.resolve()
    for item in old_package.get("files", []):
        path = Path(item["path"]).resolve(strict=True)
        if path == old_upload_root or old_upload_root in path.parents:
            continue
        add_file(files, path, item["sha256"])
    for path in (
        SOURCE_CANDIDATE,
        GUARD / "PLAN.md",
        PRESERVATION_MANIFEST,
        PRESERVATION_RUNNER,
        PRESERVATION_OUTCOMES,
        PRESERVATION_RECEIPT,
        OLD_PACKAGE_MANIFEST,
        OLD_UPLOAD / "package_freeze_receipt.json",
        HISTORICAL_EBF_RECEIPT,
        RESEARCH_RECEIPT,
        HERE / "main.py",
        HERE / "PLAN.md",
        HERE / "build_manifest.py",
        HERE / "verify_loader.py",
        ROOT_BACKUP,
        ROOT_MAIN,
    ):
        add_file(files, path)

    jobs_manifest = []
    for job in jobs:
        fixture = job["fixture"]
        panel_row = panel_rows[(job["fixture_id"], job["candidate_seat"])]
        jobs_manifest.append({
            "fixture_id": job["fixture_id"],
            "candidate_seat": job["candidate_seat"],
            "seed": fixture["seed"],
            "source_panel": job["source_panel"],
            "source_action_tape_path": fixture["source_action_tape_path"],
            "source_opponent_action_sha256": fixture["source_opponent_action_sha256"],
            "source_replay_path": fixture["source_replay_path"],
            "source_replay_sha256": fixture["source_replay_sha256"],
            "trace_path": panel_row["trace_path"],
            "trace_sha256": panel_row["trace_sha256"],
            "preservation_row_sha256": job["preservation_row_sha256"],
            "expected": job["expected"],
        })

    manifest = {
        "schema": "pet-source-guard-upload-loader-v1",
        "static_only": True,
        "operational_only": True,
        "research_promotion": False,
        "candidate_sha256": EXPECTED_CANDIDATE_SHA,
        "candidate_source_path": str(SOURCE_CANDIDATE.resolve()),
        "candidate_parent_sha256": EXPECTED_PARENT_SHA,
        "root_backup_path": str(ROOT_BACKUP.resolve()),
        "root_main_path": str(ROOT_MAIN.resolve()),
        "root_main_sha256": EXPECTED_ROOT_MAIN_SHA,
        "expected_entrypoint": entrypoint,
        "engine_version": old_package["engine_version"],
        "competition_slug": "kaggriculture",
        "runtime": {"python_executable": str(Path(sys.executable).resolve()),
                    "python_version": ".".join(map(str, sys.version_info[:3]))},
        "source_panel_path": str(SOURCE_PANEL.resolve()),
        "source_panel_sha256": sha(SOURCE_PANEL),
        "historical_ebf_receipt_path": str(HISTORICAL_EBF_RECEIPT.resolve()),
        "historical_ebf_receipt_sha256": sha(HISTORICAL_EBF_RECEIPT),
        "preservation_manifest_path": str(PRESERVATION_MANIFEST.resolve()),
        "preservation_manifest_sha256": preservation_manifest_sha,
        "preservation_receipt_path": str(PRESERVATION_RECEIPT.resolve()),
        "preservation_receipt_sha256": preservation_receipt_sha,
        "preservation_outcomes_path": str(PRESERVATION_OUTCOMES.resolve()),
        "preservation_outcomes_sha256": preservation_outcomes_sha,
        "research_reference_path": str(RESEARCH_RECEIPT.resolve()),
        "research_reference_sha256": sha(RESEARCH_RECEIPT),
        "research_reference_status": {
            "complete": True,
            "passed": False,
            "promotion": False,
            "scope": "parent EBF reactive screen; guarded derivative has no separate reactive qualification",
        },
        "preservation_status": {"complete": True, "passed": True, "fixed_tape_only": True,
                                "winning_sweeps": preserved["winning_sweeps"]},
        "native_game_runs_planned": 12,
        "job_count": len(jobs_manifest),
        "jobs": jobs_manifest,
        "files": [{"path": path, "sha256": digest} for path, digest in sorted(files.items())],
    }
    require(len(jobs_manifest) == 6, "builder did not produce six seat jobs")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
                             encoding="utf-8", newline="\n")

    # Run only checker compile/binding gates. This function does not call run()
    # or obtain the shared-game lock.
    checker = HERE / "verify_loader.py"
    checker_module = types.ModuleType("pet_source_guard_static_loader_check")
    checker_module.__file__ = str(checker)
    exec(compile(checker.read_bytes(), str(checker), "exec"), checker_module.__dict__)
    frozen_manifest, frozen_jobs, frozen_entrypoint = checker_module.verify_bindings()
    require(len(frozen_jobs) == 6 and frozen_entrypoint == entrypoint,
            "static loader binding verification returned an unexpected scope")

    research_record = read_json(RESEARCH_RECEIPT)
    freeze = {
        "schema": "pet-source-guard-loader-package-static-freeze-v1",
        "static_only": True,
        "native_games_executed": 0,
        "upload_or_kaggle_calls": 0,
        "candidate_sha256": EXPECTED_CANDIDATE_SHA,
        "package_main_sha256": sha(HERE / "main.py"),
        "source_candidate_sha256": sha(SOURCE_CANDIDATE),
        "root_backup_sha256": sha(ROOT_BACKUP),
        "root_main_sha256": sha(ROOT_MAIN),
        "package_manifest_sha256": sha(MANIFEST_PATH),
        "plan_sha256": sha(HERE / "PLAN.md"),
        "manifest_builder_sha256": sha(HERE / "build_manifest.py"),
        "loader_checker_sha256": sha(checker),
        "entrypoint": frozen_entrypoint,
        "preservation": {
            "status": "passed",
            "receipt_sha256": preservation_receipt_sha,
            "manifest_sha256": preservation_manifest_sha,
            "fixed_tape_only": True,
            "rows": len(preservation_rows),
            "winning_sweeps": preserved["winning_sweeps"],
            "research_promotion": False,
        },
        "operational_loader": {"status": "not_run", "planned_native_games": 12},
        "research": {
            "promotion": False,
            "guarded_candidate_reactive_qualification": "not_established",
            "parent_ebf_receipt_sha256": sha(RESEARCH_RECEIPT),
            "parent_ebf_reactive_complete": research_record.get("complete"),
            "parent_ebf_reactive_passed": research_record.get("passed"),
            "parent_ebf_promotion": research_record.get("promotion"),
        },
        "static_checks": {
            "checker_compiles": True,
            "manifest_files_match": True,
            "preservation_receipt_complete_and_passed": True,
            "selected_six_rows_bind_to_preservation_and_source_panel": True,
            "candidate_callable_matches_manifest": True,
            "loader_bindings_verified_without_games": True,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    with FREEZE_RECEIPT.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(freeze, out, indent=2, ensure_ascii=True)
        out.write("\n")
    print(json.dumps({
        "static_package_frozen": True,
        "candidate_sha256": EXPECTED_CANDIDATE_SHA,
        "package_manifest_sha256": sha(MANIFEST_PATH),
        "package_freeze_receipt_sha256": sha(FREEZE_RECEIPT),
        "preservation_receipt_sha256": preservation_receipt_sha,
        "selected_fixture_seats": len(frozen_jobs),
        "loader_games_executed": 0,
        "research_promotion": False,
    }, indent=2))


if __name__ == "__main__":
    main()
