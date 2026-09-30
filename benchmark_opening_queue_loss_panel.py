"""Paired benchmark of the turn-0 queue probe on the saved loss routes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from paired_benchmark import engine_version, run_game, summarize


ROOT = Path(__file__).resolve().parent
BASELINE_PATH = ROOT / "benchmark_frontier_h6_ranks501-600_full98_2026-09-24.json"
CANDIDATE_PATH = ROOT / "frontier_h6_opening_order_probe_2026-09-24.py"
OUTPUT_PATH = ROOT / "diagnostics" / "opening_queue_15loss_panel_2026-09-24.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    losses = [row for row in baseline["rows"] if float(row["pair_margin"]) < 0]
    losses.sort(key=lambda row: float(row["pair_margin"]))
    results: list[dict] = []
    routes: list[dict] = []

    for index, route in enumerate(losses, start=1):
        route_results = []
        opponent = "rawroute:" + str(route["opponent_path"])
        for seat in (0, 1):
            game = run_game(
                str(CANDIDATE_PATH),
                opponent,
                int(route["seed"]),
                seat,
                False,
                None,
                {},
            )
            game["team"] = route["team"]
            game["opponent_path"] = route["opponent_path"]
            route_results.append(game)
            results.append(game)

        new_pair_margin = sum(float(game["margin"]) for game in route_results)
        routes.append(
            {
                "team": route["team"],
                "seed": int(route["seed"]),
                "opponent_path": route["opponent_path"],
                "baseline_pair_margin": float(route["pair_margin"]),
                "probe_pair_margin": new_pair_margin,
                "improvement": new_pair_margin - float(route["pair_margin"]),
                "wins": sum(game["margin"] > 0 for game in route_results),
                "losses": sum(game["margin"] < 0 for game in route_results),
                "draws": sum(game["margin"] == 0 for game in route_results),
                "all_done": all(
                    game["candidate_status"] == "DONE"
                    and game["opponent_status"] == "DONE"
                    for game in route_results
                ),
                "games": route_results,
            }
        )
        checkpoint = {
            "complete": False,
            "engine_version": engine_version,
            "baseline_path": str(BASELINE_PATH),
            "baseline_candidate_sha256": baseline.get("candidate_sha256"),
            "probe_candidate_path": str(CANDIDATE_PATH),
            "probe_candidate_sha256": sha256(CANDIDATE_PATH),
            "opening_market": [
                ["BUY_PRODUCT", "WHEAT", 8],
                ["SELL", "WHEAT", 8],
                ["BUY_PRODUCT", "WHEAT", 5],
                ["BUY_SEED", "WHEAT", 1],
            ],
            "routes": routes,
            "games": results,
            "summary": summarize(results),
        }
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(
            json.dumps(checkpoint, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(
            f"[{index}/{len(losses)}] {route['team']}: "
            f"baseline={float(route['pair_margin']):+.0f} "
            f"probe={new_pair_margin:+.0f} "
            f"delta={new_pair_margin-float(route['pair_margin']):+.0f} "
            f"seats={route_results[0]['result']}/{route_results[1]['result']}",
            flush=True,
        )

    payload = {
        "complete": True,
        "engine_version": engine_version,
        "baseline_path": str(BASELINE_PATH),
        "baseline_candidate_sha256": baseline.get("candidate_sha256"),
        "probe_candidate_path": str(CANDIDATE_PATH),
        "probe_candidate_sha256": sha256(CANDIDATE_PATH),
        "opening_market": [
            ["BUY_PRODUCT", "WHEAT", 8],
            ["SELL", "WHEAT", 8],
            ["BUY_PRODUCT", "WHEAT", 5],
            ["BUY_SEED", "WHEAT", 1],
        ],
        "routes": routes,
        "games": results,
        "summary": summarize(results),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print("SUMMARY " + json.dumps(payload["summary"], sort_keys=True))
    print(f"wrote={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
