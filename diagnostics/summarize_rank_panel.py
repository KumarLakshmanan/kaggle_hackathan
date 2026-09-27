"""Summarize fixed-action route benchmarks by a dated leaderboard snapshot.

This reports local replay wins, not predicted Kaggle ratings or live-agent wins.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--leaderboard", type=Path, required=True)
    args = parser.parse_args()

    source = json.loads(args.summary.read_text(encoding="utf-8"))
    benchmark = json.loads(args.results.read_text(encoding="utf-8"))
    leaders = json.loads(args.leaderboard.read_text(encoding="utf-8"))
    rank_by_team = {int(row["teamId"]): int(row["rank"]) for row in leaders}
    source_by_key = {
        (row["seed"], row["action_sha256"]): row for row in source
    }
    bands = {"1-10": Counter(), "11-25": Counter(),
             "26-50": Counter(), "51-100": Counter()}
    rank_rows = []
    for row in benchmark["rows"]:
        key = (row["seed"], row["action_sha256"])
        original = source_by_key[key]
        rank = rank_by_team[int(original["team_id"])]
        margins = [game["margin"] for game in row["games"]]
        band = ("1-10" if rank <= 10 else "11-25" if rank <= 25 else
                "26-50" if rank <= 50 else "51-100")
        result = "W" if all(m > 0 for m in margins) else "L" if all(m < 0 for m in margins) else "split"
        bands[band][result] += 1
        bands[band]["teams"] += 1
        rank_rows.append({"rank": rank, "team": row["team"],
                          "pair_margin": row["pair_margin"],
                          "seat_margins": margins, "result": result})
    rank_rows.sort(key=lambda row: row["rank"])
    outcomes = Counter(row["result"] for row in rank_rows)
    close_losses = [row for row in rank_rows
                    if row["result"] == "L" and row["pair_margin"] >= -2000]
    print(json.dumps({
        "route_count": len(rank_rows),
        "all_done": benchmark["summary"]["all_done"],
        "seat_results": benchmark["summary"]["game_results"],
        "route_results": dict(outcomes),
        "rank_bands": {name: dict(counter) for name, counter in bands.items()},
        "top_10": rank_rows[:10],
        "close_loss_count_under_1000_per_seat": len(close_losses),
        "close_losses": close_losses,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
