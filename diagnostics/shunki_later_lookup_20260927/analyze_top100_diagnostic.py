"""Join exact saved top-100 candidate and incumbent route outcomes."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PANEL = ROOT / "diagnostics" / "top100_refresh_2026-09-26_0708"
BASE = PANEL / "main_100routes.json"
TRIAL = HERE / "top100_diagnostic.json"


def leaderboard() -> dict[int, int]:
    raw = (PANEL / "leaderboard_snapshot.json").read_text(encoding="utf-8-sig")
    start = min(i for i in (raw.find("["), raw.find("{")) if i >= 0)
    return {int(row["teamId"]): rank
            for rank, row in enumerate(json.loads(raw[start:]), start=1)}


def main() -> None:
    base = json.loads(BASE.read_text(encoding="utf8"))
    trial = json.loads(TRIAL.read_text(encoding="utf8"))
    assert base["unique_routes"] == trial["unique_routes"] == 100
    assert base["summary_sha256"] == trial["summary_sha256"]
    assert trial["candidate_sha256"] == hashlib.sha256(
        (ROOT / "exp_shunki_later_lookup_20260927.py").read_bytes()).hexdigest()
    assert trial["candidate_sha256"] == (
        "68aad0908c38884aba856373088f1a6ba4a0423df2ee00edbec4c796f8e45fac")
    assert base["candidate_sha256"] == hashlib.sha256((ROOT / "main.py").read_bytes()).hexdigest()
    by_base = {(row["action_sha256"], row["seed"], row["source_seat"]): row
               for row in base["rows"]}
    by_trial = {(row["action_sha256"], row["seed"], row["source_seat"]): row
                for row in trial["rows"]}
    assert len(by_base) == len(by_trial) == 100 and by_base.keys() == by_trial.keys()
    sources = {row["action_sha256"]: row for row in json.loads(
        (PANEL / "routes" / "summary.json").read_text(encoding="utf8"))}
    ranks = leaderboard()
    rows = []
    for key in by_base:
        old, new = by_base[key], by_trial[key]
        assert old["team"] == new["team"] and old["episode_id"] == new["episode_id"]
        old_games = {int(g["candidate_seat"]): g for g in old["games"]}
        new_games = {int(g["candidate_seat"]): g for g in new["games"]}
        assert old_games.keys() == new_games.keys() == {0, 1}
        assert all(g["candidate_status"] == g["opponent_status"] == "DONE"
                   for g in [*old_games.values(), *new_games.values()])
        old_margin = sum(float(g["margin"]) for g in old_games.values())
        new_margin = sum(float(g["margin"]) for g in new_games.values())
        shops = {str(seat): {"main": old_games[seat]["candidate_capture"]["shops"][:2],
                             "candidate": new_games[seat]["candidate_capture"]["shops"][:2]}
                 for seat in (0, 1)}
        rows.append({"rank": ranks[int(sources[key[0]]["team_id"])],
                     "team": old["team"], "seed": old["seed"],
                     "episode_id": old["episode_id"],
                     "action_sha256": key[0], "opponent_path": old["opponent_path"],
                     "main_pair_margin": old_margin,
                     "candidate_pair_margin": new_margin,
                     "margin_delta": new_margin - old_margin,
                     "main_win": old_margin > 0,
                     "candidate_win": new_margin > 0,
                     "shops_by_seat": shops,
                     "shops_match_seats": sum(shops[str(seat)]["main"] ==
                                              shops[str(seat)]["candidate"]
                                              for seat in (0, 1)),
                     "seat_margins": {str(seat): {"main": old_games[seat]["margin"],
                                                   "candidate": new_games[seat]["margin"]}
                                      for seat in (0, 1)}})
    rows.sort(key=lambda row: row["rank"])
    losses = sorted((row for row in rows if not row["candidate_win"]),
                    key=lambda row: row["candidate_pair_margin"])
    flips_up = [row for row in rows if not row["main_win"] and row["candidate_win"]]
    flips_down = [row for row in rows if row["main_win"] and not row["candidate_win"]]
    rank_bands = {}
    for band, low, high in (("1-10", 1, 10), ("11-20", 11, 20),
                            ("21-50", 21, 50), ("51-100", 51, 100)):
        subset = [row for row in rows if low <= row["rank"] <= high]
        rank_bands[band] = {"main_wins": sum(row["main_win"] for row in subset),
                            "candidate_wins": sum(row["candidate_win"] for row in subset)}
    pair_loss_counts = Counter(tuple(row["shops_by_seat"]["0"]["candidate"])
                               for row in losses)
    result = {"main_sha256": base["candidate_sha256"],
              "candidate_sha256": trial["candidate_sha256"],
              "panel_sha256": trial["summary_sha256"],
              "summary": {"routes": len(rows), "seats": 2 * len(rows),
                          "main_paired_wins": sum(row["main_win"] for row in rows),
                          "candidate_paired_wins": sum(row["candidate_win"] for row in rows),
                          "flipped_losses_to_wins": len(flips_up),
                          "flipped_wins_to_losses": len(flips_down),
                          "margin_delta_total": sum(row["margin_delta"] for row in rows),
                          "same_first_two_shops_seats": sum(row["shops_match_seats"]
                                                             for row in rows),
                          "rank_bands": rank_bands,
                          "candidate_loss_first_two_shop_counts":
                          {"|".join(key): count for key, count in pair_loss_counts.items()}},
              "largest_candidate_losses": losses[:20],
              "flips_up": flips_up, "flips_down": flips_down,
              "rows": rows}
    (HERE / "top100_analysis.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print("losses", [(row["rank"], row["team"], row["candidate_pair_margin"],
                       row["main_pair_margin"], row["shops_by_seat"]["0"]["candidate"])
                      for row in losses])
    print("flips up", [(row["rank"], row["team"]) for row in flips_up])
    print("flips down", [(row["rank"], row["team"]) for row in flips_down])


if __name__ == "__main__":
    main()
