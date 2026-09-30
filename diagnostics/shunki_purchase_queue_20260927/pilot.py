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
    return run_game(candidate, str(OLD), seed, seat, False, 144, {})


if __name__ == "__main__":
    manifest = json.loads((HERE / "build_manifest.json").read_text())
    assert not (HERE / "pilot.json").exists(), "Inspect previous pilot rather than repeating results"
    seeds = list(range(2695000, 2695008))
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
                  f"purchase_turns={game['candidate_telemetry'].get('purchase_queue_turns')}", flush=True)
    games = output["games"]
    points = sum(1 if g["result"] == "win" else .5 if g["result"] == "draw" else 0 for g in games)
    active_pairs = sum(all(g["candidate_telemetry"]["purchase_queue_turns"] > 0
                           for g in games if g["seed"] == seed) for seed in seeds)
    all_done = all(g["candidate_status"] == g["opponent_status"] == "DONE" and g["frames"] == 720 for g in games)
    errors = {key: sum(int((g.get("candidate_telemetry") or {}).get(key, 0)) for g in games)
              for key in ("queue_errors", "quantity_errors", "mirror_quantity_errors", "farmice_errors",
                          "integration_gate_collisions", "purchase_queue_errors")}
    output.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat(), points=points,
                  active_pairs=active_pairs, all_done=all_done, errors=errors,
                  passed=points >= 12 and active_pairs >= 6 and all_done and not any(errors.values()))
    save()
    print("RESULT " + json.dumps({k: v for k, v in output.items() if k != "games"}), flush=True)
