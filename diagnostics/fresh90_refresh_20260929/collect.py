"""Capture a fresh top-100 replay set and public episodes for submission 56680167.

This collector only reads Kaggle data. It does not run games or submit files.
"""

from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
KAGGLE = r"C:/Users/Veeramani Selvaraj/AppData/Roaming/Python/Python314/Scripts/kaggle.exe"
COMPETITION = "kaggriculture"
CURRENT_SUBMISSION_ID = 56680167
OUR_TEAM_ID = 16674353
OUR_TEAM_NAME = "Lakshmanan R"
EXPECTED_ENGINE = "1.32.7"
MAX_WORKERS = 4

sys.path.insert(0, str(ROOT))
from refresh_top_leaderboard_routes import _write_route  # noqa: E402

WRITE_LOCK = threading.Lock()
EPISODE_LOCKS: dict[int, threading.Lock] = {}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def write_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(value)
    os.replace(temporary, path)


def decode_json(text: str | bytes, label: str) -> object:
    if isinstance(text, bytes):
        text = text.decode("utf-8-sig", errors="strict")
    else:
        text = text.lstrip("\ufeff")
    candidate = text.strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        starts = [index for index in (candidate.find("["), candidate.find("{")) if index >= 0]
        if not starts:
            raise RuntimeError(f"No JSON body in {label}: {candidate[:250]!r}")
        value = json.loads(candidate[min(starts):])
    # Kaggle has returned a JSON string containing JSON in some CLI/API paths.
    for _ in range(2):
        if not isinstance(value, str):
            break
        value = json.loads(value)
    return value


def run(args: list[str], *, timeout: int = 90, output_dir: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [KAGGLE, *args]
    if output_dir is not None:
        command.extend(["-p", str(output_dir)])
    command.append("-q")
    return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)


def run_json(args: list[str], label: str, raw_path: Path, parsed_path: Path,
             *, timeout: int = 90) -> tuple[object, dict]:
    process = run([*args, "--format", "json"], timeout=timeout)
    stdout = process.stdout.encode("utf-8")
    write_bytes(raw_path, stdout)
    if process.returncode:
        raise RuntimeError(f"Kaggle read failed for {label} (exit {process.returncode}): {process.stderr[:400]}")
    value = decode_json(process.stdout, label)
    write_json(parsed_path, value)
    return value, {"stdout_sha256": sha256(stdout), "parsed_sha256": sha256(parsed_path.read_bytes()),
                   "checked_at_utc": now(), "raw_stdout_path": str(raw_path.resolve()),
                   "parsed_path": str(parsed_path.resolve())}


def episode_lock(episode_id: int) -> threading.Lock:
    with WRITE_LOCK:
        return EPISODE_LOCKS.setdefault(episode_id, threading.Lock())


def load_replay(raw: bytes) -> object:
    value: object = json.loads(raw.decode("utf-8-sig"))
    for _ in range(2):
        if not isinstance(value, str):
            break
        value = json.loads(value)
    return value


def download_episode(episode_id: int) -> tuple[Path, bytes, dict, object]:
    """Download one replay once; preserve original bytes and a hash receipt."""
    with episode_lock(episode_id):
        archive = HERE / "raw_archive" / f"episode-{episode_id}-replay.json.gz"
        receipt_path = HERE / "raw_archive" / f"episode-{episode_id}-receipt.json"
        if archive.exists() and receipt_path.exists():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            raw = gzip.decompress(archive.read_bytes())
            if sha256(raw) != receipt.get("source_sha256"):
                raise RuntimeError(f"Cached replay hash mismatch for {episode_id}")
            return archive, raw, receipt, load_replay(raw)

        unpacked = HERE / "unpacked"
        unpacked.mkdir(parents=True, exist_ok=True)
        started = now()
        with tempfile.TemporaryDirectory(prefix=f"episode-{episode_id}-", dir=unpacked) as temporary:
            process = run(["competitions", "replay", str(episode_id)], timeout=120,
                          output_dir=Path(temporary))
            if process.returncode:
                raise RuntimeError(f"Replay {episode_id} failed (exit {process.returncode}): {process.stderr[:500]}")
            candidates = sorted(Path(temporary).glob("*.json"))
            if len(candidates) != 1:
                raise RuntimeError(f"Replay {episode_id} produced {len(candidates)} JSON files")
            raw = candidates[0].read_bytes()
        replay = load_replay(raw)
        compressed = gzip.compress(raw, compresslevel=6, mtime=0)
        write_bytes(archive, compressed)
        receipt = {
            "episode_id": episode_id,
            "downloaded_at_utc": now(),
            "download_started_at_utc": started,
            "source_sha256": sha256(raw),
            "source_bytes": len(raw),
            "archive_sha256": sha256(compressed),
            "archive_bytes": len(compressed),
            "source_cli": "kaggle competitions replay",
            "raw_archive_path": str(archive.resolve()),
        }
        write_json(receipt_path, receipt)
        return archive, raw, receipt, replay


def safe_actions(steps: list, seat: int) -> list:
    return [frame[seat].get("action") or {"farmer": ["PASS"], "hands": [], "market": []}
            for frame in steps[1:]]


def build_sidecar(episode_id: int, replay: dict, replay_path: Path, raw_receipt: dict) -> dict:
    steps = replay.get("steps") or []
    names = list((replay.get("info") or {}).get("TeamNames") or [])
    if len(names) != 2:
        raise RuntimeError(f"Replay {episode_id} has unexpected TeamNames={names!r}")
    if any(not isinstance(frame, list) or len(frame) != 2 for frame in steps):
        raise RuntimeError(f"Replay {episode_id} contains malformed step frames")
    actions = {seat: safe_actions(steps, seat) for seat in (0, 1)}
    timeline = []
    for frame_index, frame in enumerate(steps):
        states = []
        for seat in (0, 1):
            observation = frame[seat].get("observation") or {}
            states.append({
                "seat": seat,
                "step": observation.get("step"),
                "day": observation.get("day"),
                "hour": observation.get("hour"),
                "town": observation.get("town"),
                "market": observation.get("market"),
            })
        timeline.append({"frame": frame_index, "states": states})

    public_state_bytes = canonical_bytes(timeline)
    public_state_path = HERE / "episode_index" / f"episode-{episode_id}-public-state.json.gz"
    compressed_state = gzip.compress(public_state_bytes, compresslevel=6, mtime=0)
    write_bytes(public_state_path, compressed_state)
    public_state_keys = sorted({
        key for frame in steps for player in frame
        for key in ((player.get("observation") or {}).get("market") or {}).keys()
    })
    town_keys = sorted({
        key for frame in steps for player in frame
        for key in ((player.get("observation") or {}).get("town") or {}).keys()
    })
    sidecar = {
        "episode_id": episode_id,
        "source_replay_sha256": raw_receipt["source_sha256"],
        "source_replay_path": str(replay_path.resolve()),
        "team_names": names,
        "frames": len(steps),
        "actions_per_seat": {str(seat): len(actions[seat]) for seat in (0, 1)},
        "actions": {str(seat): actions[seat] for seat in (0, 1)},
        "action_sha256_by_seat": {str(seat): sha256(canonical_bytes(actions[seat])) for seat in (0, 1)},
        "public_state_sha256": sha256(public_state_bytes),
        "public_state_path": str(public_state_path.resolve()),
        "public_state_archive_sha256": sha256(compressed_state),
        "market_fields": public_state_keys,
        "town_fields": town_keys,
    }
    sidecar_path = HERE / "episode_index" / f"episode-{episode_id}-index.json.gz"
    sidecar_bytes = canonical_bytes(sidecar)
    compressed_sidecar = gzip.compress(sidecar_bytes, compresslevel=6, mtime=0)
    write_bytes(sidecar_path, compressed_sidecar)
    return {
        "episode_id": episode_id,
        "sidecar_path": str(sidecar_path.resolve()),
        "sidecar_sha256": sha256(compressed_sidecar),
        "public_state_path": str(public_state_path.resolve()),
        "public_state_sha256": sha256(public_state_bytes),
        "action_sha256_by_seat": sidecar["action_sha256_by_seat"],
        "actions_per_seat": sidecar["actions_per_seat"],
        "team_names": names,
        "frames": len(steps),
        "market_fields": public_state_keys,
        "town_fields": town_keys,
    }


def make_team_route(team_record: dict, selected: dict, slot: int, replay: dict,
                    archive: Path, raw_receipt: dict, sidecar_record: dict) -> dict:
    episode = selected["episode"]
    team_name = str(team_record.get("teamName", team_record.get("team")))
    team_id = int(team_record.get("teamId", team_record.get("team_id")))
    submission_id = int(selected["submission_id"])
    info = replay.get("info") or {}
    names = list(info.get("TeamNames") or [])
    if names.count(team_name) != 1:
        raise RuntimeError(f"Episode {episode['id']} TeamNames does not contain {team_name!r} exactly once: {names!r}")
    source_seat = names.index(team_name)
    opponent_seat = 1 - source_seat
    statuses = replay.get("statuses")
    steps = replay.get("steps") or []
    route_dir = HERE / "routes" / f"episode_{slot}"
    route_dir.mkdir(parents=True, exist_ok=True)
    row = _write_route(route_dir, team_name, team_id,
                       submission_id, episode, replay)
    row.update({
        "rank": int(team_record["rank"]),
        "team_id": team_id,
        "team": team_name,
        "snapshot_score": team_record.get("score", team_record.get("snapshot_score")),
        "submission_id": submission_id,
        "selected_submission": selected["selected_submission"],
        "selected_submission_score": selected["selected_submission"].get("publicScore"),
        "episode_position": slot,
        "episode_id": int(episode["id"]),
        "episode_type": episode.get("type"),
        "episode_state": episode.get("state"),
        "episode_create_time": episode.get("createTime"),
        "episode_end_time": episode.get("endTime"),
        "seed": info.get("seed"),
        "engine_version": replay.get("module_version"),
        "source_seat": source_seat,
        "opponent_seat": opponent_seat,
        "opponent_team": names[opponent_seat],
        "opponent_action_sha256": sidecar_record["action_sha256_by_seat"][str(opponent_seat)],
        "opponent_actions_in_sidecar": sidecar_record["sidecar_path"],
        "team_actions_in_route": row.get("path"),
        "replay_path": str(archive.resolve()),
        "replay_sha256": raw_receipt["source_sha256"],
        "replay_archive_sha256": raw_receipt["archive_sha256"],
        "downloaded_at_utc": raw_receipt["downloaded_at_utc"],
        "source_statuses": statuses,
        "frames": len(steps),
        "public_state_path": sidecar_record["public_state_path"],
        "public_state_sha256": sidecar_record["public_state_sha256"],
        "public_state_index_path": sidecar_record["sidecar_path"],
        "public_state_index_sha256": sidecar_record["sidecar_sha256"],
        "market_fields": sidecar_record["market_fields"],
        "town_fields": sidecar_record["town_fields"],
        "runner_eligible": row.get("num_actions") == 719 and len(steps) == 720
                           and statuses == ["DONE", "DONE"],
    })
    return row


def leaderboard_snapshot() -> tuple[list[dict], dict]:
    snapshot_dir = HERE / "leaderboard_source"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    process = run(["competitions", "leaderboard", COMPETITION, "-d"], timeout=120,
                  output_dir=snapshot_dir)
    write_bytes(snapshot_dir / "leaderboard-cli.stdout.txt", process.stdout.encode("utf-8"))
    write_bytes(snapshot_dir / "leaderboard-cli.stderr.txt", process.stderr.encode("utf-8"))
    if process.returncode:
        raise RuntimeError(f"Leaderboard download failed (exit {process.returncode}): {process.stderr[:500]}")
    archives = sorted(snapshot_dir.glob("*.zip"))
    if len(archives) != 1:
        raise RuntimeError(f"Expected one leaderboard ZIP; found {len(archives)}")
    archive = archives[0]
    archive_bytes = archive.read_bytes()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
        members = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise RuntimeError(f"Expected one CSV in leaderboard ZIP; found {members}")
        csv_bytes = zf.read(members[0])
    write_bytes(snapshot_dir / "leaderboard.csv", csv_bytes)
    import csv
    board = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"))))
    eligible = []
    for item in board:
        try:
            rank = int(item["Rank"])
            if rank <= 100:
                eligible.append({
                    "rank": rank,
                    "teamId": int(item["TeamId"]),
                    "teamName": item["TeamName"],
                    "submissionDate": item.get("SubmissionDate"),
                    "score": float(item["Score"]),
                    "self_control": int(item["TeamId"]) == OUR_TEAM_ID,
                })
        except (KeyError, TypeError, ValueError):
            continue
    eligible.sort(key=lambda team: team["rank"])
    # Keep the official top 100 rows in leaderboard order, including any ties.
    teams = eligible[:100]
    if len(teams) != 100:
        raise RuntimeError(f"Expected 100 rank<=100 rows, received {len(teams)}")
    if len({row["teamId"] for row in teams}) != 100:
        raise RuntimeError("Leaderboard top 100 contains duplicate team IDs")
    write_json(HERE / "top100_teams.json", teams)
    meta = {
        "checked_at_utc": now(),
        "source": "Authenticated Kaggle competitions leaderboard download",
        "competition": COMPETITION,
        "requested_ranks": [1, 100],
        "leaderboard_archive_path": str(archive.resolve()),
        "leaderboard_archive_sha256": sha256(archive_bytes),
        "leaderboard_csv_path": str((snapshot_dir / "leaderboard.csv").resolve()),
        "leaderboard_csv_sha256": sha256(csv_bytes),
        "archive_member": members[0],
        "rows_in_csv": len(board),
        "top100_team_ids": [row["teamId"] for row in teams],
    }
    write_json(HERE / "snapshot.json", meta)
    return teams, meta


def fetch_team_selection(team: dict) -> dict:
    team_id = int(team["teamId"])
    stem = f"team-{team_id}"
    row = {"rank": int(team["rank"]), "team": team["teamName"], "team_id": team_id,
           "snapshot_score": team.get("score"), "checked_at_utc": now(), "episodes": [], "listing_errors": []}
    try:
        submissions, receipt = run_json(
            ["competitions", "team-submissions", str(team_id)],
            f"team submissions {team_id}", HERE / "api_raw" / f"{stem}-submissions.stdout.txt",
            HERE / "listings" / f"{stem}-submissions.json")
        row["submissions_listing"] = receipt
        if not isinstance(submissions, list):
            raise RuntimeError(f"Expected submission list for team {team_id}")
        scored = []
        for submission in submissions:
            try:
                score = float(submission.get("publicScore"))
                if score == score:
                    scored.append(submission)
            except (TypeError, ValueError):
                continue
        if not scored:
            row["unavailable"] = "No scored public submission in team listing"
            return row
        selected = max(scored, key=lambda submission: (float(submission["publicScore"]),
                                                        str(submission.get("dateSubmitted", ""))))
        submission_id = int(selected["id"])
        row["submission_id"] = submission_id
        row["selected_submission"] = selected
        row["selection_method"] = "Highest publicScore; latest dateSubmitted breaks ties"
        episodes, receipt = run_json(
            ["competitions", "episodes", str(submission_id)],
            f"submission episodes {submission_id}", HERE / "api_raw" / f"{stem}-submission-{submission_id}-episodes.stdout.txt",
            HERE / "listings" / f"{stem}-submission-{submission_id}-episodes.json")
        row["episodes_listing"] = receipt
        if not isinstance(episodes, list):
            raise RuntimeError(f"Expected episode list for submission {submission_id}")
        public = [episode for episode in episodes
                  if "PUBLIC" in str(episode.get("type", "")).upper()
                  and str(episode.get("state", "")).upper().endswith("COMPLETED")]
        public.sort(key=lambda episode: (str(episode.get("createTime", "")), int(episode["id"])), reverse=True)
        row["completed_public_episode_count"] = len(public)
        row["selected_episode_ids"] = [int(episode["id"]) for episode in public[:3]]
        for position in range(1, 4):
            if len(public) >= position:
                row["episodes"].append({"position": position, "episode": public[position - 1],
                                        "submission_id": submission_id,
                                        "selected_submission": selected})
            else:
                row["episodes"].append({"position": position, "unavailable": "Fewer than three completed public episodes"})
        return row
    except Exception as error:
        row["listing_errors"].append(f"{type(error).__name__}: {error}")
        row["unavailable"] = "Team listing retrieval failed"
        return row


def fetch_own_submission() -> dict:
    result = {"submission_id": CURRENT_SUBMISSION_ID, "team_id": OUR_TEAM_ID,
              "checked_at_utc": now(), "public_episode_slots": [], "download_errors": []}
    # Capture both account submissions and the author's team listing for the exact status.
    with ThreadPoolExecutor(max_workers=2) as pool:
        future_global = pool.submit(run_json,
            ["competitions", "submissions", COMPETITION, "--page-size", "200"],
            "competition submissions", HERE / "api_raw" / "competition-submissions.stdout.txt",
            HERE / "listings" / "competition-submissions.json")
        future_team = pool.submit(run_json,
            ["competitions", "team-submissions", str(OUR_TEAM_ID)],
            f"own team submissions {OUR_TEAM_ID}", HERE / "api_raw" / "own-team-submissions.stdout.txt",
            HERE / "listings" / "own-team-submissions.json")
        try:
            global_rows, global_receipt = future_global.result()
            own_rows, own_receipt = future_team.result()
        except Exception as error:
            result["listing_error"] = f"{type(error).__name__}: {error}"
            return result
    result["competition_submissions_receipt"] = global_receipt
    result["team_submissions_receipt"] = own_receipt
    global_match = [row for row in global_rows if int(row.get("ref", row.get("id", -1))) == CURRENT_SUBMISSION_ID]
    team_match = [row for row in own_rows if int(row.get("id", row.get("ref", -1))) == CURRENT_SUBMISSION_ID]
    result["submission_status"] = global_match[0] if global_match else None
    result["team_listing_submission"] = team_match[0] if team_match else None
    result["status_available"] = bool(global_match or team_match)
    try:
        episodes, receipt = run_json(
            ["competitions", "episodes", str(CURRENT_SUBMISSION_ID)],
            f"submission episodes {CURRENT_SUBMISSION_ID}", HERE / "api_raw" / f"submission-{CURRENT_SUBMISSION_ID}-episodes.stdout.txt",
            HERE / "listings" / f"submission-{CURRENT_SUBMISSION_ID}-episodes.json")
        result["episodes_listing"] = receipt
        result["all_episode_count"] = len(episodes)
        public = [episode for episode in episodes if "PUBLIC" in str(episode.get("type", "")).upper()]
        completed = [episode for episode in public if str(episode.get("state", "")).upper().endswith("COMPLETED")]
        completed.sort(key=lambda episode: (str(episode.get("createTime", "")), int(episode["id"])), reverse=True)
        result["public_episode_count"] = len(public)
        result["completed_public_episode_count"] = len(completed)
        result["public_episode_ids"] = [int(episode["id"]) for episode in completed]
        result["public_episode_slots"] = [{"position": i + 1, "episode": episode,
                                           "submission_id": CURRENT_SUBMISSION_ID}
                                          for i, episode in enumerate(completed)]
        result["noncompleted_public_episodes"] = [episode for episode in public if episode not in completed]
    except Exception as error:
        result["episodes_error"] = f"{type(error).__name__}: {error}"
    return result


def summarize_counts(manifest: dict) -> None:
    rows = manifest["rows"]
    for slot in (1, 2, 3):
        key = f"episode_{slot}"
        entries = [episode for row in rows for episode in row.get("episodes", [])
                   if episode.get("position") == slot and episode.get("route")]
        entries.sort(key=lambda entry: (int(entry["rank"]), int(entry["team_id"])))
        write_json(HERE / "routes" / f"episode_{slot}" / "summary.json", entries)
        if slot == 1:
            write_json(HERE / "routes" / "development_latest" / "summary.json", entries)
            write_json(HERE / "routes" / "development_top20" / "summary.json",
                       [entry for entry in entries if int(entry["rank"]) <= 20])
    manifest["latest_episode_routes"] = len([r for r in rows if r.get("episodes") and r["episodes"][0].get("route")])
    manifest["reserved_episode_2_routes"] = len([e for r in rows for e in r.get("episodes", [])
                                                 if e.get("position") == 2 and e.get("route")])
    manifest["reserved_episode_3_routes"] = len([e for r in rows for e in r.get("episodes", [])
                                                 if e.get("position") == 3 and e.get("route")])


def add_episode_record(row: dict, slot: dict, replay_data: tuple, sidecar_cache: dict) -> dict:
    episode = slot["episode"]
    episode_id = int(episode["id"])
    archive, raw, receipt, replay = replay_data
    if not isinstance(replay, dict):
        raise RuntimeError(f"Replay {episode_id} JSON root is {type(replay).__name__}, expected object")
    if episode_id not in sidecar_cache:
        sidecar_cache[episode_id] = build_sidecar(episode_id, replay, archive, receipt)
    route = make_team_route(row, slot, int(slot["position"]), replay, archive, receipt,
                            sidecar_cache[episode_id])
    return {"position": int(slot["position"]), "episode": episode,
            "submission_id": int(slot["submission_id"]), "episode_id": episode_id,
            "route": route, "download_status": "downloaded"}


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if (HERE / "manifest.json").exists():
        raise SystemExit(f"Refusing to overwrite existing collection: {HERE / 'manifest.json'}")
    for directory in ("api_raw", "listings", "raw_archive", "unpacked", "routes", "episode_index"):
        (HERE / directory).mkdir(parents=True, exist_ok=True)

    start = now()
    teams, snapshot = leaderboard_snapshot()
    own_submission = fetch_own_submission()
    write_json(HERE / "current_submission_56680167.json", own_submission)
    manifest = {
        "started_at_utc": start,
        "leaderboard_snapshot_utc": snapshot["checked_at_utc"],
        "leaderboard_snapshot": snapshot,
        "current_submission_id": CURRENT_SUBMISSION_ID,
        "current_submission_status": own_submission,
        "team_selection": "Top 100 rows from the fresh official leaderboard snapshot",
        "submission_selection": "For each team, highest numeric publicScore in team-submissions; latest dateSubmitted breaks ties",
        "episode_selection": "Three newest episodes whose listing type contains PUBLIC and state ends in COMPLETED; selection never reads reward or outcome",
        "replay_source": "Authenticated Kaggle competitions replay; original replay JSON is gzip-preserved with SHA-256",
        "route_schema": "refresh_top_leaderboard_routes._write_route; route summary rows include path, seed, rank, team_id, episode_id, submission_id, source_seat, action_sha256",
        "shop_demand_data": "Raw replay plus per-frame two-seat observation projections of town and market; explicit demand field captured if present, with exact market inventory/prices and unlocked shops",
        "expected_engine_version": EXPECTED_ENGINE,
        "complete": False,
        "rows": [],
        "errors": [],
    }
    write_json(HERE / "manifest.json", manifest)

    selections: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fetch_team_selection, team): team for team in teams}
        for future in as_completed(futures):
            team = futures[future]
            try:
                row = future.result()
            except Exception as error:
                row = {"rank": int(team["rank"]), "team": team["teamName"],
                       "team_id": int(team["teamId"]), "snapshot_score": team.get("score"),
                       "episodes": [], "listing_errors": [f"{type(error).__name__}: {error}"],
                       "unavailable": "Team listing retrieval failed"}
            selections[int(team["teamId"])] = row
            manifest["rows"] = sorted(selections.values(), key=lambda item: int(item["rank"]))
            manifest["listing_complete_teams"] = len(selections)
            write_json(HERE / "manifest.json", manifest)
            print(f"LISTED {len(selections)}/100 rank={row['rank']} team={row['team']}", flush=True)

    selected_episodes = []
    for team in teams:
        row = selections[int(team["teamId"])]
        for slot in row.get("episodes", []):
            if "episode" in slot:
                selected_episodes.append({"rank": row["rank"], "team_id": row["team_id"],
                                          "team": row["team"], "slot": slot})

    sidecar_cache: dict[int, dict] = {}
    download_cache: dict[int, tuple] = {}
    failures: dict[int, str] = {}
    duplicate_use_map: dict[int, list[dict]] = defaultdict(list)
    for item in selected_episodes:
        episode_id = int(item["slot"]["episode"]["id"])
        duplicate_use_map[episode_id].append({"rank": item["rank"], "team_id": item["team_id"],
                                               "team": item["team"], "episode_position": item["slot"]["position"]})

    # Development latest episodes first. This makes the 100-row route panel available
    # before we spend time on the two reserved episodes per team.
    latest_items = [item for item in selected_episodes if int(item["slot"]["position"]) == 1]
    unique_latest = sorted({int(item["slot"]["episode"]["id"]) for item in latest_items})
    latest_users: dict[int, list[dict]] = defaultdict(list)
    for item in latest_items:
        latest_users[int(item["slot"]["episode"]["id"])].append(item)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(download_episode, eid): eid for eid in unique_latest}
        done = 0
        for future in as_completed(futures):
            episode_id = futures[future]
            try:
                replay_data = future.result()
                download_cache[episode_id] = replay_data
                archive, raw, receipt, replay = replay_data
                if not isinstance(replay, dict):
                    raise RuntimeError("Replay JSON root is not an object")
                if episode_id not in sidecar_cache:
                    sidecar_cache[episode_id] = build_sidecar(episode_id, replay, archive, receipt)
                for item in latest_users[episode_id]:
                    team_row = selections[int(item["team_id"])]
                    slot = next(entry for entry in team_row["episodes"] if int(entry["position"]) == 1)
                    try:
                        slot["route"] = make_team_route(team_row, slot, 1, replay, archive, receipt,
                                                         sidecar_cache[episode_id])
                        slot["download_status"] = "downloaded"
                    except Exception as error:
                        slot["download_status"] = "unavailable"
                        slot["download_error"] = f"{type(error).__name__}: {error}"
            except Exception as error:
                failures[episode_id] = f"{type(error).__name__}: {error}"
                for item in latest_users[episode_id]:
                    team_row = selections[int(item["team_id"])]
                    slot = next(entry for entry in team_row["episodes"] if int(entry["position"]) == 1)
                    slot.update(download_status="unavailable", download_error=failures[episode_id])
            done += 1
            manifest["rows"] = sorted(selections.values(), key=lambda item: int(item["rank"]))
            manifest["latest_episode_downloads_complete"] = done
            summarize_counts(manifest)
            write_json(HERE / "manifest.json", manifest)
            top20_count = len(json.loads((HERE / "routes" / "development_top20" / "summary.json").read_text(encoding="utf-8")))
            print(f"LATEST {done}/{len(unique_latest)} unique episodes; usable team routes="
                  f"{manifest['latest_episode_routes']}; top20={top20_count}", flush=True)
            top20_expected = sum(1 for team in teams if int(team["rank"]) <= 20)
            ready_marker = HERE / "top20_ready.json"
            if top20_count == top20_expected and not ready_marker.exists():
                write_json(ready_marker, {"ready_at_utc": now(), "routes": top20_count,
                                          "summary_path": str((HERE / "routes" / "development_top20" / "summary.json").resolve()),
                                          "leaderboard_snapshot_utc": snapshot["checked_at_utc"]})
                print(f"TOP20_READY {ready_marker}", flush=True)

    # If top-20 is complete, notify the parent immediately so benchmarking can start.
    top20_summary = HERE / "routes" / "development_top20" / "summary.json"
    top20_entries = json.loads(top20_summary.read_text(encoding="utf-8")) if top20_summary.exists() else []
    top20_expected = sum(1 for team in teams if int(team["rank"]) <= 20)
    if len(top20_entries) == top20_expected:
        write_json(HERE / "top20_ready.json", {"ready_at_utc": now(), "routes": len(top20_entries),
                                                "summary_path": str(top20_summary.resolve()),
                                                "leaderboard_snapshot_utc": snapshot["checked_at_utc"]})
        print(f"TOP20_READY {top20_summary}", flush=True)

    # Download the second and third newest selections after the development set exists.
    reserved_items = [item for item in selected_episodes if int(item["slot"]["position"]) in (2, 3)]
    unique_reserved = sorted({int(item["slot"]["episode"]["id"]) for item in reserved_items}
                             - set(download_cache))
    reserved_users: dict[int, list[dict]] = defaultdict(list)
    for item in reserved_items:
        reserved_users[int(item["slot"]["episode"]["id"])].append(item)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(download_episode, eid): eid for eid in unique_reserved}
        done = 0
        for future in as_completed(futures):
            episode_id = futures[future]
            try:
                download_cache[episode_id] = future.result()
            except Exception as error:
                failures[episode_id] = f"{type(error).__name__}: {error}"
            done += 1
            for item in reserved_users[episode_id]:
                team_row = selections[int(item["team_id"])]
                slot = next(entry for entry in team_row["episodes"]
                            if int(entry["position"]) == int(item["slot"]["position"]))
                if episode_id in failures:
                    slot.update(download_status="unavailable", download_error=failures[episode_id])
                    continue
                try:
                    slot.update(add_episode_record(team_row, slot, download_cache[episode_id], sidecar_cache))
                except Exception as error:
                    slot.update(download_status="unavailable",
                                download_error=f"{type(error).__name__}: {error}")
            manifest["rows"] = sorted(selections.values(), key=lambda item: int(item["rank"]))
            manifest["reserved_episode_downloads_complete"] = done
            summarize_counts(manifest)
            write_json(HERE / "manifest.json", manifest)
            print(f"RESERVED {done}/{len(unique_reserved)} unique episodes", flush=True)

    # Download every completed public episode listed for the exact current upload.
    own_slots = own_submission.get("public_episode_slots", [])
    all_own_ids = sorted({int(slot["episode"]["id"]) for slot in own_slots if "episode" in slot})
    own_ids = sorted(set(all_own_ids) - set(download_cache))
    own_download_errors = []
    own_routes = []
    if own_ids:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(download_episode, eid): eid for eid in own_ids}
            for future in as_completed(futures):
                episode_id = futures[future]
                try:
                    download_cache[episode_id] = future.result()
                except Exception as error:
                    own_download_errors.append({"episode_id": episode_id,
                                                "error": f"{type(error).__name__}: {error}"})
                print(f"CURRENT_SUBMISSION_EPISODE {episode_id} downloaded={episode_id in download_cache}", flush=True)
    for slot in own_slots:
        episode = slot["episode"]
        episode_id = int(episode["id"])
        if episode_id not in download_cache:
            continue
        try:
            archive, raw, receipt, replay = download_cache[episode_id]
            if not isinstance(replay, dict):
                raise RuntimeError("Replay JSON root is not an object")
            if episode_id not in sidecar_cache:
                sidecar_cache[episode_id] = build_sidecar(episode_id, replay, archive, receipt)
            team_names = list((replay.get("info") or {}).get("TeamNames") or [])
            if team_names.count(OUR_TEAM_NAME) != 1:
                raise RuntimeError(f"Replay TeamNames does not contain {OUR_TEAM_NAME!r}: {team_names!r}")
            source_seat = team_names.index(OUR_TEAM_NAME)
            route_dir = HERE / "routes" / "current_submission_56680167"
            route_dir.mkdir(parents=True, exist_ok=True)
            route = _write_route(route_dir, OUR_TEAM_NAME, OUR_TEAM_ID, CURRENT_SUBMISSION_ID, episode, replay)
            actions = safe_actions(replay["steps"], source_seat)
            route.update({"episode_position": slot["position"],
                          "source_seat": source_seat, "opponent_seat": 1 - source_seat,
                          "opponent_team": team_names[1 - source_seat],
                          "team_id": OUR_TEAM_ID, "team": OUR_TEAM_NAME,
                          "rank": next((team["rank"] for team in teams if int(team["teamId"]) == OUR_TEAM_ID), None),
                          "seed": (replay.get("info") or {}).get("seed"),
                          "engine_version": replay.get("module_version"),
                          "replay_path": str(archive.resolve()),
                          "replay_sha256": receipt["source_sha256"],
                          "route_action_sha256": sha256(canonical_bytes(actions)),
                          "action_sha256": sha256(canonical_bytes(actions)),
                          "opponent_action_sha256": sidecar_cache[episode_id]["action_sha256_by_seat"][str(1 - source_seat)],
                          "public_state_path": sidecar_cache[episode_id]["public_state_path"],
                          "public_state_sha256": sidecar_cache[episode_id]["public_state_sha256"]})
            own_routes.append(route)
        except Exception as error:
            own_download_errors.append({"episode_id": episode_id,
                                        "error": f"{type(error).__name__}: {error}"})
    own_submission["downloaded_episode_ids"] = sorted(eid for eid in all_own_ids if eid in download_cache)
    own_submission["download_errors"] = own_download_errors
    own_submission["routes"] = sorted(own_routes, key=lambda row: (row.get("episode_position", 999), row["episode_id"]))
    write_json(HERE / "current_submission_56680167.json", own_submission)
    write_json(HERE / "routes" / "current_submission_56680167" / "summary.json", own_routes)

    # Record duplicate source episodes explicitly. They remain separate team/seat routes.
    duplicates = [{"episode_id": episode_id, "uses": uses}
                  for episode_id, uses in sorted(duplicate_use_map.items()) if len(uses) > 1]
    write_json(HERE / "duplicate_episodes.json", {
        "unique_selected_episode_ids": len(duplicate_use_map),
        "selected_episode_slots": len(selected_episodes),
        "duplicate_episode_id_count": len(duplicates),
        "duplicates": duplicates,
    })
    write_json(HERE / "collection_errors.json", {
        "episode_download_errors": [{"episode_id": eid, "error": message}
                                    for eid, message in sorted(failures.items())],
        "own_submission_download_errors": own_download_errors,
    })

    manifest["rows"] = sorted(selections.values(), key=lambda item: int(item["rank"]))
    manifest["current_submission_status"] = own_submission
    summarize_counts(manifest)
    manifest.update({
        "completed_at_utc": now(),
        "complete": len(manifest["rows"]) == 100 and all(
            all("episode" not in slot or slot.get("download_status") in ("downloaded", "unavailable")
                for slot in row.get("episodes", [])) for row in manifest["rows"]),
        "team_rows": len(manifest["rows"]),
        "selected_team_episode_slots": len(selected_episodes),
        "unique_team_episode_ids": len({int(item["slot"]["episode"]["id"]) for item in selected_episodes}),
        "duplicate_episode_id_count": len(duplicates),
        "replay_download_failures": len(failures),
        "current_submission_public_episode_download_errors": len(own_download_errors),
        "engine_versions_observed": sorted({
            str(episode["route"].get("engine_version"))
            for row in manifest["rows"] for episode in row.get("episodes", []) if episode.get("route")
        } | {str(route.get("engine_version")) for route in own_routes if route.get("engine_version")}),
    })
    write_json(HERE / "manifest.json", manifest)
    print("COMPLETE " + json.dumps({key: manifest.get(key) for key in (
        "complete", "team_rows", "latest_episode_routes", "reserved_episode_2_routes",
        "reserved_episode_3_routes", "unique_team_episode_ids", "duplicate_episode_id_count",
        "replay_download_failures", "current_submission_status", "engine_versions_observed")},
        ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
