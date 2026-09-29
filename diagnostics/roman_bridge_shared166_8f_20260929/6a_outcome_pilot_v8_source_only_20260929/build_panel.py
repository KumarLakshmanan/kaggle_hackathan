from __future__ import annotations

import gzip
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PARENT = ROOT / "diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/candidate.py"
PARENT_PANEL = ROOT / "diagnostics/a44_goose4_smoothie_source_20260929/parent_panel.json"
SIX_A_PANEL = ROOT / "diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/goalpanel_100_retry_20260929/panel.json"
SIX_A_RECEIPT = ROOT / "diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/goalpanel_100_retry_20260929/outcome_receipt.json"
SIX_A_OUTCOMES = ROOT / "diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/goalpanel_100_retry_20260929/outcomes.jsonl"
FEATURE_CENSUS = ROOT / "diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/feature_census.json"
PREFIX_DIR = ROOT / "diagnostics/roman_bridge_shared166_8f_20260929/v5_prefix_probe_20260929"
PREFIX_FREEZE = PREFIX_DIR / "freeze_manifest.json"
PREFIX_RECEIPT = PREFIX_DIR / "prefix_receipt.json"
PREFIX_SNAPSHOTS = PREFIX_DIR / "expected_step2_public_snapshots.json"
PREFIX_RUNNER = PREFIX_DIR / "prefix_probe.py"
STATIC_PREFLIGHT = ROOT / "diagnostics/roman_bridge_shared166_8f_20260929/preflight.json"
DONOR = ROOT / "diagnostics/donor_opening_agents_20260928/candidate_shared166.py"
NATIVE_CORE = ROOT / "diagnostics/physical_route_rollout_20260928/native_core.py"
NATIVE_CHECK = ROOT / "diagnostics/physical_route_rollout_20260928/check.py"
CACHED_INPUT = ROOT / "diagnostics/stream_replay_io_20260928/cached_input.py"
INITIAL_STATES = ROOT / "diagnostics/stream_replay_io_20260928/initial_states.json"
FAST_GAME = ROOT / "diagnostics/stream_replay_io_20260928/fast_game_cached.py"
RUN_LOCK = ROOT / "diagnostics/local_target_20260928/run_lock.py"

PARENT_SHA = "6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc"
DONOR_SHA = "fc403d05e29b1b317985f7ec77d1a3fa490c0264af8d639c3bfea899fcf1a849"
FIXTURE_IDS = (
    "live-114270587",
    "public-win-114251368",
    "top20-18-Kaggledew Valley 🏆-114273541",
)
TARGET_ID = FIXTURE_IDS[0]
CONTROL_IDS = FIXTURE_IDS[1:]
PANEL_PATH = HERE / "panel.json"
MANIFEST_PATH = HERE / "frozen_manifest.json"
RUNTIME_OUTPUTS = (
    "baseline_outcomes.jsonl", "prefix_results.json", "snapshot_discovery.json",
    "snapshot_validation.json", "live_step2_public_snapshots.json",
    "outcomes.jsonl", "outcome_receipt.json", "run_manifest.json", "run.lock",
    "target_seat0_trace.jsonl.gz", "target_seat1_trace.jsonl.gz",
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_once(path: Path, value):
    raw = (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with Path(path).open("xb") as stream:
        stream.write(raw)


def engine_path() -> Path:
    spec = importlib.util.find_spec("kaggle_environments")
    if spec is None or not spec.origin:
        raise RuntimeError("installed Kaggriculture engine is unavailable")
    if importlib.metadata.version("kaggle-environments") != "1.32.7":
        raise RuntimeError("expected Kaggriculture engine 1.32.7")
    path = Path(spec.origin).parent / "envs" / "kaggriculture" / "kaggriculture.py"
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.resolve()


def fixture_map():
    data = read(PARENT_PANEL)
    source = data.get("fixtures")
    rows = []
    if isinstance(source, dict):
        for key, value in source.items():
            if isinstance(value, dict):
                row = dict(value)
                row.setdefault("fixture_id", key)
                rows.append(row)
    elif isinstance(source, list):
        rows = [dict(row) for row in source if isinstance(row, dict)]
    result = {row.get("fixture_id"): row for row in rows}
    missing = [fixture_id for fixture_id in FIXTURE_IDS if fixture_id not in result]
    if missing:
        raise AssertionError(f"source fixture panel is missing {missing}")
    return data, result


def saved_6a_rows():
    data = read(SIX_A_PANEL)
    receipt = read(SIX_A_RECEIPT)
    if (data.get("candidate_sha256") != PARENT_SHA
            or receipt.get("candidate_sha256") != PARENT_SHA
            or receipt.get("complete") is not True
            or receipt.get("game_count") != 100):
        raise AssertionError("completed 6a panel provenance is invalid")
    rows = {}
    for line in SIX_A_OUTCOMES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (row.get("fixture_id"), int(row.get("seat", row.get("candidate_seat", -1))))
        if row.get("candidate_sha256") == PARENT_SHA:
            rows[key] = row
    return data, receipt, rows


def build_panel_data():
    if sha(PARENT) != PARENT_SHA or sha(DONOR) != DONOR_SHA:
        raise AssertionError("frozen 6a parent or shared166 donor hash changed")
    source_panel, fixtures = fixture_map()
    six_panel, six_receipt, six_rows = saved_6a_rows()
    census = read(FEATURE_CENSUS)
    if census.get("row_count") != 208 or len(census.get("rows", [])) != 208:
        raise AssertionError("expected the hash-bound 208-seat static census")

    prefix = read(PREFIX_FREEZE)
    prefix_receipt = read(PREFIX_RECEIPT)
    prefix_snapshots = read(PREFIX_SNAPSHOTS)
    static_preflight = read(STATIC_PREFLIGHT)
    if (prefix.get("complete") is not True or prefix.get("job_count") != 2
            or prefix.get("parent_candidate_sha256") != "8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62"):
        raise AssertionError("historical target prefix source manifest changed")
    if (prefix_receipt.get("passed") is not True or prefix_receipt.get("passed_seats") != 2
            or prefix_snapshots.get("complete") is not True
            or static_preflight.get("passed") is not True
            or static_preflight.get("panel_208", {}).get("trigger_count") != 2):
        raise AssertionError("historical Roman evidence or exact-trigger census changed")
    target_prefix_jobs = [job for job in prefix["jobs"] if job.get("fixture_id") == TARGET_ID]
    if len(target_prefix_jobs) != 2 or {int(job["candidate_seat"]) for job in target_prefix_jobs} != {0, 1}:
        raise AssertionError("historical target prefix manifest does not bind both seats")

    census_by_key = {(row["fixture_id"], int(row["seat"])): row for row in census["rows"]}
    jobs = []
    for fixture_id in FIXTURE_IDS:
        fixture = dict(fixtures[fixture_id])
        if fixture.get("fixture_id") != fixture_id:
            fixture["fixture_id"] = fixture_id
        for key in ("source_replay_path", "source_action_tape_path"):
            if not Path(fixture[key]).is_file():
                raise FileNotFoundError(fixture[key])
        replay_path = Path(fixture["source_replay_path"])
        tape_path = Path(fixture["source_action_tape_path"])
        if sha_bytes(gzip.decompress(replay_path.read_bytes())) != fixture["source_replay_sha256"]:
            raise AssertionError(f"decompressed replay hash mismatch: {fixture_id}")
        tape_data = json.loads(gzip.decompress(tape_path.read_bytes()))
        tape = tape_data["actions"]
        if len(tape) != 719:
            raise AssertionError(f"opponent tape length changed for {fixture_id}")
        tape_hashes = [sha_bytes(json.dumps(tape, sort_keys=sort_keys,
                                            separators=(",", ":")).encode())
                       for sort_keys in (False, True)]
        if fixture["source_opponent_action_sha256"] not in tape_hashes:
            raise AssertionError(f"opponent action tape hash mismatch: {fixture_id}")

        for seat in (0, 1):
            census_row = census_by_key.get((fixture_id, seat))
            if census_row is None:
                raise AssertionError(f"static census missing {fixture_id} seat {seat}")
            saved = None
            if fixture_id != CONTROL_IDS[0]:
                reference = six_rows.get((fixture_id, seat))
                if reference is None or not reference.get("v5_preserved", False):
                    raise AssertionError(f"completed 6a receipt lacks reference {fixture_id} seat {seat}")
                saved = reference["actual"]
            jobs.append({
                "fixture_id": fixture_id,
                "seat": seat,
                "role": "roman_target" if fixture_id == TARGET_ID else "near_miss_control",
                "trigger_expected": fixture_id == TARGET_ID,
                "fixture": fixture,
                "static_census_row": census_row,
                "saved_6a_reference": saved,
            })

    target_jobs = [job for job in target_prefix_jobs]
    parent_panel_sha = sha(PARENT_PANEL)
    panel = {
        "schema": "roman-shared166-current-6a-six-seat-outcome-pilot-v1",
        "candidate_path": str((HERE / "candidate.py").resolve()),
        "candidate_sha256": sha(HERE / "candidate.py"),
        "candidate_adapter_sha256": sha(HERE / "candidate_adapter.py"),
        "parent_candidate_sha256": PARENT_SHA,
        "donor_sha256": DONOR_SHA,
        "historical_prefix_parent_sha256": prefix["parent_candidate_sha256"],
        "source_fixture_panel_sha256": parent_panel_sha,
        "six_a_panel_sha256": sha(SIX_A_PANEL),
        "six_a_receipt_sha256": sha(SIX_A_RECEIPT),
        "fixed_tape_only": True,
        "reactive_validation": False,
        "promotion": False,
        "fixture_count": 3,
        "seat_count": 6,
        "full_game_count": 12,
        "fixtures": list(FIXTURE_IDS),
        "target_prefix_jobs": target_jobs,
        "jobs": jobs,
        "gates": {
            "all_six_6a_baselines_clean_before_adapter_discovery": True,
            "both_target_baselines_lose": True,
            "both_control_baselines_win": True,
            "6a_target_prefix_matches_historical_source_both_seats": True,
            "both_fresh_snapshot_discoveries_before_validation": True,
            "both_fresh_snapshot_validations_pass_before_candidate_games": True,
            "target_both_seats_win_positive_margin": True,
            "donor_shape_failure_returns_to_6a_parent": True,
            "parent_matches_every_post_fallback_action": True,
            "controls_exactly_match_6a_outcomes_and_rewards": True,
            "roman_activates_only_on_target": True,
            "all_games_done_done_720_no_errors": True,
        },
    }
    return panel


def binding_paths(panel):
    paths = [
        HERE / "PLAN.md", HERE / "build_panel.py", HERE / "run.py",
        HERE / "candidate.py", HERE / "candidate_adapter.py", PANEL_PATH,
        PARENT, DONOR, PARENT_PANEL, SIX_A_PANEL, SIX_A_RECEIPT, SIX_A_OUTCOMES,
        FEATURE_CENSUS, PREFIX_FREEZE, PREFIX_RECEIPT, PREFIX_SNAPSHOTS, PREFIX_RUNNER,
        STATIC_PREFLIGHT,
        NATIVE_CORE, NATIVE_CHECK, CACHED_INPUT, INITIAL_STATES, FAST_GAME, RUN_LOCK,
        engine_path(),
    ]
    for job in panel["jobs"]:
        paths.extend((Path(job["fixture"]["source_replay_path"]),
                      Path(job["fixture"]["source_action_tape_path"])))
    for job in panel["target_prefix_jobs"]:
        paths.append(Path(job["source_trace_path"]))
    return sorted({Path(path).resolve() for path in paths}, key=str)


def freeze():
    unbound_bytecode = [str(path) for path in HERE.rglob("*.pyc")]
    if unbound_bytecode:
        raise RuntimeError(f"unbound local bytecode is forbidden in the frozen pilot: {unbound_bytecode}")
    if PANEL_PATH.exists() or MANIFEST_PATH.exists():
        raise FileExistsError("pilot freeze is one-shot")
    if any((HERE / name).exists() for name in RUNTIME_OUTPUTS):
        raise FileExistsError("runtime output already exists")
    panel = build_panel_data()
    write_once(PANEL_PATH, panel)
    bindings = {str(path): sha(path) for path in binding_paths(panel)}
    manifest = {
        "schema": "roman-shared166-current-6a-frozen-outcome-pilot-v1",
        "complete": True,
        "diagnostic_only": True,
        "fixed_tape_only": True,
        "reactive_validation": False,
        "promotion": False,
        "candidate_sha256": panel["candidate_sha256"],
        "candidate_adapter_sha256": panel["candidate_adapter_sha256"],
        "parent_candidate_sha256": PARENT_SHA,
        "donor_sha256": DONOR_SHA,
        "panel_sha256": sha(PANEL_PATH),
        "binding_count": len(bindings),
        "bindings": bindings,
        "shared_lock_path": str(ROOT / "diagnostics/.shared_game_run.lock"),
        "worker_count": 1,
        "resume_allowed": False,
    }
    write_once(MANIFEST_PATH, manifest)
    print(json.dumps({key: manifest[key] for key in
                      ("complete", "candidate_sha256", "candidate_adapter_sha256",
                       "parent_candidate_sha256", "donor_sha256", "panel_sha256",
                       "binding_count")}, indent=2))


if __name__ == "__main__":
    freeze()
