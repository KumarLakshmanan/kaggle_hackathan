"""Small native feasibility pilot of complete static DECEM/Majkel action tapes."""

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

EXPECTED = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"
SEEDS = [2716200, 2716201, 2716202]
TEAMS = ("DECEM", "Majkel1337")


def play(job):
    entry, seed, seat = job
    assert hashlib.sha256((HERE / "candidate_frozen.py").read_bytes()).hexdigest() == EXPECTED
    game = run_game("rawroute:" + entry["path"], str(HERE / "candidate_frozen.py"),
                    seed, seat, False, 455, {})
    return {"team": entry["team"], "source_episode_id": entry["episode_id"],
            "source_seed": entry["seed"], "action_sha256": entry["action_sha256"], **game}


if __name__ == "__main__":
    assert not (HERE / "full_tape_pilot.json").exists()
    assert hashlib.sha256((HERE / "candidate_frozen.py").read_bytes()).hexdigest() == EXPECTED
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf8"))
    entries = [entry for entry in manifest["rows"] if entry["team"] in TEAMS]
    assert len(entries) == 2
    for entry in entries:
        route = json.loads(gzip.decompress(Path(entry["path"]).read_bytes()))
        digest = hashlib.sha256(json.dumps(route["actions"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert digest == entry["action_sha256"]
        assert len(route["actions"]) == 719
    result = {"started_at_utc": datetime.now(timezone.utc).isoformat(),
              "engine_version": engine_version, "opponent_sha256": EXPECTED,
              "seeds": SEEDS, "selection": "Whole static DECEM and Majkel action tapes; no policy code from opponents",
              "complete": False, "games": []}

    def save():
        (HERE / "full_tape_pilot.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf8")

    save()
    jobs = [(entry, seed, seat) for entry in entries for seed in SEEDS for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs]):
            game = future.result()
            result["games"].append(game)
            result["games"].sort(key=lambda g: (g["team"], g["seed"], g["candidate_seat"]))
            save()
            print(f"{len(result['games'])}/{len(jobs)} {game['team']} seed={game['seed']} "
                  f"seat={game['candidate_seat']} {game['result']} margin={game['margin']:+.0f} "
                  f"{game['candidate_status']}/{game['opponent_status']}", flush=True)
    result.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat())
    save()
