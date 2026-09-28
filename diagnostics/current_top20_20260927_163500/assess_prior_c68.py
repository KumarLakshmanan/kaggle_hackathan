from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game, engine_version

EXPECTED = "c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad"
CANDIDATE = ROOT / "main_uploaded_disjoint_integrated_20260927_c68fa46f.py"
OUTPUT = HERE / "assessment_prior_c68.json"


def play(job):
    entry, seat = job
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == EXPECTED
    route = json.loads(gzip.decompress(Path(entry['path']).read_bytes()))
    digest = hashlib.sha256(json.dumps(route['actions'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert digest == entry['action_sha256']
    game = run_game(str(CANDIDATE), "rawroute:" + entry["path"], int(entry["seed"]), seat, False, 144, {})
    return {"team_id": entry["team_id"], "team": entry["team"], "rank": entry["rank"],
            "episode_id": entry["episode_id"], "submission_id": entry["submission_id"], "self_control": entry.get("self_control",False), **game}


def statistics(entries, games, limit):
    selected = [e for e in entries if e["rank"] <= limit and not e.get('self_control')]
    played = [g for g in games if g["rank"] <= limit and not g.get('self_control')]
    pairs = [[g for g in played if g["team_id"] == e["team_id"]] for e in selected]
    own = sum(e["rank"] <= limit and e.get("self_control") for e in entries)
    return {"snapshot_rows": limit, "self_control_rows": own,
            "teams_requested": limit-own, "teams_downloaded": len(selected),
            "teams_completed": sum(len(pair) == 2 for pair in pairs),
            "both_seat_sweeps": sum(len(pair) == 2 and all(g["result"] == "win" for g in pair) for pair in pairs),
            "seat_wins": sum(g["result"] == "win" for g in played),
            "seat_draws": sum(g["result"] == "draw" for g in played),
            "seat_losses": sum(g["result"] == "loss" for g in played),
            "all_done": all(g["candidate_status"] == g["opponent_status"] == "DONE" and g["frames"] == 720 for g in played)}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf8", errors="replace")
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf8"))
    assert manifest["complete"]
    entries = json.loads((HERE / "routes/summary.json").read_text(encoding="utf8"))
    assert len({e["team_id"] for e in entries}) == len(entries)
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == EXPECTED
    assert not OUTPUT.exists(), "Inspect checkpoint before resuming"
    result = {"started_at_utc": datetime.now(timezone.utc).isoformat(),
              "leaderboard_snapshot_utc": manifest["leaderboard_snapshot_utc"],
              "candidate": str(CANDIDATE), "candidate_sha256": EXPECTED,
              "engine_version": engine_version, "complete": False, "games": [],
              "manifest_sha256": hashlib.sha256((HERE / "manifest.json").read_bytes()).hexdigest()}

    def save():
        result["groups"] = {f"top{n}": statistics(entries, result["games"], n) for n in (10, 20)}
        result['self_control'] = [g for g in result['games'] if g.get('self_control')]
        OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf8")

    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(play, (entry, seat)) for entry in entries for seat in (0, 1)]
        for future in as_completed(futures):
            game = future.result()
            result["games"].append(game)
            result["games"].sort(key=lambda g: (g["rank"], g["candidate_seat"]))
            save()
            print(f"{len(result['games'])}/{len(futures)} rank={game['rank']} {game['team']} "
                  f"seat={game['candidate_seat']} {game['result']} margin={game['margin']:+.0f} "
                  f"{game['candidate_status']}/{game['opponent_status']}", flush=True)
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == EXPECTED
    result.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat())
    save()
    print("COMPLETE " + json.dumps(result["groups"], ensure_ascii=False), flush=True)
