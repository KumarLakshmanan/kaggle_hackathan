from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


if __name__ == "__main__":
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf8"))
    result = json.loads((HERE / "assessment.json").read_text(encoding="utf8"))
    assert manifest["complete"] and result["complete"]
    sources = [r for r in manifest["rows"] if "action_sha256" in r]
    games = result["games"]
    assert len(games) == 2 * len(sources)
    context = json.loads((HERE / "source_context.json").read_text(encoding="utf8"))
    assert context["complete"]
    shops_by_team = {r["team_id"]: r["states"]["144"]["shops"] for r in context["rows"]}
    shop_difference_teams = sorted({g["team_id"] for g in games if g["candidate_capture"]["shops"] != shops_by_team[g["team_id"]]})
    prior = {r["team_id"]: r for r in json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))}
    repeats = [r for r in sources if prior.get(r["team_id"], {}).get("episode_id") == r["episode_id"]]
    errors = {}
    for game in games:
        for key, value in (game.get("candidate_telemetry") or {}).items():
            if key.endswith("errors") or key == "integration_gate_collisions":
                errors[key] = errors.get(key, 0) + int(value or 0)
    rows = []
    for source in sources:
        pair = sorted([g for g in games if g["team_id"] == source["team_id"]], key=lambda g: g["candidate_seat"])
        assert [g["candidate_seat"] for g in pair] == [0, 1]
        rows.append({"rank": source["rank"], "team": source["team"], "team_id": source["team_id"],
                     "source_episode_id": source["episode_id"], "source_time_utc": source["create_time"],
                     "margins": [g["margin"] for g in pair], "results": [g["result"] for g in pair],
                     "sweep": all(g["result"] == "win" for g in pair)})
    failed = [r for r in rows if not r["sweep"]]
    failed_ids = {r["team_id"] for r in failed}
    (HERE / "non_swept_routes.json").write_text(
        json.dumps([r for r in sources if r["team_id"] in failed_ids], indent=2, ensure_ascii=False), encoding="utf8")
    loss_context = [{"rank": g["rank"], "team": g["team"], "seed": g["seed"],
                     "seat": g["candidate_seat"], "margin": g["margin"],
                     "native_capture_144": g["candidate_capture"],
                     "source_shops_144": shops_by_team[g["team_id"]],
                     "telemetry": g.get("candidate_telemetry")}
                    for g in games if g["team_id"] in failed_ids]
    (HERE / "non_swept_context.json").write_text(json.dumps(loss_context, indent=2, ensure_ascii=False), encoding="utf8")
    group = result["groups"]["top100"]
    passed = group["teams_completed"] == group["both_seat_sweeps"] == 100 and group["seat_wins"] == 200 and group["all_done"]
    summary = {"candidate_sha256": result["candidate_sha256"], "leaderboard_snapshot_utc": manifest["leaderboard_snapshot_utc"],
               "groups": result["groups"], "downloaded_teams": len(sources), "unique_episodes": manifest["unique_episodes"],
               "oldest_replay_utc": min(r["create_time"] for r in sources),
               "newest_replay_utc": max(r["create_time"] for r in sources),
               "reused_yesterday_episodes": len(repeats), "error_counts": errors,
               "teams_with_shop_prefix_different_from_recording_at_144": len(shop_difference_teams),
               "all_top100_target_passed": passed, "non_swept_teams": failed,
               "candidate_max_action_ms": max(g["candidate_timing"]["max_ms"] for g in games),
               "completed_at_utc": result["completed_at_utc"]}
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf8")
    lines = ["# Fresh top-100 assessment — 27 September 2026", "",
             "## Result", "", f"Exact uploaded c68fa46f, submission **56602057**, wins **{group['both_seat_sweeps']}/100 matchups in both seats** and **{group['seat_wins']}/200 seats**.",
             f"Seat draws: {group['seat_draws']}; losses: {group['seat_losses']}. The all-top-100 target is {'passed on this recorded panel' if passed else 'not achieved'}.", "",
             "| Current leaderboard cohort | Teams covered | Both-seat sweeps | Seat wins | Draws | Losses |",
             "|---|---:|---:|---:|---:|---:|"]
    for limit in (10, 50, 100):
        g = result["groups"][f"top{limit}"]
        lines.append(f"| Top {limit} | {g['teams_completed']}/{limit} | {g['both_seat_sweeps']}/{limit} | {g['seat_wins']}/{2*limit} | {g['seat_draws']} | {g['seat_losses']} |")
    lines += ["", "## Freshness and method", "",
              f"Official leaderboard snapshot: **{manifest['leaderboard_snapshot_utc']}**. All {len(sources)} team sources were selected from fresh API queries and downloaded into this collection.",
              f"Source games were created between **{summary['oldest_replay_utc']} UTC** and **{summary['newest_replay_utc']} UTC**; {manifest['unique_episodes']} distinct episodes cover {len(sources)} teams.",
              f"Episodes reused from yesterday's 50-team panel: **{len(repeats)}**. No prior test outcomes were reused.", "",
              "For each snapshot team, select its higher-scoring active submission and latest complete public replay without filtering for wins. Run the exact uploaded file against each action tape in both seats, on its recorded seed, with original native shop generation. The candidate remained frozen throughout.", "",
              f"All games DONE/DONE with 720 frames: **{group['all_done']}**. Error telemetry: {json.dumps(errors, sort_keys=True)}.", "",
              "These opponents are recorded action tapes, not the teams' private reacting agents. They cannot respond to changed decisions or future shop differences. This result is a development benchmark, not a forecast of live rating or rank.", "",
              f"At turn 144, the native shop prefix differs from the source recording for **{len(shop_difference_teams)}/100 teams** in at least one seat. This follows from replaying fixed actions under changed farm states and original native shop generation; it limits conclusions about the live policies.", "",
              "## Matchups not won in both seats", "",
              "| Snapshot rank | Team | Seat 0 cash margin | Seat 1 cash margin |", "|---:|---|---:|---:|"]
    for row in failed:
        name = row["team"].replace("|", "\\|")
        lines.append(f"| {row['rank']} | {name} | {row['margins'][0]:+,.0f} | {row['margins'][1]:+,.0f} |")
    lines += ["", "## Decision and evidence", "",
              ("The exact recorded-panel completion criterion passes; live top 10 remains a separate requirement." if passed else "Reject the claim that c68 beats all current top-100 replays. Preserve this baseline and the losing cases for the next candidate; this assessment alone does not justify replacing or re-uploading main.py."), "",
              "- Frozen protocol: PLAN.md.", "- Fresh source selection and hashes: manifest.json and listings/.",
              "- All 200 game records: assessment.json.", "- Every team result and replay date: MATCHUPS.md.",
              "- Machine-readable summary: summary.json.", "- Exact uploaded root backup: main_uploaded_disjoint_integrated_20260927_c68fa46f.py."]
    lines += ["- Development-only losing subset and state captures: non_swept_routes.json and non_swept_context.json. Selecting these after outcomes does not make them validation data."]
    (HERE / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    lines = ["# All current top-100 matchups", "", "Snapshot: 2026-09-27 07:27:24 UTC. Candidate: c68fa46f. Positive margins are wins.", "",
             "| Rank | Team | Replay episode | Replay created UTC | Seat 0 margin | Seat 1 margin | Both seats won |", "|---:|---|---:|---|---:|---:|---|"]
    for row in rows:
        name = row["team"].replace("|", "\\|")
        lines.append(f"| {row['rank']} | {name} | {row['source_episode_id']} | {row['source_time_utc']} | {row['margins'][0]:+,.0f} | {row['margins'][1]:+,.0f} | {'Yes' if row['sweep'] else 'No'} |")
    (HERE / "MATCHUPS.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print(json.dumps({k: v for k, v in summary.items() if k != "non_swept_teams"}, indent=2))
