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

ERROR_KEYS = ("queue_errors", "quantity_errors", "mirror_quantity_errors", "farmice_errors",
              "integration_gate_collisions", "planned_funding_errors")


def play(job):
    candidate, digest, panel, entry, seat = job
    assert hashlib.sha256(Path(candidate).read_bytes()).hexdigest() == digest
    game = run_game(candidate, "rawroute:" + entry["path"], int(entry["seed"]), seat, False, 144, {})
    return {"panel": panel, "team": entry["team"], "team_id": entry["team_id"],
            "rank": entry.get("rank"), "episode_id": entry["episode_id"], **game}


def totals(games, expected):
    by_team = {}
    for game in games:
        by_team.setdefault(game["team_id"], []).append(game)
    return {"expected_teams": expected, "completed_teams": sum(len(pair) == 2 for pair in by_team.values()),
            "sweeps": sum(len(pair) == 2 and all(g["result"] == "win" for g in pair) for pair in by_team.values()),
            "seat_wins": sum(g["result"] == "win" for g in games),
            "seat_draws": sum(g["result"] == "draw" for g in games),
            "seat_losses": sum(g["result"] == "loss" for g in games)}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf8", errors="replace")
    manifest = json.loads((HERE / "build_manifest.json").read_text())
    pilot = json.loads((HERE / "screening.json").read_text())
    assert pilot["complete"] and pilot["passed"] and pilot["candidate_sha256"] == manifest["candidate_sha256"]
    assert not (HERE / "panels.json").exists(), "Inspect checkpoint instead of repeating games"
    paths = {"current100": ROOT / "diagnostics/current_top100_20260927_0730/routes/summary.json",
             "legacy50": ROOT / "diagnostics/top50_refresh_20260927_2303/routes/summary.json"}
    sources = {label: json.loads(path.read_text(encoding="utf8")) for label, path in paths.items()}
    assert len(sources["current100"]) == 100 and len(sources["legacy50"]) == 50
    jobs = [(manifest["candidate"], manifest["candidate_sha256"], label, entry, seat)
            for label, entries in sources.items() for entry in entries for seat in (0, 1)]
    development_path = HERE / "development.json"
    development = json.loads(development_path.read_text(encoding="utf8"))
    assert development["complete"] and development["passed"]
    assert development["candidate_sha256"] == manifest["candidate_sha256"]
    reused_games = [dict(g, panel="current100", provenance="development.json") for g in development["games"]]
    reused_keys = {(g["team_id"], g["candidate_seat"]) for g in reused_games}
    route_lookup = {r["team_id"]: r for r in sources["current100"]}
    assert len(reused_games) == len(reused_keys) == 46
    for g in reused_games:
        r = route_lookup[g["team_id"]]
        assert g["episode_id"] == r["episode_id"] and g["seed"] == r["seed"]
    jobs = [job for job in jobs if not (job[2] == "current100" and (job[3]["team_id"], job[4]) in reused_keys)]
    assert len(jobs) == 254
    output = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "candidate_sha256": manifest["candidate_sha256"],
              "engine_version": engine_version, "source_hashes": {label: hashlib.sha256(path.read_bytes()).hexdigest() for label, path in paths.items()},
              "complete": False, "games": reused_games, "reused_development_games": 46, "development_sha256": hashlib.sha256(development_path.read_bytes()).hexdigest()}

    def save():
        current = [g for g in output["games"] if g["panel"] == "current100"]
        legacy = [g for g in output["games"] if g["panel"] == "legacy50"]
        output["summary"] = {"current100": totals(current, 100),
                             "current50": totals([g for g in current if g["rank"] <= 50], 50),
                             "legacy50": totals(legacy, 50)}
        (HERE / "panels.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf8")

    save()
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(play, job) for job in jobs]):
            game = future.result()
            output["games"].append(game)
            output["games"].sort(key=lambda g: (g["panel"], g["team_id"], g["candidate_seat"]))
            save()
            print(f"{len(output['games'])}/300 {game['panel']} {game['team']} "
                  f"seat={game['candidate_seat']} {game['result']} {game['margin']:+.0f}", flush=True)
    all_done = all(g["candidate_status"] == g["opponent_status"] == "DONE" and g["frames"] == 720 for g in output["games"])
    errors = {key: sum(int((g.get("candidate_telemetry") or {}).get(key, 0)) for g in output["games"]) for key in ERROR_KEYS}
    current_old = json.loads((ROOT / "diagnostics/current_top100_20260927_0730/assessment.json").read_text(encoding="utf8"))
    legacy_old = json.loads((ROOT / "diagnostics/shunki_disjoint_integration_20260927/top50_reuse_proof.json").read_text(encoding="utf8"))
    assert current_old["candidate_sha256"] == legacy_old["candidate_sha256"] == "c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad"
    old = {("current100", g["team"], g["candidate_seat"]): g["margin"] for g in current_old["games"]}
    old.update({("legacy50", g["team"], g["seat"]): g["margin"] for g in legacy_old["branches"]})
    comparisons = []
    for panel, entries in sources.items():
        for entry in entries:
            pair = sorted([g for g in output["games"] if g["panel"] == panel and g["team_id"] == entry["team_id"]], key=lambda g: g["candidate_seat"])
            old_margins = [old[panel, entry["team"], seat] for seat in (0, 1)]
            margins = [g["margin"] for g in pair]
            comparisons.append({"panel": panel, "team": entry["team"], "rank": entry.get("rank"),
                                "old_margins": old_margins, "new_margins": margins,
                                "old_sweep": all(x > 0 for x in old_margins), "new_sweep": all(x > 0 for x in margins)})
    output.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat(), all_done=all_done,
                  errors=errors, comparisons=comparisons)
    s = output["summary"]
    output["passed"] = (s["current100"]["sweeps"] > 77 and s["current50"]["sweeps"] > 36
                        and s["legacy50"]["sweeps"] >= 44 and all_done and not any(errors.values()))
    save()
    print("RESULT " + json.dumps({k: output[k] for k in ("complete", "summary", "all_done", "errors", "passed")}), flush=True)
