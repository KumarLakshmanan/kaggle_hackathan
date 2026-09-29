from __future__ import annotations

"""Static-only freeze and verification for the four-game outcome pilot."""

from datetime import datetime, timezone
from pathlib import Path
import ast
import hashlib
import importlib.metadata
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
CANDIDATE_DIR = HERE.parent
ROOT = HERE.parents[2]
SIXD_DIR = ROOT / "diagnostics" / "a44_goose4_smoothie_source_20260929"
PREFIX_DIR = CANDIDATE_DIR
PASTURE_DIR = ROOT / "diagnostics" / "pasture_guard_source_leaf_20260928"
ENGINE_HELPER_DIR = ROOT / "diagnostics" / "physical_route_rollout_20260928"
CACHE_HELPER_DIR = ROOT / "diagnostics" / "stream_replay_io_20260928"
LOCK_HELPER = ROOT / "diagnostics" / "local_target_20260928" / "run_lock.py"

MANIFEST_PATH = HERE / "outcome_manifest.json"
PREFLIGHT_PATH = HERE / "static_preflight.json"
RECEIPT_PATH = HERE / "freeze_receipt.json"
PLAN_PATH = HERE / "PLAN.md"
RUNNER_PATH = HERE / "run_outcomes.py"
BUILDER_PATH = HERE / "build_outcome.py"
RUN_DIR = HERE / "run_001"

EXPECTED_CANDIDATE_SHA = "5b4ef52d19cb8ffb310b2bb067c725810241668667a0b5b468ac09b6b9215506"
EXPECTED_6D_SHA = "6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9"
EXPECTED_GOOSE4_REUSE_SHA = "c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632"
EXPECTED_A44_SHA = "a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f"
LEAF_KEY = "BRUNCH_SPOT|M8+|C>S|G+"
LEAF_ROUTE = "113332529"
BASELINE_FIELDS = (
    "result", "candidate_reward", "opponent_reward", "margin",
    "candidate_status", "opponent_status", "frames",
)
TARGETS = {
    "live-114274897": {"role": "THIRD", "panel": "loss30", "leaf": True},
    "public-win-114193811": {"role": "ChrisTu", "panel": "public-win", "leaf": False},
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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


def engine_source_path() -> tuple[Path, str]:
    spec = importlib.util.find_spec("kaggle_environments")
    require(spec is not None and spec.origin is not None, "Installed Kaggriculture engine is unavailable")
    engine = Path(spec.origin).parent / "envs" / "kaggriculture" / "kaggriculture.py"
    require(engine.is_file(), f"Installed Kaggriculture engine source is missing: {engine}")
    version = importlib.metadata.version("kaggle-environments")
    require(version == "1.32.7", f"Expected Kaggle engine 1.32.7, found {version}")
    return engine.resolve(), version


def extracted_engine_text(engine: Path) -> str:
    source = engine.read_text(encoding="utf-8")
    syntax = ast.parse(source)
    kept = []
    for node in syntax.body:
        if isinstance(node, ast.Assign) and node.lineno < 121:
            names = [name.id for name in node.targets if isinstance(name, ast.Name)]
            if names and all(name.isupper() for name in names):
                kept.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name != "_initialize" and node.lineno < 968:
            kept.append(node)
    text = '"""Pure Kaggriculture 1.32.7 transitions; initialized-state use only."""\nimport math\nimport random\n\n'
    text += "\n\n".join(ast.get_source_segment(source, node) for node in kept)
    text += '\n\ndef _initialize(state, env):\n    raise ValueError("An initialized observation is required")\n'
    return text


def add_binding(bindings: dict, roles: dict, path: Path, role: str) -> None:
    path = Path(path).resolve()
    require(path.is_file(), f"Required frozen input is missing: {path}")
    key = str(path)
    digest = sha256(path)
    if key in bindings:
        require(bindings[key] == digest, f"Conflicting binding for {path}")
        roles[key] = sorted(set(roles[key] + [role]))
    else:
        bindings[key] = digest
        roles[key] = [role]


def load_and_check_sources() -> tuple[dict, dict, dict, dict, dict, dict]:
    sixd_manifest_path = SIXD_DIR / "frozen_manifest.json"
    sixd_manifest = read_json(sixd_manifest_path)
    require(sixd_manifest.get("complete") is True, "6d upstream manifest is incomplete")
    require(sixd_manifest.get("candidate_sha256") == EXPECTED_6D_SHA, "6d candidate hash changed")
    require(sixd_manifest.get("source_a44_sha256") == EXPECTED_A44_SHA, "a44 base hash changed")
    sixd_combined = read_json(SIXD_DIR / "combined_results.json")
    require(sixd_combined.get("complete") is True and sixd_combined.get("fixed_tape_only") is True,
            "6d combined baseline is incomplete or has unexpected protocol")
    require(sixd_combined.get("candidate_sha256") == EXPECTED_6D_SHA, "combined baseline is not exact 6d")
    require(sixd_combined.get("panel_sha256") == sixd_manifest.get("full_panel_sha256"),
            "6d combined panel hash mismatch")

    parent_panel = read_json(SIXD_DIR / "parent_panel.json")
    require(parent_panel.get("fixture_count") == 104 and len(parent_panel.get("fixtures", [])) == 104,
            "6d parent panel must contain all 104 fixtures")
    sixd_panel = read_json(SIXD_DIR / "panel.json")
    require(sixd_panel.get("candidate") == "exact a44 + Goose4 + source-only Smoothie continuation",
            "6d six-fixture panel scope changed")

    prefix_manifest_path = PREFIX_DIR / "prefix_manifest.json"
    prefix_results_path = PREFIX_DIR / "prefix_results.json"
    prefix_static_path = PREFIX_DIR / "static_preflight.json"
    prefix_receipt_path = PREFIX_DIR / "prefix_freeze_receipt.json"
    prefix_manifest = read_json(prefix_manifest_path)
    prefix_results = read_json(prefix_results_path)
    prefix_static = read_json(prefix_static_path)
    prefix_receipt = read_json(prefix_receipt_path)
    require(prefix_results.get("complete") is True and prefix_results.get("passed") is True,
            "four-seat exact-6d source prefix result did not pass")
    require(prefix_results.get("candidate_sha256") == EXPECTED_CANDIDATE_SHA,
            "prefix result candidate is not the frozen pasture derivative")
    require(prefix_manifest.get("candidate", {}).get("sha256") == EXPECTED_CANDIDATE_SHA,
            "prefix manifest candidate hash mismatch")
    require(prefix_results.get("manifest_sha256") == sha256(prefix_manifest_path),
            "prefix result does not bind the current prefix manifest")
    require(prefix_static.get("passed") is True and prefix_static.get("static_only") is True,
            "upstream pasture static preflight did not pass")
    require(prefix_static.get("candidate_sha256") == EXPECTED_CANDIDATE_SHA,
            "upstream pasture static preflight candidate mismatch")
    require(prefix_receipt.get("static_freeze_passed") is True
            and prefix_receipt.get("manifest_sha256") == sha256(prefix_manifest_path),
            "upstream prefix freeze receipt is incomplete or mismatched")
    require(prefix_results.get("job_count") == 4 and len(prefix_results.get("jobs", [])) == 4,
            "expected exactly four passed prefix jobs")

    baseline_rows = {
        (row["fixture_id"], int(row["candidate_seat"])): row
        for row in sixd_combined.get("games", [])
    }
    require(len(sixd_combined.get("games", [])) == 208 and len(baseline_rows) == 208,
            "exact 6d combined baseline must have 208 unique seat rows")
    parent_fixtures = {row["fixture_id"]: row for row in parent_panel["fixtures"]}
    require(set(TARGETS).issubset(parent_fixtures), "target fixtures are absent from the full parent panel")
    prefix_jobs = {row["job_id"]: row for row in prefix_manifest.get("jobs", [])}
    prefix_result_jobs = {row["job_id"]: row for row in prefix_results.get("jobs", [])}
    census_rows = {
        (row["fixture_id"], int(row["seat"])): row
        for row in prefix_static["census"]["rows"]
        if row["fixture_id"] in TARGETS
    }
    require(len(census_rows) == 4, "expected four target rows in the frozen 208-row census")
    return sixd_manifest, sixd_combined, parent_panel, prefix_manifest, prefix_results, {
        "prefix_static": prefix_static,
        "prefix_receipt": prefix_receipt,
        "sixd_panel": sixd_panel,
        "baseline_rows": baseline_rows,
        "parent_fixtures": parent_fixtures,
        "prefix_jobs": prefix_jobs,
        "prefix_result_jobs": prefix_result_jobs,
        "census_rows": census_rows,
    }


def build_jobs(aux: dict) -> list:
    jobs = []
    for fixture_id, target in TARGETS.items():
        parent_fixture = aux["parent_fixtures"][fixture_id]
        for seat in (0, 1):
            job_id = f"{fixture_id}-seat{seat}"
            prefix_job = aux["prefix_jobs"][job_id]
            prefix_row = aux["prefix_result_jobs"][job_id]
            census = aux["census_rows"][(fixture_id, seat)]
            baseline = aux["baseline_rows"][(fixture_id, seat)]
            require(prefix_row.get("passed") is True, f"prefix row failed: {job_id}")
            require(prefix_row.get("candidate_sha256") == EXPECTED_CANDIDATE_SHA, f"prefix candidate mismatch: {job_id}")
            require(prefix_row.get("candidate_selected_branch") == "source"
                    and prefix_row.get("candidate_requested_branch") == "source",
                    f"prefix did not prove source fallback: {job_id}")
            require(int(prefix_row["candidate_step1_public_features"]["rival_hands"]) == census["rival_hands_step1"],
                    f"prefix step-1 hand feature differs from census: {job_id}")
            require(int(prefix_row["candidate_step1_public_features"]["rival_pastures"]) == census["rival_pasture_count_step1"],
                    f"prefix step-1 pasture feature differs from census: {job_id}")
            key72 = prefix_row["candidate_reported_step72_key"]
            require(prefix_row.get("candidate_pasture_stats", {}).get("pasture_brunch_key72") == key72,
                    f"prefix Brunch key telemetry mismatch: {job_id}")
            if target["leaf"]:
                require(key72 == LEAF_KEY, f"THIRD source prefix did not activate the Brunch goose key: {job_id}")
                require(prefix_row.get("candidate_reported_step72_route") == LEAF_ROUTE
                        and prefix_row.get("candidate_reported_leaf_turns") == 1,
                        f"THIRD source prefix route proof changed: {job_id}")
            else:
                require(key72 != LEAF_KEY, f"ChrisTu source prefix unexpectedly activated the leaf: {job_id}")
                require(prefix_row.get("candidate_reported_step72_route") == ""
                        and prefix_row.get("candidate_reported_leaf_turns") == 0,
                        f"ChrisTu source prefix leaf was not inactive: {job_id}")

            fixture = prefix_job["fixture"]
            for field in ("seed", "source_replay_path", "source_replay_sha256",
                          "source_action_tape_path", "source_opponent_action_sha256"):
                require(fixture[field] == parent_fixture[field], f"parent/prefix fixture binding differs: {job_id} {field}")
            require(target["panel"] == parent_fixture["panel"], f"target panel label mismatch: {fixture_id}")
            require(int(fixture["seed"]) == int(parent_fixture["seed"]), f"target seed mismatch: {fixture_id}")

            require(baseline.get("candidate_status") == "DONE"
                    and baseline.get("opponent_status") == "DONE"
                    and baseline.get("frames") == 720
                    and baseline.get("candidate_errors") == {},
                    f"6d combined baseline row is not clean: {job_id}")
            require(baseline.get("decision_equivalence_reuse") is True
                    and baseline.get("reused_parent_candidate_sha256") == EXPECTED_GOOSE4_REUSE_SHA,
                    f"6d combined baseline reuse provenance changed: {job_id}")
            require(baseline.get("candidate_sha256") == EXPECTED_GOOSE4_REUSE_SHA,
                    f"6d combined baseline row source hash changed: {job_id}")
            if target["leaf"]:
                require(baseline["result"] == "loss", f"THIRD baseline is no longer a loss: {job_id}")
            else:
                require(baseline["result"] == "win", f"ChrisTu control baseline is no longer a win: {job_id}")

            trace = prefix_job["source_trace_provenance"]
            expected = {field: baseline[field] for field in BASELINE_FIELDS}
            jobs.append({
                "job_id": job_id,
                "fixture_id": fixture_id,
                "seat": seat,
                "panel": target["panel"],
                "role": target["role"],
                "seed": int(fixture["seed"]),
                "fixture": {
                    "source_replay_path": fixture["source_replay_path"],
                    "source_replay_sha256": fixture["source_replay_sha256"],
                    "source_action_tape_path": fixture["source_action_tape_path"],
                    "source_opponent_action_sha256": fixture["source_opponent_action_sha256"],
                },
                "parent_trace_provenance": {
                    "path": trace["path"],
                    "sha256": trace["sha256"],
                    "usage": trace["usage"],
                },
                "expected_step1_public": {
                    "rival_hands": int(census["rival_hands_step1"]),
                    "rival_pastures": int(census["rival_pasture_count_step1"]),
                    "requested_branch": "source",
                    "selected_branch": "source",
                },
                "expected_step72": {
                    "branch": "source",
                    "key": key72,
                    "leaf_active": bool(target["leaf"]),
                    "route": LEAF_ROUTE if target["leaf"] else "",
                    "active_turns": 647 if target["leaf"] else 0,
                },
                "baseline_6d": expected,
                "baseline_row_provenance": {
                    "combined_candidate_sha256": EXPECTED_6D_SHA,
                    "row_candidate_sha256": baseline["candidate_sha256"],
                    "decision_equivalence_reuse": baseline["decision_equivalence_reuse"],
                    "reused_parent_candidate_sha256": baseline["reused_parent_candidate_sha256"],
                },
            })
    require([(job["fixture_id"], job["seat"]) for job in jobs] == [
        (fixture_id, seat) for fixture_id in TARGETS for seat in (0, 1)
    ], "job order changed")
    return jobs


def make_manifest() -> dict:
    sixd_manifest, sixd_combined, parent_panel, prefix_manifest, prefix_results, aux = load_and_check_sources()
    engine_path, engine_version = engine_source_path()
    core_path = ENGINE_HELPER_DIR / "native_core.py"
    extracted = extracted_engine_text(engine_path)
    require(core_path.read_text(encoding="utf-8") == extracted,
            "frozen native transition core no longer matches the installed Kaggriculture source")

    bindings: dict[str, str] = {}
    roles: dict[str, list[str]] = {}
    package = {
        "candidate": (CANDIDATE_DIR / "candidate.py", "candidate_derivative"),
        "parent_6d_candidate": (SIXD_DIR / "candidate.py", "exact_6d_parent_candidate"),
        "sixd_manifest": (SIXD_DIR / "frozen_manifest.json", "exact_6d_manifest"),
        "sixd_combined_results": (SIXD_DIR / "combined_results.json", "exact_6d_combined_baseline"),
        "sixd_parent_panel": (SIXD_DIR / "parent_panel.json", "104_fixture_parent_panel"),
        "sixd_panel": (SIXD_DIR / "panel.json", "sixd_candidate_panel"),
        "sixd_reuse_rows": (SIXD_DIR / "reuse_rows.json", "sixd_baseline_reuse_provenance"),
        "sixd_preflight": (SIXD_DIR / "preflight.json", "sixd_static_preflight"),
        "sixd_candidate_receipt": (SIXD_DIR / "candidate.json", "sixd_candidate_outcomes"),
        "prefix_result": (PREFIX_DIR / "prefix_results.json", "passed_four_seat_prefix_result"),
        "prefix_manifest": (PREFIX_DIR / "prefix_manifest.json", "four_seat_prefix_manifest"),
        "prefix_static_preflight": (PREFIX_DIR / "static_preflight.json", "prefix_static_preflight"),
        "prefix_freeze_receipt": (PREFIX_DIR / "prefix_freeze_receipt.json", "prefix_freeze_receipt"),
        "outcome_plan": (PLAN_PATH, "outcome_plan"),
        "outcome_builder": (BUILDER_PATH, "outcome_builder"),
        "outcome_runner": (RUNNER_PATH, "outcome_runner"),
        "cached_game_helper": (CACHE_HELPER_DIR / "fast_game_cached.py", "native_game_helper"),
        "cached_input_helper": (CACHE_HELPER_DIR / "cached_input.py", "replay_cache_loader"),
        "initial_state_cache": (CACHE_HELPER_DIR / "initial_states.json", "initial_state_cache"),
        "native_transition_core": (core_path, "native_transition_core"),
        "native_state_helpers": (ENGINE_HELPER_DIR / "check.py", "native_state_helpers"),
        "run_lock_helper": (LOCK_HELPER, "exclusive_lock_helper"),
        "installed_kaggriculture_engine": (engine_path, "installed_kaggriculture_1_32_7_engine"),
    }
    package_bindings = {}
    for name, (path, role) in package.items():
        add_binding(bindings, roles, path, role)
        package_bindings[name] = {"path": str(path.resolve()), "sha256": sha256(path)}

    for path_string, digest in sixd_manifest["bindings"].items():
        path = Path(path_string)
        require(sha256(path) == digest, f"upstream 6d manifest binding changed: {path}")
        add_binding(bindings, roles, path, "inherited_exact_6d_manifest_binding")
    for path_string, digest in prefix_manifest["file_bindings"].items():
        path = Path(path_string)
        require(sha256(path) == digest, f"upstream prefix manifest binding changed: {path}")
        add_binding(bindings, roles, path, "inherited_passed_prefix_manifest_binding")

    jobs = build_jobs(aux)
    for job in jobs:
        for role, field in (
            ("selected_fixture_replay", "source_replay_path"),
            ("selected_fixture_action_tape", "source_action_tape_path"),
        ):
            add_binding(bindings, roles, Path(job["fixture"][field]), role)
        add_binding(bindings, roles, Path(job["parent_trace_provenance"]["path"]), "parent_fixture_trace_provenance")

    matrix_json = json.dumps(jobs, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sixd_manifest_path = SIXD_DIR / "frozen_manifest.json"
    combined_path = SIXD_DIR / "combined_results.json"
    parent_panel_path = SIXD_DIR / "parent_panel.json"
    prefix_manifest_path = PREFIX_DIR / "prefix_manifest.json"
    prefix_result_path = PREFIX_DIR / "prefix_results.json"
    prefix_static_path = PREFIX_DIR / "static_preflight.json"
    return {
        "schema": "a44-goose4-smoothie-pasture-terminal-outcome-manifest-v1",
        "diagnostic_only": True,
        "fixed_action_tape_only": True,
        "static_freeze_only": True,
        "candidate": {
            "path": str((CANDIDATE_DIR / "candidate.py").resolve()),
            "sha256": EXPECTED_CANDIDATE_SHA,
        },
        "parent_6d_candidate": {
            "path": str((SIXD_DIR / "candidate.py").resolve()),
            "sha256": EXPECTED_6D_SHA,
        },
        "baseline": {
            "kind": "exact_6d_combined_results",
            "path": str(combined_path.resolve()),
            "sha256": sha256(combined_path),
            "combined_candidate_sha256": EXPECTED_6D_SHA,
            "full_panel_sha256": sixd_manifest["full_panel_sha256"],
            "parent_panel_path": str(parent_panel_path.resolve()),
            "parent_panel_sha256": sha256(parent_panel_path),
            "fixture_count": parent_panel["fixture_count"],
            "row_count": len(sixd_combined["games"]),
            "reused_row_note": (
                "The four selected exact-6d combined rows are marked as decision-equivalence reuse "
                "of the frozen Goose4 parent; per-row source SHA is retained in each job."
            ),
        },
        "prefix_proof": {
            "result_path": str(prefix_result_path.resolve()),
            "result_sha256": sha256(prefix_result_path),
            "manifest_path": str(prefix_manifest_path.resolve()),
            "manifest_sha256": sha256(prefix_manifest_path),
            "static_preflight_path": str(prefix_static_path.resolve()),
            "static_preflight_sha256": sha256(prefix_static_path),
            "freeze_receipt_sha256": sha256(PREFIX_DIR / "prefix_freeze_receipt.json"),
            "passed": True,
            "job_count": 4,
        },
        "engine": {
            "distribution": "kaggle-environments",
            "version": engine_version,
            "source_path": str(engine_path),
            "source_sha256": sha256(engine_path),
            "native_core_path": str(core_path.resolve()),
            "native_core_sha256": sha256(core_path),
            "core_exactly_reconstructed_from_engine": True,
        },
        "runner": {
            "path": str(RUNNER_PATH.resolve()),
            "sha256": sha256(RUNNER_PATH),
            "builder_path": str(BUILDER_PATH.resolve()),
            "builder_sha256": sha256(BUILDER_PATH),
            "workers": 1,
            "execution": "one sequential worker, four fixed action-tape games",
            "resume_allowed": False,
            "overwrite_allowed": False,
            "shared_lock_path": "diagnostics/.shared_game_run.lock",
            "study_lock_path": str((HERE / ".outcome_run_20260929.lock").resolve()),
            "run_output_path": str(RUN_DIR.resolve()),
        },
        "outcome_gates_frozen_before_run": {
            "all_four_games_done_done_720_and_error_free": True,
            "THIRD_both_seats_win_with_positive_margin": True,
            "ChrisTu_both_seats_exactly_match_6d_baseline_result_rewards_margin_statuses_and_frames": True,
            "Brunch_route_113332529_active_only_on_THIRD_both_seats": True,
            "ChrisTu_both_seats_leaf_inactive_with_zero_turns_and_errors": True,
            "all_four_observation1_select_source_and_match_frozen_public_counts": True,
            "all_four_route_maps_reset_to_6d_base": True,
        },
        "error_free_telemetry_fields": [
            "bridge_errors", "bridge_common_failed", "bridge_guard_refusals",
            "bridge_source_guard_failed", "a44_goose4_errors",
            "a44_smoothie_errors", "pasture_brunch_errors",
        ],
        "jobs": jobs,
        "job_count": len(jobs),
        "workers": 1,
        "job_matrix_sha256": hashlib.sha256(matrix_json).hexdigest(),
        "input_binding_count": len(bindings),
        "file_bindings": dict(sorted(bindings.items())),
        "binding_roles": dict(sorted(roles.items())),
        "package_bindings": package_bindings,
        "upstream_manifests": {
            "sixd": {
                "path": str(sixd_manifest_path.resolve()),
                "sha256": sha256(sixd_manifest_path),
                "binding_count": len(sixd_manifest["bindings"]),
            },
            "passed_prefix": {
                "path": str(prefix_manifest_path.resolve()),
                "sha256": sha256(prefix_manifest_path),
                "binding_count": len(prefix_manifest["file_bindings"]),
            },
        },
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "simulator_jobs_run_at_freeze": 0,
        "native_transitions_at_freeze": 0,
        "full_game_outcomes_run_at_freeze": False,
    }


def verify_manifest(manifest: dict) -> dict:
    require(manifest.get("schema") == "a44-goose4-smoothie-pasture-terminal-outcome-manifest-v1",
            "outcome manifest schema mismatch")
    require(manifest.get("diagnostic_only") is True and manifest.get("fixed_action_tape_only") is True,
            "outcome scope flags mismatch")
    require(manifest.get("candidate", {}).get("sha256") == EXPECTED_CANDIDATE_SHA,
            "frozen pasture candidate hash mismatch")
    require(manifest.get("parent_6d_candidate", {}).get("sha256") == EXPECTED_6D_SHA,
            "frozen 6d parent hash mismatch")
    require(manifest.get("job_count") == 4 and len(manifest.get("jobs", [])) == 4
            and manifest.get("workers") == 1,
            "outcome job matrix or worker count mismatch")
    require(manifest.get("simulator_jobs_run_at_freeze") == 0
            and manifest.get("native_transitions_at_freeze") == 0
            and manifest.get("full_game_outcomes_run_at_freeze") is False,
            "freeze receipt claims game execution")

    current_jobs = build_jobs(load_and_check_sources()[5])
    require(manifest.get("jobs") == current_jobs, "frozen outcome job matrix differs from its upstream sources")
    matrix = json.dumps(current_jobs, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    require(manifest.get("job_matrix_sha256") == hashlib.sha256(matrix).hexdigest(),
            "job matrix hash mismatch")
    require(manifest.get("input_binding_count") == len(manifest.get("file_bindings", {})),
            "binding count mismatch")
    checked = 0
    for path_text, digest in manifest["file_bindings"].items():
        path = Path(path_text)
        require(path.is_file(), f"bound input is missing: {path}")
        require(sha256(path) == digest, f"bound input changed: {path}")
        checked += 1
    require(sha256(CANDIDATE_DIR / "candidate.py") == EXPECTED_CANDIDATE_SHA,
            "candidate file changed")
    require(sha256(SIXD_DIR / "candidate.py") == EXPECTED_6D_SHA, "exact 6d file changed")
    runner_source = RUNNER_PATH.read_text(encoding="utf-8")
    require("exclusive_run(SHARED_LOCK_PATH)" in runner_source,
            "runner does not acquire the shared game lock")
    require("exclusive_run(OWN_LOCK_PATH)" in runner_source,
            "runner does not acquire its study-local lock")
    compile(runner_source, str(RUNNER_PATH), "exec")
    require(not RUN_DIR.exists(), "run output exists before static freeze; refuse resume or overwrite")
    require(not (HERE / ".outcome_run_20260929.lock").exists(),
            "study-local lock exists during static freeze")
    return {"passed": True, "checked_binding_count": checked}


def freeze() -> dict:
    for path in (MANIFEST_PATH, PREFLIGHT_PATH, RECEIPT_PATH):
        require(not path.exists(), f"refusing to overwrite frozen outcome artifact: {path}")
    require(not RUN_DIR.exists(), f"run directory already exists: {RUN_DIR}")
    manifest = make_manifest()
    write_once(MANIFEST_PATH, manifest)
    verification = verify_manifest(manifest)
    preflight = {
        "schema": "a44-goose4-smoothie-pasture-terminal-outcome-static-preflight-v1",
        "passed": True,
        "static_only": True,
        "agent_calls": 0,
        "simulator_jobs_run": 0,
        "native_transitions": 0,
        "full_game_outcomes_run": False,
        "candidate_sha256": EXPECTED_CANDIDATE_SHA,
        "parent_6d_candidate_sha256": EXPECTED_6D_SHA,
        "manifest_path": str(MANIFEST_PATH.resolve()),
        "manifest_sha256": sha256(MANIFEST_PATH),
        "runner_path": str(RUNNER_PATH.resolve()),
        "runner_sha256": sha256(RUNNER_PATH),
        "job_count": 4,
        "workers": 1,
        "checked_binding_count": verification["checked_binding_count"],
        "exact_6d_baseline_rows": 4,
        "THIRD_win_seats_required": 2,
        "ChrisTu_exact_control_seats_required": 2,
        "native_core_engine_source_match": True,
        "run_directory_created": False,
    }
    write_once(PREFLIGHT_PATH, preflight)
    receipt = {
        "schema": "a44-goose4-smoothie-pasture-terminal-outcome-static-freeze-v1",
        "static_freeze_passed": True,
        "candidate_sha256": EXPECTED_CANDIDATE_SHA,
        "parent_6d_candidate_sha256": EXPECTED_6D_SHA,
        "manifest_path": str(MANIFEST_PATH.resolve()),
        "manifest_sha256": sha256(MANIFEST_PATH),
        "preflight_path": str(PREFLIGHT_PATH.resolve()),
        "preflight_sha256": sha256(PREFLIGHT_PATH),
        "builder_path": str(BUILDER_PATH.resolve()),
        "builder_sha256": sha256(BUILDER_PATH),
        "runner_path": str(RUNNER_PATH.resolve()),
        "runner_sha256": sha256(RUNNER_PATH),
        "file_binding_count": len(manifest["file_bindings"]),
        "job_count": 4,
        "workers": 1,
        "simulator_jobs_run": 0,
        "native_transitions": 0,
        "full_game_outcomes_run": False,
        "run_directory_created": False,
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_once(RECEIPT_PATH, receipt)
    return receipt


def verify() -> dict:
    manifest = read_json(MANIFEST_PATH)
    preflight = read_json(PREFLIGHT_PATH)
    receipt = read_json(RECEIPT_PATH)
    checked = verify_manifest(manifest)
    require(preflight.get("passed") is True and preflight.get("static_only") is True,
            "outcome static preflight did not pass")
    require(preflight.get("manifest_sha256") == sha256(MANIFEST_PATH),
            "outcome static preflight manifest hash mismatch")
    require(preflight.get("runner_sha256") == sha256(RUNNER_PATH),
            "outcome static preflight runner hash mismatch")
    require(receipt.get("static_freeze_passed") is True
            and receipt.get("manifest_sha256") == sha256(MANIFEST_PATH)
            and receipt.get("preflight_sha256") == sha256(PREFLIGHT_PATH),
            "outcome freeze receipt is incomplete or mismatched")
    require(receipt.get("simulator_jobs_run") == 0
            and receipt.get("native_transitions") == 0
            and receipt.get("full_game_outcomes_run") is False
            and receipt.get("run_directory_created") is False,
            "outcome freeze receipt reports game execution")
    return {
        "verified": True,
        "candidate_sha256": EXPECTED_CANDIDATE_SHA,
        "manifest_sha256": sha256(MANIFEST_PATH),
        "preflight_sha256": sha256(PREFLIGHT_PATH),
        "freeze_receipt_sha256": sha256(RECEIPT_PATH),
        "runner_sha256": sha256(RUNNER_PATH),
        "jobs": manifest["job_count"],
        "checked_bindings": checked["checked_binding_count"],
        "simulator_jobs_run": 0,
        "native_transitions": 0,
    }


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"freeze", "verify"}:
        raise SystemExit("usage: build_outcome.py freeze|verify")
    if sys.argv[1] == "freeze":
        print(json.dumps(freeze(), indent=2, ensure_ascii=False), flush=True)
    else:
        print(json.dumps(verify(), indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
