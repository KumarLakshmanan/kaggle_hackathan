"""Run a candidate in both seats against each frozen live-loss reply tape.

These fixed-action fixtures measure tape regression only. The saved rival tape
does not react to the candidate, so results are not native-policy validation.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "local_target_manifest_180951.json"
DEFAULT_CANDIDATE = ROOT / "main.py"
EXPECTED_BASELINE = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"
sys.path.insert(0, str(ROOT))
from paired_benchmark import engine_version, run_game  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def actions_digest(actions: list) -> str:
    return sha(json.dumps(actions, separators=(",", ":")).encode("utf-8"))


def fixture_set_digest(entries: list[dict]) -> str:
    payload = [{key: entry[key] for key in (
        "fixture_id", "episode_id", "seed", "source_replay_sha256",
        "source_opponent_action_sha256")}
        for entry in sorted(entries, key=lambda row: int(row["episode_id"]))]
    return sha(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def play(job: tuple[dict, int, str, str]) -> dict:
    entry, seat, candidate_path, expected_hash = job
    candidate = Path(candidate_path)
    assert sha(candidate.read_bytes()) == expected_hash
    tape_path = Path(entry["source_action_tape_path"])
    tape = json.loads(gzip.decompress(tape_path.read_bytes()))["actions"]
    digest = actions_digest(tape)
    assert digest == entry["source_opponent_action_sha256"], entry["fixture_id"]
    game = run_game(str(candidate), "rawroute:" + str(tape_path),
                    int(entry["seed"]), int(seat), False, 144, {})
    assert game["candidate_status"] == game["opponent_status"] == "DONE"
    assert game["frames"] == 720
    return {
        "fixture_id": entry["fixture_id"],
        "episode_id": int(entry["episode_id"]),
        "team": entry["team"],
        "seed": int(entry["seed"]),
        "candidate_seat": int(seat),
        "opponent_action_sha256": digest,
        "candidate_reward": float(game["candidate_reward"]),
        "opponent_reward": float(game["opponent_reward"]),
        "margin": float(game["margin"]),
        "result": game["result"],
        "candidate_status": game["candidate_status"],
        "opponent_status": game["opponent_status"],
        "frames": int(game["frames"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--expected-sha256", default=EXPECTED_BASELINE)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=Path,
                        default=HERE / "live_loss_tape_baseline_180951.json")
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    candidate_hash = sha(candidate.read_bytes())
    assert candidate_hash == args.expected_sha256, (candidate_hash, args.expected_sha256)
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest["live_loss_count"] == 30
    jobs = [(entry, seat, str(candidate), candidate_hash)
            for entry in manifest["live_losses"] for seat in (0, 1)]
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(play, job) for job in jobs]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"{len(results)}/{len(jobs)} {result['fixture_id']} "
                  f"seat={result['candidate_seat']} {result['result']} "
                  f"margin={result['margin']:+.0f}", flush=True)
    results.sort(key=lambda row: (row["episode_id"], row["candidate_seat"]))
    assert len(results) == 60
    assert len({(row["episode_id"], row["candidate_seat"]) for row in results}) == 60
    assert all(row["candidate_status"] == row["opponent_status"] == "DONE"
               and row["frames"] == 720 for row in results)
    output = {
        "candidate_path": str(candidate),
        "candidate_sha256": candidate_hash,
        "fixture_manifest_path": str(MANIFEST.resolve()),
        "fixture_manifest_sha256": sha(manifest_bytes),
        "fixture_set_sha256": fixture_set_digest(manifest["live_losses"]),
        "engine_version": engine_version,
        "interpretation": "Fixed saved-opponent action tapes; diagnostic regression only, not reactive validation.",
        "complete": True,
        "game_count": len(results),
        "seat_wins": sum(row["result"] == "win" for row in results),
        "seat_draws": sum(row["result"] == "draw" for row in results),
        "seat_losses": sum(row["result"] == "loss" for row in results),
        "games": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()),
                      "games": output["game_count"],
                      "wins": output["seat_wins"], "draws": output["seat_draws"],
                      "losses": output["seat_losses"], "complete": output["complete"]},
                     indent=2), flush=True)


if __name__ == "__main__":
    main()
