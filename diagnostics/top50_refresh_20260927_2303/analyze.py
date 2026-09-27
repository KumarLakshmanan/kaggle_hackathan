"""Exact side-by-side comparison of every fresh top-50 replay opponent."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    sources = json.loads((HERE / "routes/summary.json").read_text(encoding="utf8"))
    original = json.loads((HERE / "incumbent_top50.json").read_text(encoding="utf8"))
    candidate = json.loads((HERE / "candidate_top50.json").read_text(encoding="utf8"))
    assert len(sources) == original["unique_routes"] == candidate["unique_routes"] == 50
    assert original["summary_sha256"] == candidate["summary_sha256"]
    old = {r["team"]: r for r in original["rows"]}
    new = {r["team"]: r for r in candidate["rows"]}
    rows = []
    for source in sources:
        a, b = old[source["team"]], new[source["team"]]
        assert a["action_sha256"] == b["action_sha256"] == source["action_sha256"]
        assert a["seed"] == b["seed"] == source["seed"]
        ga = sorted(a["games"], key=lambda r: r["candidate_seat"])
        gb = sorted(b["games"], key=lambda r: r["candidate_seat"])
        assert [r["candidate_seat"] for r in ga] == [r["candidate_seat"] for r in gb] == [0, 1]
        rows.append({"rank": source["leaderboard_rank"], "team": source["team"], "seed": source["seed"],
                     "episode_id": source["episode_id"], "route_path": source["path"],
                     "incumbent_seat_margins": [r["margin"] for r in ga],
                     "candidate_seat_margins": [r["margin"] for r in gb],
                     "incumbent_sweep": all(r["margin"] > 0 for r in ga),
                     "candidate_sweep": all(r["margin"] > 0 for r in gb),
                     "candidate_pair_margin": sum(r["margin"] for r in gb),
                     "candidate_shops": [r["candidate_capture"]["shops"] for r in gb],
                     "all_done": all(r["candidate_status"] == r["opponent_status"] == "DONE" for r in ga + gb)})
    rows.sort(key=lambda r: r["rank"])
    losses = [r for r in rows if not r["candidate_sweep"]]
    summary = {"teams": 50, "games_per_policy": 100,
               "incumbent_both_seat_wins": sum(r["incumbent_sweep"] for r in rows),
               "candidate_both_seat_wins": sum(r["candidate_sweep"] for r in rows),
               "incumbent_seat_wins": sum(m > 0 for r in rows for m in r["incumbent_seat_margins"]),
               "candidate_seat_wins": sum(m > 0 for r in rows for m in r["candidate_seat_margins"]),
               "flipped_losses_to_sweeps": sum(r["candidate_sweep"] and not r["incumbent_sweep"] for r in rows),
               "flipped_sweeps_to_losses": sum(r["incumbent_sweep"] and not r["candidate_sweep"] for r in rows),
               "all_done": all(r["all_done"] for r in rows), "local_50_target_complete": len(losses) == 0 and all(r["all_done"] for r in rows)}
    result = {"incumbent_sha256": original["candidate_sha256"], "candidate_sha256": candidate["candidate_sha256"],
              "panel_sha256": candidate["summary_sha256"], "summary": summary, "losses": losses, "rows": rows}
    (HERE / "comparison.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(summary, indent=2), flush=True)
    for row in losses:
        print(row["rank"], row["team"], row["candidate_seat_margins"], row["candidate_shops"][0], flush=True)


if __name__ == "__main__":
    main()
