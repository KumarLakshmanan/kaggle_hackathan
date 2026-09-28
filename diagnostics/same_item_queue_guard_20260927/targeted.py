"""Frozen five-opponent recorded-action development screen."""

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game, engine_version

CANDIDATE = HERE / "candidate.py"
CANDIDATE_SHA = "f8ba652449f657939272ce7946d22ddb757b56a5c017f62c035b6d6d024b873c"
MANIFEST = ROOT / "diagnostics/current_top20_20260927_163500/routes/summary.json"
SELECTED = {"DECEM", "Boey", "Vadim Vasilenko", "Majkel1337", "Yizhou"}
LOSSES = SELECTED - {"Yizhou"}


def play(job):
    entry, seat = job
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == CANDIDATE_SHA
    route = json.loads(gzip.decompress(Path(entry["path"]).read_bytes()))
    action_hash = hashlib.sha256(json.dumps(route["actions"], sort_keys=True,
                                            separators=(",", ":")).encode()).hexdigest()
    assert action_hash == entry["action_sha256"]
    game = run_game(str(CANDIDATE), "rawroute:" + entry["path"],
                    int(entry["seed"]), seat, False, 144, {})
    return {"team_id": entry["team_id"], "team": entry["team"],
            "rank": entry["rank"], "episode_id": entry["episode_id"], **game}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf8", errors="replace")
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == CANDIDATE_SHA
    assert not (HERE / "targeted.json").exists()
    entries = [e for e in json.loads(MANIFEST.read_text(encoding="utf8"))
               if e["team"] in SELECTED]
    assert {e["team"] for e in entries} == SELECTED and len(entries) == 5
    result = {"started_at_utc": datetime.now(timezone.utc).isoformat(),
              "candidate_sha256": CANDIDATE_SHA,
              "plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest(),
              "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
              "engine_version": engine_version, "complete": False, "games": []}

    def save():
        (HERE / "targeted.json").write_text(json.dumps(result, indent=2,
                                           ensure_ascii=False), encoding="utf8")

    save()
    jobs = [(entry, seat) for entry in entries for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs]):
            row = future.result()
            result["games"].append(row)
            result["games"].sort(key=lambda g: (g["rank"], g["candidate_seat"]))
            save()
            print(f'{len(result["games"])}/{len(jobs)} {row["team"]} '
                  f'seat={row["candidate_seat"]} {row["result"]} '
                  f'margin={row["margin"]:+.0f}', flush=True)
    games = result["games"]
    all_done = all(g["candidate_status"] == g["opponent_status"] == "DONE"
                   and g["frames"] == 720 for g in games)
    swept = {team for team in SELECTED if all(g["result"] == "win"
             for g in games if g["team"] == team)}
    assert len(games) == 10
    result.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat(),
                  all_done=all_done, swept=sorted(swept),
                  passed=all_done and "Yizhou" in swept and bool(LOSSES & swept))
    save()
    print("RESULT " + json.dumps({k: v for k, v in result.items() if k != "games"},
                                 ensure_ascii=False), flush=True)
