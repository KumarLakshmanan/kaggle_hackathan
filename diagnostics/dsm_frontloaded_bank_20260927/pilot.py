from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game, engine_version

OLD = ROOT / "main_uploaded_disjoint_integrated_20260927_c68fa46f.py"


def play(job):
    candidate, expected, seed, seat = job
    assert hashlib.sha256(Path(candidate).read_bytes()).hexdigest() == expected
    assert hashlib.sha256(OLD.read_bytes()).hexdigest() == "c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad"
    return run_game(candidate, str(OLD), seed, seat, False, 72, {})


if __name__ == "__main__":
    manifest = json.loads((HERE / "build_manifest.json").read_text())
    assert not (HERE / "pilot.json").exists(), "Inspect previous pilot rather than replaying results"
    seeds = list(range(2693100, 2693108))
    jobs = [(manifest["candidate"], manifest["candidate_sha256"], seed, seat) for seed in seeds for seat in (0, 1)]
    output = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "candidate_sha256": manifest["candidate_sha256"],
              "engine_version": engine_version, "seeds": seeds, "complete": False, "games": []}

    def save():
        (HERE / "pilot.json").write_text(json.dumps(output, indent=2), encoding="utf8")

    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs]):
            game = future.result()
            output["games"].append(game)
            output["games"].sort(key=lambda g: (g["seed"], g["candidate_seat"]))
            save()
            print(f"{len(output['games'])}/16 seed={game['seed']} seat={game['candidate_seat']} "
                  f"{game['result']} margin={game['margin']:+.0f} "
                  f"{game['candidate_status']}/{game['opponent_status']} "
                  f"{json.dumps(game['candidate_telemetry'])}", flush=True)
    games = output["games"]
    points = sum(1 if g["result"] == "win" else .5 if g["result"] == "draw" else 0 for g in games)
    both = lambda seed, field: all((g.get("candidate_telemetry") or {}).get(field) for g in games if g["seed"] == seed)
    opening_pairs = sum(both(seed, "statebank_opening_match") for seed in seeds)
    switched_pairs = sum(both(seed, "statebank_switches") for seed in seeds)
    all_done = all(g["candidate_status"] == g["opponent_status"] == "DONE" and g["frames"] == 720 for g in games)
    errors = sum(g["candidate_telemetry"]["statebank_errors"] for g in games)
    output.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat(), points=points,
                  opening_pairs=opening_pairs, switched_pairs=switched_pairs, all_done=all_done, errors=errors,
                  passed=points >= 12 and opening_pairs >= 6 and switched_pairs >= 6 and all_done and errors == 0)
    save()
    print("RESULT " + json.dumps({k: v for k, v in output.items() if k != "games"}), flush=True)
