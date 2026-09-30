"""Run both frozen opening arms on all 50 local entries; resume exact jobs."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
MANIFEST = ROOT / "diagnostics/loss_class_20260927/local_target_manifest_180951.json"
MANIFEST_SHA = "524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20"
MAIN_SHA = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game, engine_version


def sha(data):
    return hashlib.sha256(data).hexdigest()


def play(job):
    record, fixture, seat = job
    candidate = Path(record["path"])
    assert sha(candidate.read_bytes()) == record["sha256"]
    actions = json.loads(gzip.decompress(Path(fixture["source_action_tape_path"]).read_bytes()))["actions"]
    digests = [sha(json.dumps(actions, sort_keys=sort, separators=(",", ":")).encode())
               for sort in (False, True)]
    assert fixture["source_opponent_action_sha256"] in digests
    game = run_game(str(candidate), "rawroute:" + fixture["source_action_tape_path"],
                    int(fixture["seed"]), seat, False, 1, {})
    assert game["candidate_status"] == game["opponent_status"] == "DONE"
    assert game["frames"] == 720
    assert sha(candidate.read_bytes()) == record["sha256"]
    baseline = next(x for x in fixture["baseline_frozen_tape_both_seat_outcomes"] if x["seat"] == seat)
    return {"arm": record["arm"], "candidate_sha256": record["sha256"],
            "manifest_sha256": MANIFEST_SHA, "fixture_id": fixture["fixture_id"],
            "panel": "loss30" if fixture["fixture_id"].startswith("live-") else "top20",
            "team": fixture["team"], "baseline_result": baseline["result"],
            "baseline_margin": baseline["margin"],
            "margin_delta": game["margin"] - baseline["margin"], **game}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    assert engine_version == "1.32.7"
    assert sha(MANIFEST.read_bytes()) == MANIFEST_SHA
    assert sha((ROOT / "main.py").read_bytes()) == MAIN_SHA
    physical = json.loads((HERE / "physical.json").read_text(encoding="utf-8"))
    assert physical["physical_gate_pass"] and physical["common_step1_observations"]
    records = json.loads((HERE / "candidates.json").read_text())
    assert records == physical["candidate_hashes"]
    for record in records:
        assert sha(Path(record["path"]).read_bytes()) == record["sha256"]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    fixtures = manifest["live_losses"] + manifest["current_top20"]
    assert len(fixtures) == 50
    for fixture in fixtures:
        assert sha(gzip.decompress(Path(fixture["source_replay_path"]).read_bytes())) == fixture["source_replay_sha256"]
    jobs = [(r, f, seat) for f in fixtures for r in records for seat in (0, 1)]
    expected = {(r["arm"], f["fixture_id"], seat): r["sha256"] for r, f, seat in jobs}
    checkpoint = HERE / "arms.jsonl"
    results = []
    if checkpoint.exists():
        for line in checkpoint.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            key = (row["arm"], row["fixture_id"], row["candidate_seat"])
            assert row["candidate_sha256"] == expected[key] and row["manifest_sha256"] == MANIFEST_SHA
            results.append(row)
    keys = {(r["arm"], r["fixture_id"], r["candidate_seat"]) for r in results}
    assert len(keys) == len(results)
    pending = [job for job in jobs if (job[0]["arm"], job[1]["fixture_id"], job[2]) not in keys]
    print(f"Resuming {len(results)}/200 completed jobs; {len(pending)} pending", flush=True)
    with checkpoint.open("a", encoding="utf-8") as output, ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(play, job) for job in pending]
        for future in as_completed(futures):
            row = future.result()
            results.append(row)
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()
            if len(results) % 10 == 0 or row["team"] in ("DECEM", "Boey", "Vadim Vasilenko"):
                print(f"{len(results)}/200 {row['arm']} {row['team']} seat{row['candidate_seat']} "
                      f"{row['result']} {row['margin']:+.0f}", flush=True)
    assert len(results) == 200
    assert sha((ROOT / "main.py").read_bytes()) == MAIN_SHA
    for record in records:
        assert sha(Path(record["path"]).read_bytes()) == record["sha256"]
    results.sort(key=lambda r: (r["arm"], r["fixture_id"], r["candidate_seat"]))
    summaries = []
    for record in records:
        for panel in ("loss30", "top20"):
            rows = [r for r in results if r["arm"] == record["arm"] and r["panel"] == panel]
            by_fixture = {}
            for row in rows:
                by_fixture.setdefault(row["fixture_id"], []).append(row)
            summaries.append({"arm": record["arm"], "panel": panel,
                              "seat_wins": sum(r["result"] == "win" for r in rows),
                              "seat_draws": sum(r["result"] == "draw" for r in rows),
                              "seat_losses": sum(r["result"] == "loss" for r in rows),
                              "both_seat_wins": sum(all(r["result"] == "win" for r in pair) for pair in by_fixture.values()),
                              "lost_incumbent_win_seats": sum(r["baseline_result"] == "win" and r["result"] != "win" for r in rows),
                              "margin_delta": sum(r["margin_delta"] for r in rows)})
    common = {}
    same_captures = True
    for row in results:
        key = (row["fixture_id"], row["candidate_seat"])
        if key in common:
            same_captures = same_captures and common[key] == row["candidate_capture"]
        else:
            common[key] = row["candidate_capture"]
    payload = {"complete": True, "game_count": 200, "manifest_sha256": MANIFEST_SHA,
               "candidates": records, "same_step1_captures": same_captures,
               "summaries": summaries, "games": results,
               "interpretation": "Development against fixed action tapes; no reacting validation."}
    (HERE / "arms.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"summaries": summaries, "same_step1_captures": same_captures}, indent=2), flush=True)


if __name__ == "__main__":
    main()
