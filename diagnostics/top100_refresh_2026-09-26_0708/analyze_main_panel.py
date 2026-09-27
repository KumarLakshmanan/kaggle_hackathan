"""Summarize paired outcomes and day-six portfolio gaps on this fresh panel."""

import json
from collections import Counter
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
SUMMARY = HERE / "routes" / "summary.json"
RESULTS = HERE / "main_100routes.json"
OUTPUT = HERE / "main_panel_analysis.json"
LOSSES = HERE / "main_loss_manifest.json"


def load_leaderboard():
    raw = (HERE / "leaderboard_snapshot.json").read_text(encoding="utf-8-sig")
    start = min(i for i in (raw.find("["), raw.find("{")) if i >= 0)
    return {int(x["teamId"]): {**x, "rank": rank}
            for rank, x in enumerate(json.loads(raw[start:]), start=1)}


def band(rank):
    if rank <= 10:
        return "1-10"
    if rank <= 20:
        return "11-20"
    if rank <= 50:
        return "21-50"
    return "51-100"


def main():
    leaders = load_leaderboard()
    source = {str(Path(x["path"]).resolve()): x for x in json.loads(SUMMARY.read_text(encoding="utf8"))}
    result = json.loads(RESULTS.read_text(encoding="utf8"))
    assert result["unique_routes"] == 100
    rows = []
    for tested in result["rows"]:
        origin = source[str(Path(tested["opponent_path"]).resolve())]
        games = tested["games"]
        assert len(games) == 2
        assert {g["candidate_seat"] for g in games} == {0, 1}
        assert all(g["candidate_status"] == g["opponent_status"] == "DONE" for g in games)
        capture = games[0]["candidate_capture"]
        player = int(capture["player"])
        our_counts = capture["farms"][player]["counts"]
        rival_counts = capture["farms"][1 - player]["counts"]
        pair_margin = sum(g["margin"] for g in games)
        leader = leaders[int(origin["team_id"])]
        rows.append({
            "rank": int(leader["rank"]), "team": origin["team"],
            "team_id": origin["team_id"], "episode_id": origin["episode_id"],
            "seed": origin["seed"], "source_seat": origin["source_seat"],
            "action_sha256": origin["action_sha256"],
            "opponent_path": origin["path"],
            "shops_at_day6": capture["shops"],
            "our_day6_counts": our_counts, "rival_day6_counts": rival_counts,
            "paired_margin": pair_margin,
            "seat_margins": {str(g["candidate_seat"]): g["margin"] for g in games},
            "physical_mirror_turns": max(g["candidate_telemetry"].get("clone_gate_equal_turns", 0)
                                         for g in games),
        })
    assert len(rows) == 100 and len({x["team_id"] for x in rows}) == 100
    rows.sort(key=lambda x: x["rank"])
    losses = [x for x in rows if x["paired_margin"] < 0]
    bands = {}
    for name in ("1-10", "11-20", "21-50", "51-100"):
        group = [x for x in rows if band(x["rank"]) == name]
        bands[name] = {"routes": len(group),
                       "paired_wins": sum(x["paired_margin"] > 0 for x in group),
                       "paired_losses": sum(x["paired_margin"] < 0 for x in group)}
    strawberry_groups = {}
    for name, subset in (
        ("rival_at_most_4", [x for x in losses if x["rival_day6_counts"].get("STRAWBERRY", 0) <= 4]),
        ("rival_5_to_6", [x for x in losses if 5 <= x["rival_day6_counts"].get("STRAWBERRY", 0) <= 6]),
        ("rival_at_least_7", [x for x in losses if x["rival_day6_counts"].get("STRAWBERRY", 0) >= 7]),
    ):
        strawberry_groups[name] = {"losses": len(subset),
                                   "median_per_seat_loss": median([-x["paired_margin"] / 2 for x in subset]) if subset else None}
    analysis = {
        "candidate_sha256": result["candidate_sha256"],
        "engine_version": result["engine_version"],
        "routes": len(rows),
        "paired_wins": sum(x["paired_margin"] > 0 for x in rows),
        "paired_losses": len(losses),
        "paired_ties": sum(x["paired_margin"] == 0 for x in rows),
        "seat_wins": sum(m > 0 for x in rows for m in x["seat_margins"].values()),
        "seat_losses": sum(m < 0 for x in rows for m in x["seat_margins"].values()),
        "seat_ties": sum(m == 0 for x in rows for m in x["seat_margins"].values()),
        "rank_bands": bands,
        "loss_portfolios": strawberry_groups,
        "mirror_routes": sum(x["physical_mirror_turns"] > 0 for x in rows),
        "largest_losses": sorted(losses, key=lambda x: x["paired_margin"])[:10],
        "top10": rows[:10],
    }
    OUTPUT.write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    LOSSES.write_text(json.dumps(losses, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print(json.dumps({k: v for k, v in analysis.items() if k not in ("largest_losses", "top10")},
                     indent=2, ensure_ascii=False))
    print("largest_losses", [(x["rank"], x["team"], x["paired_margin"])
                             for x in analysis["largest_losses"]])
    print("top10", [(x["rank"], x["team"], x["paired_margin"]) for x in analysis["top10"]])


if __name__ == "__main__":
    main()
