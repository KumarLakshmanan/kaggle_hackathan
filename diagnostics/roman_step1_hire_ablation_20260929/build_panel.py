from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PARENT = ROOT / "diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/candidate.py"
V8_DIR = ROOT / "diagnostics/roman_bridge_shared166_8f_20260929/6a_outcome_pilot_v8_source_only_20260929"
V8_PANEL = V8_DIR / "panel.json"
V8_BASELINES = V8_DIR / "baseline_outcomes.jsonl"
V8_RECEIPT = V8_DIR / "outcome_receipt.json"
V8_PREFIX = V8_DIR / "prefix_results.json"
PANEL_PATH = HERE / "panel.json"
MANIFEST_PATH = HERE / "frozen_manifest.json"
SHARED_LOCK = ROOT / "diagnostics/.shared_game_run.lock"
PARENT_SHA = "6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc"
TARGET_ID = "live-114270587"
CONTROL_IDS = ("public-win-114251368", "top20-18-Kaggledew Valley 🏆-114273541")
RUNTIME_OUTPUTS = (
    "baseline_outcomes.jsonl", "candidate_outcomes.jsonl", "prefix_results.json", "outcome_receipt.json",
    "run_manifest.json", "run.lock",
    "prefix_parent_target0.jsonl.gz", "prefix_parent_target1.jsonl.gz",
    "prefix_candidate_target0.jsonl.gz", "prefix_candidate_target1.jsonl.gz",
    "baseline_target0.jsonl.gz", "baseline_target1.jsonl.gz",
    "baseline_control0_0.jsonl.gz", "baseline_control0_1.jsonl.gz",
    "baseline_control1_0.jsonl.gz", "baseline_control1_1.jsonl.gz",
    "candidate_target0.jsonl.gz", "candidate_target1.jsonl.gz",
    "candidate_control0_0.jsonl.gz", "candidate_control0_1.jsonl.gz",
    "candidate_control1_0.jsonl.gz", "candidate_control1_1.jsonl.gz",
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


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


def build_panel():
    if sha(PARENT) != PARENT_SHA:
        raise AssertionError("exact 6a parent source changed")
    old_panel = read(V8_PANEL)
    old_receipt = read(V8_RECEIPT)
    old_prefix = read(V8_PREFIX)
    if (old_panel.get("parent_candidate_sha256") != PARENT_SHA
            or old_receipt.get("parent_candidate_sha256") != PARENT_SHA
            or old_receipt.get("baseline_game_count") != 6
            or not old_receipt.get("complete")
            or old_prefix.get("passed") is not True
            or len(old_prefix.get("results", [])) != 2):
        raise AssertionError("v8 exact-6a baseline provenance is invalid")

    baselines = {}
    for line in V8_BASELINES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("parent_candidate_sha256") != PARENT_SHA:
            raise AssertionError("v8 baseline row has unexpected parent hash")
        baselines[(row["fixture_id"], int(row["seat"]))] = row["parent"]

    jobs = []
    tag_by_key = {}
    controls_seen = {key: 0 for key in CONTROL_IDS}
    for old_job in old_panel.get("jobs", []):
        fixture_id = old_job.get("fixture_id")
        seat = int(old_job.get("seat", -1))
        key = (fixture_id, seat)
        if key in tag_by_key:
            raise AssertionError(f"duplicate fixed-panel job {key}")
        reference = baselines.get(key)
        if reference is None or reference.get("candidate_sha256") != PARENT_SHA:
            raise AssertionError(f"missing exact 6a baseline for {key}")
        if fixture_id == TARGET_ID:
            tag = f"target{seat}"
            role = "target_loss"
        elif fixture_id == CONTROL_IDS[0]:
            tag = f"control0_{seat}"
            role = "public_win_control"
            controls_seen[CONTROL_IDS[0]] += 1
        elif fixture_id == CONTROL_IDS[1]:
            tag = f"control1_{seat}"
            role = "top20_control"
            controls_seen[CONTROL_IDS[1]] += 1
        else:
            raise AssertionError(f"unexpected fixture {fixture_id}")
        tag_by_key[key] = tag
        jobs.append({
            "fixture_id": fixture_id,
            "seat": seat,
            "tag": tag,
            "role": role,
            "fixture": old_job["fixture"],
            "baseline_reference": reference,
        })
    if len(jobs) != 6 or set(tag_by_key) != {
        (fixture, seat) for fixture in (TARGET_ID, *CONTROL_IDS) for seat in (0, 1)
    } or any(count != 2 for count in controls_seen.values()):
        raise AssertionError("fixed panel must contain both seats of target and controls")

    return {
        "schema": "6a-step1-hire-only-fixed-tape-pilot-v1",
        "candidate_path": str((HERE / "candidate.py").resolve()),
        "candidate_sha256": sha(HERE / "candidate.py"),
        "parent_candidate_sha256": PARENT_SHA,
        "v8_panel_sha256": sha(V8_PANEL),
        "v8_baselines_sha256": sha(V8_BASELINES),
        "v8_receipt_sha256": sha(V8_RECEIPT),
        "v8_prefix_sha256": sha(V8_PREFIX),
        "fixed_tape_only": True,
        "reactive_validation": False,
        "promotion": False,
        "target_fixture": TARGET_ID,
        "control_fixtures": list(CONTROL_IDS),
        "jobs": jobs,
        "gates": {
            "six_direct_6a_baselines_match_v8_receipt": True,
        "candidate_adds_only_one_step1_trailing_hire_on_target": True,
        "native_prefix_confirms_hire_and_five_hand_parent_actions": True,
            "both_controls_match_all_observations_and_actions": True,
            "both_target_seats_win_positive_margin": True,
            "all_games_done_done_720_without_errors": True,
        },
    }


def binding_paths(panel):
    paths = [
        HERE / "PLAN.md", HERE / "build_panel.py", HERE / "run.py",
        HERE / "candidate.py", PANEL_PATH,
        PARENT, V8_PANEL, V8_BASELINES, V8_RECEIPT, V8_PREFIX,
        ROOT / "diagnostics/stream_replay_io_20260928/fast_game_cached.py",
        ROOT / "diagnostics/stream_replay_io_20260928/cached_input.py",
        ROOT / "diagnostics/physical_route_rollout_20260928/native_core.py",
        ROOT / "diagnostics/physical_route_rollout_20260928/check.py",
        ROOT / "diagnostics/local_target_20260928/run_lock.py",
        engine_path(),
    ]
    for job in panel["jobs"]:
        fixture = job["fixture"]
        paths.extend((Path(fixture["source_replay_path"]),
                      Path(fixture["source_action_tape_path"])))
    return sorted({Path(path).resolve() for path in paths}, key=str)


def freeze():
    if PANEL_PATH.exists() or MANIFEST_PATH.exists():
        raise FileExistsError("one-shot freeze already exists")
    if any((HERE / name).exists() for name in RUNTIME_OUTPUTS):
        raise FileExistsError("runtime output exists before freeze")
    if any(HERE.rglob("*.pyc")):
        raise RuntimeError("unbound local bytecode is forbidden")
    panel = build_panel()
    PANEL_PATH.write_text(json.dumps(panel, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8", newline="\n")
    bindings = {str(path): sha(path) for path in binding_paths(panel)}
    manifest = {
        "schema": "6a-step1-hire-only-freeze-v1",
        "complete": True,
        "diagnostic_only": True,
        "fixed_tape_only": True,
        "reactive_validation": False,
        "promotion": False,
        "candidate_sha256": panel["candidate_sha256"],
        "parent_candidate_sha256": PARENT_SHA,
        "panel_sha256": sha(PANEL_PATH),
        "binding_count": len(bindings),
        "bindings": bindings,
        "shared_lock_path": str(SHARED_LOCK.resolve()),
        "resume_allowed": False,
        "worker_count": 1,
        "game_count": 12,
        "native_prefix_pair_count": 2,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8", newline="\n")
    return manifest


if __name__ == "__main__":
    print(json.dumps(freeze(), ensure_ascii=True, indent=2))
