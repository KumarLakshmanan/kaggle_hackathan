"""Build a rank-ordered table from two identical top-50 route panels."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ROUTES = HERE / "routes" / "summary.json"
MAIN = HERE / "main_50routes.json"
NEW = HERE / "new_50routes.json"
SNAPSHOT = HERE / "snapshot_meta.json"


def outcome(value: float) -> str:
    return "W" if value > 0 else "L" if value < 0 else "D"


def main() -> None:
    entries = json.loads(ROUTES.read_text(encoding="utf8"))
    main_panel = json.loads(MAIN.read_text(encoding="utf8"))
    new_panel = json.loads(NEW.read_text(encoding="utf8"))
    meta = json.loads(SNAPSHOT.read_text(encoding="utf8"))
    route_sha = hashlib.sha256(ROUTES.read_bytes()).hexdigest()
    for panel in (main_panel, new_panel):
        assert panel["summary_sha256"] == route_sha
        assert panel["unique_routes"] == len(entries) == 50
        assert panel["summary"]["all_done"]
    assert main_panel["candidate_sha256"] == (
        "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b")
    assert new_panel["candidate_sha256"] == (
        "1f22192297821ab5205b8cdcbd22bd1fab30d546860f3c61e8096a2a4355446b")
    main_by = {row["opponent_path"]: row for row in main_panel["rows"]}
    new_by = {row["opponent_path"]: row for row in new_panel["rows"]}
    assert set(main_by) == set(new_by)
    rows = []
    shop_parity = 0
    own_delta_total = 0.0
    rival_delta_total = 0.0
    for entry in sorted(entries, key=lambda row: row["rank"]):
        route = str(Path(entry["path"]).resolve())
        base, trial = main_by[route], new_by[route]
        assert (base["team"], base["seed"], base["action_sha256"], base["source_seat"]) == (
            trial["team"], trial["seed"], trial["action_sha256"], trial["source_seat"])
        base_games = {int(game["candidate_seat"]): game for game in base["games"]}
        trial_games = {int(game["candidate_seat"]): game for game in trial["games"]}
        assert set(base_games) == set(trial_games) == {0, 1}
        own_delta = sum(trial_games[seat]["candidate_reward"] - base_games[seat]["candidate_reward"]
                        for seat in (0, 1))
        rival_delta = sum(trial_games[seat]["opponent_reward"] - base_games[seat]["opponent_reward"]
                          for seat in (0, 1))
        own_delta_total += own_delta
        rival_delta_total += rival_delta
        shop_parity += sum(
            trial_games[seat]["candidate_capture"]["shops"][:2]
            == base_games[seat]["candidate_capture"]["shops"][:2]
            for seat in (0, 1))
        main_margin = float(base["pair_margin"])
        new_margin = float(trial["pair_margin"])
        rows.append({
            "rank": int(entry["rank"]), "team": entry["team"],
            "leaderboard_score": entry["leaderboard_score"],
            "episode_id": entry["episode_id"], "seed": entry["seed"],
            "source_seat": entry["source_seat"], "action_sha256": entry["action_sha256"],
            "main_paired_margin": main_margin, "new_paired_margin": new_margin,
            "margin_change": new_margin - main_margin,
            "main_outcome": outcome(main_margin), "new_outcome": outcome(new_margin),
            "own_cash_change": own_delta, "rival_cash_change": rival_delta,
        })
    summary = {
        "teams": 50, "games_per_agent": 100,
        "main_wins": sum(row["main_outcome"] == "W" for row in rows),
        "main_draws": sum(row["main_outcome"] == "D" for row in rows),
        "main_losses": sum(row["main_outcome"] == "L" for row in rows),
        "new_wins": sum(row["new_outcome"] == "W" for row in rows),
        "new_draws": sum(row["new_outcome"] == "D" for row in rows),
        "new_losses": sum(row["new_outcome"] == "L" for row in rows),
        "loss_to_win": sum(row["main_outcome"] == "L" and row["new_outcome"] == "W" for row in rows),
        "win_to_loss": sum(row["main_outcome"] == "W" and row["new_outcome"] == "L" for row in rows),
        "new_better_margin_routes": sum(row["margin_change"] > 0 for row in rows),
        "total_main_paired_margin": sum(row["main_paired_margin"] for row in rows),
        "total_new_paired_margin": sum(row["new_paired_margin"] for row in rows),
        "total_margin_change": sum(row["margin_change"] for row in rows),
        "total_own_cash_change": own_delta_total,
        "total_rival_cash_change": rival_delta_total,
        "same_first_two_shops_seats": shop_parity,
        "max_submission_score_gap": max(
            abs(float(entry["leaderboard_score"])
                - float(entry["selected_submission_score"])) for entry in entries),
        "median_submission_score_gap": statistics.median(
            abs(float(entry["leaderboard_score"])
                - float(entry["selected_submission_score"])) for entry in entries),
    }
    telemetry = [game.get("candidate_telemetry") or {}
                 for group in new_panel["rows"] for game in group["games"]]
    summary["repair_idle_weed_digs"] = sum(
        int(row.get("idle_weed_digs", 0)) for row in telemetry)
    summary["repair_blocked_work_digs"] = sum(
        int(row.get("blocked_work_digs", 0)) for row in telemetry)
    summary["repair_errors"] = sum(int(row.get("repair_errors", 0)) for row in telemetry)
    payload = {"snapshot": meta, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "main_sha256": main_panel["candidate_sha256"],
               "new_sha256": new_panel["candidate_sha256"],
               "engine_version": main_panel["engine_version"],
               "summary": summary, "rows": rows}
    (HERE / "comparison.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf8")
    with (HERE / "comparison.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Current Kaggriculture top-50 route comparison",
        "",
        f"Leaderboard snapshot: {meta['fetched_at_utc']}. Engine: {main_panel['engine_version']}.",
        "One completed public action history per displayed top-50 team, replayed on its",
        "original seed in both seats. Both files faced the same fixed opponent tape.",
        "The source submission for each team was the recent one whose public score",
        "was closest to the frozen leaderboard score. Ratings moved during collection:",
        f"median selection gap {summary['median_submission_score_gap']:.1f},",
        f"maximum {summary['max_submission_score_gap']:.1f} leaderboard points.",
        "The opponent does not react to our changed actions, and this is not a Kaggle rating.",
        "",
        f"`main.py` SHA-256 `{main_panel['candidate_sha256']}`;",
        f"new file SHA-256 `{new_panel['candidate_sha256']}`.",
        "",
        "## Summary",
        "",
        "| Measure | main.py | New Python file |",
        "| --- | ---: | ---: |",
        f"| Paired wins / 50 | {summary['main_wins']} | {summary['new_wins']} |",
        f"| Paired draws / 50 | {summary['main_draws']} | {summary['new_draws']} |",
        f"| Paired losses / 50 | {summary['main_losses']} | {summary['new_losses']} |",
        f"| Total paired coin margin | {summary['total_main_paired_margin']:+,.0f} | {summary['total_new_paired_margin']:+,.0f} |",
        "",
        f"The new file flips {summary['loss_to_win']} losses to wins and",
        f"{summary['win_to_loss']} wins to losses. Its total paired-margin change is",
        f"{summary['total_margin_change']:+,.0f} coins; own-cash change",
        f"{summary['total_own_cash_change']:+,.0f}, rival-cash change",
        f"{summary['total_rival_cash_change']:+,.0f}.",
        f"First-two shops matched between policies in {shop_parity}/100 seat comparisons.",
        f"The new file recorded {summary['repair_idle_weed_digs']} idle weed DIG repairs,",
        f"{summary['repair_blocked_work_digs']} blocked-work DIG repairs and",
        f"{summary['repair_errors']} repair errors across its 100 games.",
        "The aggregate gain cannot be assigned to those repairs without a same-route ablation.",
        "",
        "## Every top-50 team",
        "",
        "W/L/D use the sum of margins from the two seat-swapped games.",
        "A positive change favors the new file.",
        "",
        "| Rank | Team | LB score | main.py | New file | Margin change |",
        "| ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        team = str(row["team"]).replace("|", "\\|")
        lines.append(
            f"| {row['rank']} | {team} | {row['leaderboard_score']} | "
            f"{row['main_outcome']} {row['main_paired_margin']:+,.0f} | "
            f"{row['new_outcome']} {row['new_paired_margin']:+,.0f} | "
            f"{row['margin_change']:+,.0f} |")
    lines += ["", "## Evidence", "", "`leaderboard_snapshot.json`, `snapshot_meta.json`,",
              "`routes/summary.json`, `main_50routes.json`, `new_50routes.json`,",
              "`comparison.json`, and `comparison.csv` are the frozen evidence.",
              "Every one of the 200 games finished DONE/DONE.", ""]
    (HERE / "COMPARISON.md").write_text("\n".join(lines), encoding="utf8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
