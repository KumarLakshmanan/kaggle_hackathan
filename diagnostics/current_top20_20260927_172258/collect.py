from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from refresh_top_leaderboard_routes import _run_json, _write_route

KAGGLE = r"C:/Users/Veeramani Selvaraj/AppData/Roaming/Python/Python314/Scripts/kaggle.exe"
EXPECTED = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"
LOCK = threading.Lock()
EPISODE_LOCKS = {}


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf8")


def raw_episode(eid):
    with LOCK:
        lock = EPISODE_LOCKS.setdefault(eid, threading.Lock())
    with lock:
        archive = HERE / "raw_archive" / f"episode-{eid}-replay.json.gz"
        receipt = HERE / "raw_archive" / f"episode-{eid}-receipt.json"
        if archive.exists():
            raw = gzip.decompress(archive.read_bytes())
            saved = json.loads(receipt.read_text())
            assert hashlib.sha256(raw).hexdigest() == saved["sha256"]
            return archive, raw, saved
        unpacked = (HERE / "unpacked").resolve()
        temporary = unpacked / f"episode-{eid}-replay.json"
        assert temporary.parent == unpacked and not temporary.exists()
        result = subprocess.run(
            [KAGGLE, "competitions", "replay", str(eid), "-p", str(unpacked), "-q"],
            capture_output=True, text=True, encoding="utf8", errors="replace",
        )
        if result.returncode:
            raise RuntimeError(f"replay {eid} download returned {result.returncode}: {result.stderr[:300]}")
        raw = temporary.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        archive.write_bytes(gzip.compress(raw, compresslevel=6))
        assert hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest() == digest
        saved = {"episode_id": eid, "downloaded_at_utc": now(), "sha256": digest,
                 "source_bytes": len(raw), "archive_bytes": archive.stat().st_size}
        write(receipt, saved)
        temporary.unlink()
        return archive, raw, saved


def collect(team):
    tid = team["teamId"]
    base = {"rank": team["rank"], "team": team["teamName"], "team_id": tid,
            "snapshot_score": team["score"], "checked_at_utc": now(), "self_control": team.get("self_control",False), "attempts": []}
    try:
        submissions = _run_json(KAGGLE, ["competitions", "team-submissions", str(tid)])
        write(HERE / "listings" / f"team-{tid}-submissions.json", submissions)
        scored = [s for s in submissions if str(s.get("publicScore", "")).strip()]
        if not scored:
            return dict(base, unavailable="No active submission with public score")
        selected = max(scored, key=lambda s: (float(s["publicScore"]), s.get("dateSubmitted", "")))
        sid = int(selected["id"])
        base.update(submission_id=sid, selected_submission=selected)
        listing = _run_json(KAGGLE, ["competitions", "episodes", str(sid)])
        write(HERE / "listings" / f"team-{tid}-submission-{sid}-episodes.json", listing)
        choices = sorted(
            [e for e in listing if "PUBLIC" in str(e.get("type", ""))
             and str(e.get("state", "")).endswith("COMPLETED")],
            key=lambda e: (e["createTime"], int(e["id"])), reverse=True,
        )
        base["episode_listing_checked_at_utc"] = now()
        for episode in choices:
            eid = int(episode["id"])
            path, raw, downloaded = raw_episode(eid)
            replay = json.loads(raw)
            statuses = replay.get("statuses")
            if statuses != ["DONE", "DONE"] or len(replay.get("steps", [])) != 720:
                base["attempts"].append({"episode_id": eid, "reason": "Requires 720 DONE/DONE frames", "statuses": statuses})
                continue
            row = _write_route(HERE / "routes", team["teamName"], tid, sid, episode, replay)
            row.update(base)
            row.update(replay_path=str(path.resolve()), replay_sha256=downloaded["sha256"],
                       downloaded_at_utc=downloaded["downloaded_at_utc"], source_statuses=statuses,
                       episode_end_time=episode.get("endTime"), compressed=True)
            return row
        return dict(base, unavailable="No complete public DONE/DONE episode")
    except Exception as error:
        return dict(base, error=f"{type(error).__name__}: {error}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf8", errors="replace")
    assert hashlib.sha256((HERE / "candidate_frozen.py").read_bytes()).hexdigest() == EXPECTED
    assert not (HERE / "manifest.json").exists(), "Inspect existing collection before resuming"
    for directory in ("unpacked", "raw_archive", "routes", "listings"):
        (HERE / directory).mkdir(exist_ok=True)
    teams = json.loads((HERE / "top20_teams.json").read_text(encoding="utf8"))
    assert len(teams) == len({t["teamId"] for t in teams}) == 20
    manifest = {"started_at_utc": now(), "leaderboard_snapshot_utc": json.loads((HERE / "snapshot.json").read_text())["checked_at_utc"],
                "candidate_sha256": EXPECTED, "submission_id": 56609430,
                "selection": "Current top 20; higher-scored active submission; latest completed public DONE/DONE episode, no outcome filtering",
                "complete": False, "rows": []}
    write(HERE / "manifest.json", manifest)
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(collect, team) for team in teams]):
            row = future.result()
            manifest["rows"].append(row)
            manifest["rows"].sort(key=lambda r: r["rank"])
            write(HERE / "manifest.json", manifest)
            print(f"{len(manifest['rows'])}/20 rank={row['rank']} {row['team']} "
                  f"{row.get('error', row.get('unavailable', 'episode='+str(row.get('episode_id'))))}", flush=True)
    eligible = [r for r in manifest["rows"] if "action_sha256" in r]
    manifest.update(complete=True, completed_at_utc=now(), eligible=len(eligible),
                    unique_episodes=len({r["episode_id"] for r in eligible}))
    write(HERE / "manifest.json", manifest)
    write(HERE / "routes" / "summary.json", eligible)
    print(f"COMPLETE {len(eligible)}/20 teams; {manifest['unique_episodes']} distinct episodes", flush=True)
