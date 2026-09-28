"""Frozen five-fixture screen of saved alternative agents against action tapes."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
TOP_DIR = ROOT / "diagnostics/current_top20_20260927_172258"
TOP_MANIFEST = TOP_DIR / "manifest.json"
TOP_ASSESSMENT = TOP_DIR / "assessment.json"
BASELINE = ROOT / "main.py"
EXPECTED_MAIN = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"
EXPECTED_TOP_MANIFEST = "4cf340e5ac28eec35dc202a459c3910cee8da1c692324b41ebd3f619f70230ea"
EXPECTED_TOP_ASSESSMENT = "9d328af8115e27acb45fd4251a1bbc1fde5fda8c793c027b46792a54c04cbeb7"
EXPECTED_ENGINE = "1.32.7"
FIXTURES = {
    "DECEM": (1, 114267880, 1390733823,
              "a326e4f9e779ce21762e8cac5a0058884a1676271f296bf4c2291180b0175226",
              "1d6a1d7ce66a2e07bd1576528e930ac5f13777fdb88f673eea3aa0a4c34c8072", "target"),
    "DSM": (2, 114267880, 1390733823,
            "f3ef1eb69b43dcb3051235fedbc71b331966972cc92d17f8b877acfd1066bc30",
            "1d6a1d7ce66a2e07bd1576528e930ac5f13777fdb88f673eea3aa0a4c34c8072", "control"),
    "Boey": (3, 114266440, 1042173125,
             "62fff0dbd859fe5cb99d2fff2a126731f740f3345f4d1b7e8c1e3fab43d81c97",
             "2780737421202cc6d8d5c322de491b6430e4699168f65063229f87dd8934a385", "target"),
    "Vadim Vasilenko": (5, 114265033, 931842424,
                        "d7a9a8d5e3b6feab6b21a09796f70972668a1a9d1fc9ba4ae316479efaf8a741",
                        "55c62652e267c2b2df114df06e479bda051feda41f7abc8a6fe6cd2327dace10", "target"),
    "Majkel1337": (6, 114263239, 1525050266,
                   "35753ab4044c3192ef625f780d76a41a6ffe4d4f2658084f64bdfc1289df2282",
                   "e70478604a64682af14cae0a5110f7bf3b970536465f1ccdbeb863c4885e6e6d", "control"),
}
CANDIDATES = [
    {"name": "v43_decoded", "path": "main_v43_current.py",
     "sha256": "69f06a802b62aa08f28705dab5728eb924bb6a7c23ffe0164f65b104cc3dadf3"},
    {"name": "v48_full", "path": "diagnostics/public_kaito_v48_20260926/full_policy_local_screen.py",
     "sha256": "dadee25a9840313218384208c53b2c4752f82c3209cc654632e0b96c65e2664a"},
    {"name": "search_v2", "path": "kaggriculture_search_agent_v2_20260926.py",
     "sha256": "5e4023df7b78d62e86df068c4ae54c7c95b2d29a0908be680b3332a3019fa6da"},
]
ITEMS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "GOOSE", "COW", "SHEEP")
sys.path.insert(0, str(ROOT))
from paired_benchmark import engine_version, run_game  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def action_digest(actions: list) -> str:
    data = json.dumps(actions, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha(data)


def load_and_check_fixtures() -> list[dict]:
    assert sha(TOP_MANIFEST.read_bytes()) == EXPECTED_TOP_MANIFEST
    assert sha(TOP_ASSESSMENT.read_bytes()) == EXPECTED_TOP_ASSESSMENT
    manifest = json.loads(TOP_MANIFEST.read_text(encoding="utf-8"))
    assessment = json.loads(TOP_ASSESSMENT.read_text(encoding="utf-8"))
    assert manifest["candidate_sha256"] == EXPECTED_MAIN
    assert assessment["candidate_sha256"] == EXPECTED_MAIN
    by_team = {row["team"]: row for row in manifest["rows"]}
    baseline_by_key: dict[tuple[str, int], list[dict]] = {}
    for row in assessment["games"]:
        baseline_by_key.setdefault((row["team"], int(row["episode_id"])), []).append(row)
    fixtures = []
    for team, (rank, episode, seed, expected_action, expected_replay, role) in FIXTURES.items():
        row = by_team[team]
        assert int(row["rank"]) == rank and int(row["episode_id"]) == episode
        assert int(row["seed"]) == seed and row["action_sha256"] == expected_action
        assert row["replay_sha256"] == expected_replay
        route = Path(row["path"])
        tape = json.loads(gzip.decompress(route.read_bytes()))["actions"]
        assert len(tape) == 719 and action_digest(tape) == expected_action
        replay_path = Path(row["replay_path"])
        replay_raw = gzip.decompress(replay_path.read_bytes())
        assert sha(replay_raw) == expected_replay
        replay = json.loads(replay_raw)
        assert replay["module_version"] == EXPECTED_ENGINE
        baseline_rows = sorted(baseline_by_key[(team, episode)], key=lambda item: item["candidate_seat"])
        assert [item["candidate_seat"] for item in baseline_rows] == [0, 1]
        assert all(item["candidate_status"] == item["opponent_status"] == "DONE"
                   and item["frames"] == 720 for item in baseline_rows)
        want = "loss" if role == "target" else "win"
        assert all(item["result"] == want for item in baseline_rows)
        fixtures.append({
            "team": team, "role": role, "rank": rank, "episode_id": episode,
            "seed": seed, "source_seat": int(row["source_seat"]),
            "action_sha256": expected_action, "replay_sha256": expected_replay,
            "route_path": str(route.resolve()), "replay_path": str(replay_path.resolve()),
            "baseline_both_seat_outcomes": [{
                "seat": int(item["candidate_seat"]), "result": item["result"],
                "margin": float(item["margin"]),
            } for item in baseline_rows],
        })
    return fixtures


def play(job: tuple[dict, dict]) -> dict:
    candidate, fixture = job
    path = (ROOT / candidate["path"]).resolve()
    assert sha(path.read_bytes()) == candidate["sha256"], candidate["name"]
    rows = []
    for seat in (0, 1):
        game = run_game(str(path), "rawroute:" + fixture["route_path"],
                        int(fixture["seed"]), seat, False, 48, {})
        rows.append({
            "candidate_seat": seat,
            "candidate_reward": float(game["candidate_reward"]),
            "opponent_reward": float(game["opponent_reward"]),
            "margin": float(game["margin"]), "result": game["result"],
            "candidate_status": game["candidate_status"],
            "opponent_status": game["opponent_status"],
            "frames": int(game["frames"]),
            "candidate_capture_step48": game["candidate_capture"],
        })
        assert game["candidate_status"] == game["opponent_status"] == "DONE"
        assert game["frames"] == 720
        assert sha(path.read_bytes()) == candidate["sha256"], candidate["name"]
    return {"candidate": candidate["name"], "fixture": fixture, "seats": rows}


def trigger_key(capture: dict, seat: int) -> dict:
    farm = capture["farms"][seat]
    shed = capture.get("private_shed", {})
    return {
        "first_two_shops": list(capture.get("shops", []))[:2],
        "own_hands": int(farm["hands"]),
        "own_land": int(farm["land"]),
        "own_cash_bucket_5000": math.floor(float(farm["money"]) / 5000),
        "own_asset_counts": {item: int(farm["counts"].get(item, 0)) for item in ITEMS},
        "own_shed_counts": {item: int(shed.get(item, 0)) for item in ITEMS},
    }


def analyze_candidate(candidate_name: str, fixtures: list[dict], results: list[dict]) -> dict:
    candidate_rows = [row for row in results if row["candidate"] == candidate_name]
    targets = [row for row in candidate_rows if row["fixture"]["role"] == "target"]
    controls = [row for row in candidate_rows if row["fixture"]["role"] == "control"]
    flips = []
    for row in targets:
        for seat in row["seats"]:
            if seat["result"] == "win":
                flips.append({
                    "team": row["fixture"]["team"], "episode_id": row["fixture"]["episode_id"],
                    "seat": seat["candidate_seat"], "margin": seat["margin"],
                    "trigger_key": trigger_key(seat["candidate_capture_step48"], seat["candidate_seat"]),
                })
    control_regressions = [{
        "team": row["fixture"]["team"], "episode_id": row["fixture"]["episode_id"],
        "seat": seat["candidate_seat"], "margin": seat["margin"], "result": seat["result"],
        "trigger_key": trigger_key(seat["candidate_capture_step48"], seat["candidate_seat"]),
    } for row in controls for seat in row["seats"] if seat["result"] != "win"]
    key_json = {json.dumps(item["trigger_key"], sort_keys=True, separators=(",", ":"))
                for item in flips}
    matched_controls = [{
        "team": row["fixture"]["team"], "episode_id": row["fixture"]["episode_id"],
        "seat": seat["candidate_seat"], "result": seat["result"], "margin": seat["margin"],
    } for row in controls for seat in row["seats"]
       if json.dumps(trigger_key(seat["candidate_capture_step48"], seat["candidate_seat"]),
                     sort_keys=True, separators=(",", ":")) in key_json]
    target_sweeps = sum(all(seat["result"] == "win" for seat in row["seats"]) for row in targets)
    control_sweeps = sum(all(seat["result"] == "win" for seat in row["seats"]) for row in controls)
    return {
        "candidate": candidate_name,
        "target_flip_seats": len(flips), "target_flips": flips,
        "target_both_seat_sweeps": target_sweeps,
        "control_regression_seats": len(control_regressions),
        "control_regressions": control_regressions,
        "control_both_seat_sweeps": control_sweeps,
        "trigger_audit": {
            "performed": bool(flips),
            "definition": "first two shops + step-48 hands/land/cash bucket/asset and shed counts",
            "unique_target_flip_keys": len(key_json),
            "matching_control_seats": matched_controls,
            "no_control_harm_on_observed_keys": bool(flips) and not any(
                row["result"] != "win" for row in matched_controls),
            "interpretation": "Descriptive five-fixture signature check only; no promotion evidence.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=Path, default=HERE / "screen.json")
    args = parser.parse_args()
    assert engine_version == EXPECTED_ENGINE, engine_version
    assert sha(BASELINE.read_bytes()) == EXPECTED_MAIN
    for candidate in CANDIDATES:
        path = ROOT / candidate["path"]
        assert sha(path.read_bytes()) == candidate["sha256"], candidate["name"]
    fixtures = load_and_check_fixtures()
    jobs = [(candidate, fixture) for candidate in CANDIDATES for fixture in fixtures]
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            seat_summary = "/".join(
                f"{seat['result']}({seat['margin']:+.0f})" for seat in result["seats"])
            print(f"{len(results)}/{len(jobs)} {result['candidate']} "
                  f"{result['fixture']['team']} {seat_summary}", flush=True)
    results.sort(key=lambda row: (row["candidate"], row["fixture"]["rank"]))
    assert len(results) == 15
    assert sha(BASELINE.read_bytes()) == EXPECTED_MAIN
    for candidate in CANDIDATES:
        assert sha((ROOT / candidate["path"]).read_bytes()) == candidate["sha256"]
    summaries = [analyze_candidate(candidate["name"], fixtures, results)
                 for candidate in CANDIDATES]
    payload = {
        "complete": True, "engine_version": engine_version,
        "candidate_baseline_sha256": EXPECTED_MAIN,
        "top20_manifest_sha256": EXPECTED_TOP_MANIFEST,
        "top20_assessment_sha256": EXPECTED_TOP_ASSESSMENT,
        "interpretation": "Fixed saved-action-tape diagnostic only; opponents do not react.",
        "candidate_file_hashes": CANDIDATES,
        "fixtures": fixtures, "candidate_fixture_results": results,
        "candidate_summaries": summaries,
        "game_count": sum(len(row["seats"]) for row in results),
        "all_done_720": all(seat["candidate_status"] == seat["opponent_status"] == "DONE"
                             and seat["frames"] == 720
                             for row in results for seat in row["seats"]),
        "baseline_hash_verified_after": sha(BASELINE.read_bytes()) == EXPECTED_MAIN,
        "candidate_hashes_verified_after": all(
            sha((ROOT / row["path"]).read_bytes()) == row["sha256"] for row in CANDIDATES),
    }
    assert payload["game_count"] == 30 and payload["all_done_720"]
    assert payload["baseline_hash_verified_after"] and payload["candidate_hashes_verified_after"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(args.output.resolve()), "games": payload["game_count"],
                      "all_done_720": payload["all_done_720"],
                      "summaries": [{"candidate": row["candidate"],
                                     "target_flip_seats": row["target_flip_seats"],
                                     "control_regression_seats": row["control_regression_seats"]}
                                    for row in summaries]}, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
