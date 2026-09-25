"""Compare the opening-queue probe with the current H6 candidate on its loss routes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from paired_benchmark import engine_version, run_game, summarize


ROOT = Path(__file__).resolve().parent
BASELINE_PANEL = ROOT / "benchmark_frontier_h6_ranks501-600_full98_2026-09-24.json"
BASE_CANDIDATE = ROOT / "main_frontier_h6_candidate_2026-09-24.py"
PROBE_CANDIDATE = ROOT / "frontier_main_h6_opening_order_probe_2026-09-24.py"
OUTPUT_PATH = ROOT / "diagnostics" / "current_mainfrontier_opening_queue_15loss_panel_2026-09-24.json"
OPENING_MARKET = [
    ["BUY_PRODUCT", "WHEAT", 8],
    ["SELL", "WHEAT", 8],
    ["BUY_PRODUCT", "WHEAT", 5],
    ["BUY_SEED", "WHEAT", 1],
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_checkpoint(routes: list[dict], games: list[dict], complete: bool) -> None:
    payload = {
        "complete": complete,
        "engine_version": engine_version,
        "baseline_panel": str(BASELINE_PANEL),
        "baseline_panel_candidate_sha256": json.loads(
            BASELINE_PANEL.read_text(encoding="utf-8")
        ).get("candidate_sha256"),
        "base_candidate": str(BASE_CANDIDATE),
        "base_candidate_sha256": sha256(BASE_CANDIDATE),
        "probe_candidate": str(PROBE_CANDIDATE),
        "probe_candidate_sha256": sha256(PROBE_CANDIDATE),
        "opening_market": OPENING_MARKET,
        "routes": routes,
        "games": games,
        "base_summary": summarize([game for game in games if game["variant"] == "base"]),
        "probe_summary": summarize([game for game in games if game["variant"] == "probe"]),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    baseline = json.loads(BASELINE_PANEL.read_text(encoding="utf-8"))
    losses = [row for row in baseline["rows"] if float(row["pair_margin"]) < 0]
    losses.sort(key=lambda row: float(row["pair_margin"]))
    games: list[dict] = []
    routes: list[dict] = []

    for index, route in enumerate(losses, start=1):
        route_games: dict[str, list[dict]] = {"base": [], "probe": []}
        opponent = "rawroute:" + str(route["opponent_path"])
        for variant, candidate_path in (
            ("base", BASE_CANDIDATE),
            ("probe", PROBE_CANDIDATE),
        ):
            for seat in (0, 1):
                game = run_game(
                    str(candidate_path),
                    opponent,
                    int(route["seed"]),
                    seat,
                    False,
                    None,
                    {},
                )
                game.update(
                    variant=variant,
                    team=route["team"],
                    opponent_path=route["opponent_path"],
                )
                route_games[variant].append(game)
                games.append(game)

        base_pair = sum(float(row["margin"]) for row in route_games["base"])
        probe_pair = sum(float(row["margin"]) for row in route_games["probe"])
        record = {
            "team": route["team"],
            "seed": int(route["seed"]),
            "opponent_path": route["opponent_path"],
            "previous_panel_pair_margin": float(route["pair_margin"]),
            "current_base_pair_margin": base_pair,
            "probe_pair_margin": probe_pair,
            "improvement_vs_current_base": probe_pair - base_pair,
            "base_seat_results": [row["result"] for row in route_games["base"]],
            "probe_seat_results": [row["result"] for row in route_games["probe"]],
            "all_done": all(
                row["candidate_status"] == "DONE" and row["opponent_status"] == "DONE"
                for group in route_games.values()
                for row in group
            ),
        }
        routes.append(record)
        save_checkpoint(routes, games, False)
        print(
            f"[{index}/{len(losses)}] {route['team']}: "
            f"base={base_pair:+.0f} probe={probe_pair:+.0f} "
            f"delta={probe_pair-base_pair:+.0f} "
            f"seats={'/'.join(record['base_seat_results'])}"
            f"->{'/'.join(record['probe_seat_results'])}",
            flush=True,
        )

    save_checkpoint(routes, games, True)
    print(f"wrote={OUTPUT_PATH}")


if __name__ == "__main__":
    main()
