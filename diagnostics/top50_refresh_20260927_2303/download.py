"""Read-only download of latest valid public replays for a frozen top 50."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from refresh_top_leaderboard_routes import _run_json, _score, _write_route

KAGGLE = r"C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe"


def download(job):
    rank, team = job
    team_id, team_name = int(team["teamId"]), team["teamName"]
    submissions = _run_json(KAGGLE, ["competitions", "team-submissions", str(team_id)])
    public_submissions = [r for r in submissions if _score(r.get("publicScore")) > float("-inf")]
    if not public_submissions:
        raise RuntimeError(f"Rank {rank}: no public submissions")
    selected = max(public_submissions, key=lambda r: (_score(r.get("publicScore")), str(r.get("dateSubmitted", ""))))
    submission_id = int(selected["id"])
    episodes = _run_json(KAGGLE, ["competitions", "episodes", str(submission_id)])
    public = sorted([r for r in episodes if "PUBLIC" in str(r.get("type", "")) and str(r.get("state", "")).endswith("COMPLETED")],
                    key=lambda r: str(r.get("createTime", "")), reverse=True)
    incoming = HERE / "incoming" / f"rank-{rank:02d}"
    incoming.mkdir(parents=True, exist_ok=True)
    skipped = []
    for episode in public[:5]:
        eid = int(episode["id"])
        path = incoming / f"episode-{eid}-replay.json"
        if not path.is_file() or not path.stat().st_size:
            subprocess.run([KAGGLE, "competitions", "replay", str(eid), "-p", str(incoming), "-q"], check=True, capture_output=True)
        if not path.is_file() or not path.stat().st_size:
            skipped.append({"episode_id": eid, "reason": "replay not ready"})
            continue
        raw = path.read_bytes()
        replay = json.loads(raw)
        if replay.get("statuses") != ["DONE", "DONE"]:
            skipped.append({"episode_id": eid, "reason": "non-DONE status", "statuses": replay.get("statuses")})
            continue
        row = _write_route(HERE / "routes", team_name, team_id, submission_id, episode, replay)
        row.update({"leaderboard_rank": rank, "leaderboard_score": team["score"],
                    "source_submission_score": selected["publicScore"],
                    "replay_path": str(path.resolve()), "replay_sha256": hashlib.sha256(raw).hexdigest(),
                    "skipped_newer_episodes": skipped})
        return row
    raise RuntimeError(f"Rank {rank} {team_name}: no ready DONE/DONE public replay among latest five")


def main():
    sys.stdout.reconfigure(encoding="utf8", errors="replace")
    source = ROOT / "diagnostics/winrate_review_20260927/top50_latest_snapshot.json"
    text = source.read_text(encoding="utf-8-sig")
    start = min(i for i in (text.find("["), text.find("{")) if i >= 0)
    teams = json.loads(text[start:])
    assert len(teams) == 50 and len({r["teamId"] for r in teams}) == 50
    (HERE / "leaderboard_snapshot.json").write_text(json.dumps(teams, ensure_ascii=False, indent=2), encoding="utf8")
    (HERE / "routes").mkdir(parents=True, exist_ok=True)
    rows, errors = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download, (rank, team)): (rank, team) for rank, team in enumerate(teams, 1)}
        for future in as_completed(futures):
            rank, team = futures[future]
            try:
                row = future.result()
                rows.append(row)
                print(f"[{rank:02d}] {team['teamName']}: episode {row['episode_id']} ready", flush=True)
            except Exception as error:
                errors.append({"rank": rank, "team": team["teamName"], "error": str(error)})
                print(f"[{rank:02d}] failed: {error}", flush=True)
            (HERE / "download_partial.json").write_text(json.dumps({"rows": rows, "errors": errors}, ensure_ascii=False, indent=2), encoding="utf8")
    rows.sort(key=lambda r: r["leaderboard_rank"])
    (HERE / "routes/summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf8")
    result = {"completed_utc": datetime.now(timezone.utc).isoformat(), "requested_teams": 50,
              "downloaded_teams": len(rows), "unique_action_hashes": len({r["action_sha256"] for r in rows}),
              "unique_episodes": len({r["episode_id"] for r in rows}), "errors": errors}
    (HERE / "download_result.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(result, indent=2), flush=True)
    assert len(rows) == 50 and not errors, "Top-50 collection is incomplete"


if __name__ == "__main__":
    main()
