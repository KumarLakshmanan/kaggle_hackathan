"""Replay-holdout validation for the current H6 opening-queue probe."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import statistics
import sys

from paired_benchmark import engine_version, run_game


ROOT = Path(__file__).resolve().parent
PROBE_CANDIDATE = ROOT / "frontier_main_h6_opening_order_probe_2026-09-24.py"
BEST_PANEL = ROOT / "benchmark_frontier_h6_best_replay_2026-09-24.json"
FAILED_PANEL = ROOT / "benchmark_frontier_h6_failed_replay_2026-09-24.json"
OUTPUT_PATH = ROOT / "diagnostics" / "opening_queue_best_failed_holdouts_2026-09-24.json"
OPENING_MARKET = [
    ["BUY_PRODUCT", "WHEAT", 8],
    ["SELL", "WHEAT", 8],
    ["BUY_PRODUCT", "WHEAT", 5],
    ["BUY_SEED", "WHEAT", 1],
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    best = json.loads(BEST_PANEL.read_text(encoding="utf-8"))
    failed = json.loads(FAILED_PANEL.read_text(encoding="utf-8"))
    selected = [
        ("best_replay", best, row)
        for row in best["rows"]
    ] + [
        ("failed_replay", failed, row)
        for row in failed["rows"]
    ]
    results: list[dict] = []
    routes: list[dict] = []

    for index, (panel_name, panel, route) in enumerate(selected, start=1):
        game_rows = []
        opponent = "rawroute:" + str(route["opponent_path"])
        for seat in (0, 1):
            game = run_game(
                str(PROBE_CANDIDATE),
                opponent,
                int(route["seed"]),
                seat,
                False,
                None,
                {},
            )
            game.update(
                panel=panel_name,
                team=route["team"],
                opponent_path=route["opponent_path"],
            )
            game_rows.append(game)
            results.append(game)

        new_pair_margin = sum(float(game["margin"]) for game in game_rows)
        routes.append(
            {
                "panel": panel_name,
                "team": route["team"],
                "seed": int(route["seed"]),
                "opponent_path": route["opponent_path"],
                "historical_pair_margin": float(route["pair_margin"]),
                "probe_pair_margin": new_pair_margin,
                "change_vs_historical": new_pair_margin - float(route["pair_margin"]),
                "seat_results": [game["result"] for game in game_rows],
                "all_done": all(
                    game["candidate_status"] == "DONE"
                    and game["opponent_status"] == "DONE"
                    for game in game_rows
                ),
            }
        )
        payload = {
            "complete": False,
            "engine_version": engine_version,
            "probe_candidate": str(PROBE_CANDIDATE),
            "probe_candidate_sha256": sha256(PROBE_CANDIDATE),
            "best_panel_source": str(BEST_PANEL),
            "best_panel_candidate_sha256": best.get("candidate_sha256"),
            "failed_panel_source": str(FAILED_PANEL),
            "failed_panel_candidate_sha256": failed.get("candidate_sha256"),
            "opening_market": OPENING_MARKET,
            "routes": routes,
            "games": results,
        }
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(
            f"[{index}/{len(selected)}] {panel_name} | {route['team']}: "
            f"historical={float(route['pair_margin']):+.0f} "
            f"probe={new_pair_margin:+.0f} "
            f"seats={game_rows[0]['result']}/{game_rows[1]['result']}",
            flush=True,
        )

    paired_margins = [float(route["probe_pair_margin"]) for route in routes]
    result_counts = {
        "wins": sum(value > 0 for value in paired_margins),
        "draws": sum(value == 0 for value in paired_margins),
        "losses": sum(value < 0 for value in paired_margins),
    }
    payload.update(
        complete=True,
        summary={
            "routes": len(routes),
            "games": len(results),
            "route_results": result_counts,
            "game_results": {
                "wins": sum(row["margin"] > 0 for row in results),
                "draws": sum(row["margin"] == 0 for row in results),
                "losses": sum(row["margin"] < 0 for row in results),
            },
            "mean_paired_margin": statistics.fmean(paired_margins),
            "median_paired_margin": statistics.median(paired_margins),
            "all_done": all(route["all_done"] for route in routes),
            "agent_mean_us": statistics.fmean(
                row["candidate_timing"]["mean_us"] for row in results
            ),
            "agent_max_ms": max(
                row["candidate_timing"]["max_ms"] for row in results
            ),
        },
    )
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print("SUMMARY " + json.dumps(payload["summary"], sort_keys=True))
    print(f"wrote={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
