"""Exact native day-nine capture for the four ICE/BRUNCH panel losses."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

CANDIDATE = ROOT / "exp_shunki_later_lookup_20260927.py"


def trace(row: dict) -> dict:
    game = run_game(str(CANDIDATE), f"rawroute:{row['opponent_path']}",
                    int(row["seed"]), 0, False, 216, {})
    assert game["candidate_status"] == game["opponent_status"] == "DONE"
    assert float(game["margin"]) == float(row["seat_margins"]["0"]["candidate"])
    capture = game["candidate_capture"]
    player = int(capture["player"])
    return {"rank": row["rank"], "team": row["team"], "seed": row["seed"],
            "margin": game["margin"], "shops": capture["shops"],
            "our_day9": capture["farms"][player],
            "rival_day9": capture["farms"][1 - player],
            "our_cash": game["candidate_reward"],
            "rival_cash": game["opponent_reward"]}


def main() -> None:
    analysis = json.loads((HERE / "top100_analysis.json").read_text(encoding="utf8"))
    targets = [row for row in analysis["largest_candidate_losses"]
               if row["shops_by_seat"]["0"]["candidate"] ==
               ["ICE_CREAM_SHOP", "BRUNCH_SPOT"]]
    assert len(targets) == 4
    route_map = json.loads((ROOT / "diagnostics" / "shunki_portfolio_20260927" /
                            "later_shop_analysis.json").read_text(encoding="utf8"))["route_map"]
    with ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(trace, targets))
    for row in rows:
        shops = row["shops"]
        row["selected_source_at_day9"] = route_map.get("|".join(shops[:3]),
                                                        route_map["|".join(shops[:2])])
        row["source_available_for_triple"] = "|".join(shops[:3]) in route_map
    (HERE / "ice_brunch_loss_captures.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf8")
    for row in rows:
        print(row["rank"], row["team"], row["seed"], row["shops"][:3],
              row["selected_source_at_day9"], "margin", row["margin"],
              "farm_money", row["our_day9"]["money"], row["rival_day9"]["money"])


if __name__ == "__main__":
    main()
