"""Verify and summarize the 17:23 UTC leaderboard tape assessment."""

from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / "diagnostics/current_top20_20260927_163500"
EXPECTED = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"


def load(path):
    return json.loads(path.read_text(encoding="utf8"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf8")


if __name__ == "__main__":
    snapshot = load(HERE / "snapshot.json")
    manifest = load(HERE / "manifest.json")
    assessment = load(HERE / "assessment.json")
    context = load(HERE / "source_context.json")
    previous = load(OLD / "manifest.json")
    assert manifest["complete"] and assessment["complete"] and context["complete"]
    assert assessment["candidate_sha256"] == EXPECTED
    assert hashlib.sha256((HERE / "candidate_frozen.py").read_bytes()).hexdigest() == EXPECTED
    entries = sorted(manifest["rows"], key=lambda r: r["rank"])
    assert len(entries) == 20 and [r["rank"] for r in entries] == list(range(1, 21))
    for row in entries:
        raw = gzip.decompress(Path(row["replay_path"]).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == row["replay_sha256"]
        route = load(Path(row["path"])) if row["path"].endswith(".json") else json.loads(gzip.decompress(Path(row["path"]).read_bytes()))
        action_hash = hashlib.sha256(json.dumps(route["actions"], sort_keys=True,
                                                separators=(",", ":")).encode()).hexdigest()
        assert action_hash == row["action_sha256"]
    games = assessment["games"]
    assert len(games) == 40
    assert all(g["candidate_status"] == g["opponent_status"] == "DONE"
               and g["frames"] == 720 for g in games)
    game_by = {(g["team_id"], g["candidate_seat"]): g for g in games}
    assert set(game_by) == {(r["team_id"], seat) for r in entries for seat in (0, 1)}
    shop_by = {r["team_id"]: r["states"]["144"]["shops"] for r in context["rows"]}
    divergent_shops = sorted({g["team_id"] for g in games
                             if g["candidate_capture"]["shops"] != shop_by[g["team_id"]]})
    per_team = []
    for row in entries:
        pair = [game_by[row["team_id"], seat] for seat in (0, 1)]
        per_team.append({"rank": row["rank"], "team": row["team"],
                         "team_id": row["team_id"], "episode_id": row["episode_id"],
                         "source_create_time": row["create_time"],
                         "source_seat": row["source_seat"], "submission_id": row["submission_id"],
                         "seat_results": [g["result"] for g in pair],
                         "seat_margins": [g["margin"] for g in pair],
                         "both_seat_sweep": all(g["result"] == "win" for g in pair)})
    old_ids = {r["episode_id"] for r in previous["rows"]}
    current_ids = {r["episode_id"] for r in entries}
    old_teams = {r["team_id"] for r in previous["rows"]}
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "leaderboard_snapshot_utc": snapshot["checked_at_utc"],
        "source_csv_sha256": snapshot["source_csv_sha256"],
        "candidate_sha256": EXPECTED,
        "all_source_replay_and_action_hashes_verified": True,
        "all_games_done_720": True,
        "teams": 20, "unique_source_episodes": len(current_ids),
        "source_episode_overlap_with_1635_panel": len(current_ids & old_ids),
        "new_team_ids_since_1635": sorted({r["team_id"] for r in entries} - old_teams),
        "oldest_source_create_time": min(r["create_time"] for r in entries),
        "newest_source_create_time": max(r["create_time"] for r in entries),
        "top10_both_seat_sweeps": sum(r["both_seat_sweep"] for r in per_team[:10]),
        "top20_both_seat_sweeps": sum(r["both_seat_sweep"] for r in per_team),
        "seat_wins": sum(g["result"] == "win" for g in games),
        "seat_losses": sum(g["result"] == "loss" for g in games),
        "seat_draws": sum(g["result"] == "draw" for g in games),
        "shop_divergence_at_144_team_count": len(divergent_shops),
        "shop_divergence_at_144_team_ids": divergent_shops,
        "per_team": per_team,
    }
    write(HERE / "summary.json", summary)
    lines = ["# Fresh top-20 recorded-action assessment — 27 September 2026", "",
             f"Official leaderboard snapshot: **{snapshot['checked_at_utc']}**.",
             f"The 20 latest completed source episodes were created from **{summary['oldest_source_create_time']}** "
             f"to **{summary['newest_source_create_time']}** UTC. All 20 raw replay and action hashes verify; "
             f"the {len(current_ids)} distinct episodes have **zero overlap** with the earlier 16:35 panel. "
             "Kaggledew Valley 🏆 entered the top 20 in place of My second life.", "",
             "Exact uploaded 4ee `main.py`, native engine 1.32.7, original shops, both seats: "
             f"**{summary['top20_both_seat_sweeps']}/20** both-seat sweeps and "
             f"**{summary['top10_both_seat_sweeps']}/10** top-ten sweeps. "
             "All 40 games are DONE/DONE/720 with no failed seats. "
             f"The native second-shop state differs from the source replay for "
             f"{len(divergent_shops)}/20 teams. Fixed opponent action tapes cannot "
             "establish results against their reacting private policies.", "",
             "| Rank | Team | Episode | Seat 0 margin | Seat 1 margin | Both seats won |",
             "|---:|---|---:|---:|---:|---|" ]
    for row in per_team:
        a, b = row["seat_margins"]
        lines.append(f'| {row["rank"]} | {row["team"].replace("|", "\\|")} | '
                     f'{row["episode_id"]} | {a:+,.0f} | {b:+,.0f} | '
                     f'{"yes" if row["both_seat_sweep"] else "no"} |')
    lines += ["", "Current losses in both seats are DECEM (rank 1), Boey (rank 3), "
              "and Vadim Vasilenko (rank 5). Majkel1337 is a win in this new "
              "source episode; it was a loss on the earlier, different episode. "
              "The changed sample is not evidence of a policy improvement.", "",
              "**Decision:** Accept the complete fresh assessment. The requested "
              "all-top-20 and top-10 goals remain unmet. No `main.py` change "
              "or Kaggle upload occurred.", "",
              "Evidence: `snapshot.json`, `manifest.json`, `routes/summary.json`, "
              "`assessment.json`, `source_context.json`, `summary.json`, "
              "`raw_archive/*`, and `PLAN.md`.", ""]
    (HERE / "RESULTS.md").write_text("\n".join(lines), encoding="utf8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("per_team", "shop_divergence_at_144_team_ids")},
                     ensure_ascii=True), flush=True)
