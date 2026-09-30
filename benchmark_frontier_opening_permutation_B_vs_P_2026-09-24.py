"""Paired fixed-tape test of B vs. its quantity-matched order permutation P.

This is a diagnostic experiment, not a Kaggle submission or a change to main.py.
It selects all 16 B-loss routes plus the 16 closest B-win routes from the saved
301-420 development panel, then plays both candidate seats for each arm.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import statistics
import sys

from paired_benchmark import engine_version, run_game


ROOT = Path(__file__).resolve().parent
SOURCE_PANEL = ROOT / "diagnostics" / "mainfrontier_h6_opening_B_ranks301-420_full_2026-09-24.json"
ARM_CANDIDATE = ROOT / "main_frontier_h6_opening_arm_2026-09-24.py"
BASE_CANDIDATE = ROOT / "main_frontier_h6_candidate_2026-09-24.py"
OUTPUT_PATH = ROOT / "diagnostics" / "mainfrontier_h6_opening_permutation_BvsP_loss16_win16_2026-09-24.json"
ARMS = ("B", "P")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def choose_routes(panel: dict) -> list[tuple[str, dict]]:
    rows = panel["rows"]
    losses = sorted(
        (row for row in rows if float(row["pair_margin"]) < 0),
        key=lambda row: float(row["pair_margin"]),
    )
    if len(losses) != 16:
        raise ValueError(f"Expected 16 B-loss routes; found {len(losses)}")

    # Use the nearest positive margins, but only one control route per team so
    # repeated seeds from one public submission do not dominate this pilot.
    wins = sorted(
        (row for row in rows if float(row["pair_margin"]) > 0),
        key=lambda row: float(row["pair_margin"]),
    )
    controls: list[dict] = []
    seen_teams: set[str] = set()
    for row in wins:
        team = str(row["team"])
        if team in seen_teams:
            continue
        controls.append(row)
        seen_teams.add(team)
        if len(controls) == len(losses):
            break
    if len(controls) != len(losses):
        raise ValueError(f"Expected 16 distinct-team win controls; found {len(controls)}")

    return [("B_loss", row) for row in losses] + [("near_B_win_control", row) for row in controls]


def save_checkpoint(payload: dict, complete: bool) -> None:
    payload["complete"] = complete
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def result_counts(games: list[dict]) -> dict[str, int]:
    return {
        "wins": sum(row["result"] == "win" for row in games),
        "draws": sum(row["result"] == "draw" for row in games),
        "losses": sum(row["result"] == "loss" for row in games),
    }


def summarize(routes: list[dict], games: list[dict]) -> dict:
    route_margins = {
        arm: [float(route[f"{arm}_pair_margin"]) for route in routes]
        for arm in ARMS
    }
    arm_games = {
        arm: [game for game in games if game["arm"] == arm]
        for arm in ARMS
    }
    p_minus_b = [float(route["P_pair_margin"]) - float(route["B_pair_margin"]) for route in routes]
    flip_counts = {
        "B_loss_to_P_win": sum(
            route["B_pair_margin"] < 0 <= route["P_pair_margin"] for route in routes
        ),
        "B_win_to_P_loss": sum(
            route["B_pair_margin"] >= 0 > route["P_pair_margin"] for route in routes
        ),
    }
    return {
        "routes": len(routes),
        "games": len(games),
        "all_done": all(
            game["candidate_status"] == "DONE" and game["opponent_status"] == "DONE"
            for game in games
        ),
        "route_results": {
            arm: {
                "wins": sum(value > 0 for value in values),
                "draws": sum(value == 0 for value in values),
                "losses": sum(value < 0 for value in values),
                "mean_pair_margin": statistics.fmean(values),
            }
            for arm, values in route_margins.items()
        },
        "game_results": {
            arm: {
                **result_counts(arm_games[arm]),
                "mean_margin": statistics.fmean(float(game["margin"]) for game in arm_games[arm]),
                "win_score": (
                    sum(game["result"] == "win" for game in arm_games[arm])
                    + 0.5 * sum(game["result"] == "draw" for game in arm_games[arm])
                ) / len(arm_games[arm]),
            }
            for arm in ARMS
        },
        "P_minus_B": {
            "mean_paired_route_margin": statistics.fmean(p_minus_b),
            "total_paired_route_margin": sum(p_minus_b),
            "route_outcome_flips": flip_counts,
        },
        "B_exactly_reproduces_source_panel": all(
            route["B_pair_margin"] == route["source_B_pair_margin"]
            for route in routes
        ),
        "B_source_panel_mismatches": [
            {
                "team": route["team"],
                "seed": route["seed"],
                "source": route["source_B_pair_margin"],
                "rerun": route["B_pair_margin"],
            }
            for route in routes
            if route["B_pair_margin"] != route["source_B_pair_margin"]
        ],
        "agent_mean_us": {
            arm: statistics.fmean(
                float(game["candidate_timing"]["mean_us"])
                for game in arm_games[arm]
                if game["candidate_timing"] is not None
            )
            for arm in ARMS
        },
        "agent_max_ms": {
            arm: max(
                float(game["candidate_timing"]["max_ms"])
                for game in arm_games[arm]
                if game["candidate_timing"] is not None
            )
            for arm in ARMS
        },
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if OUTPUT_PATH.exists():
        raise FileExistsError(f"Refusing to overwrite existing report: {OUTPUT_PATH}")

    panel = json.loads(SOURCE_PANEL.read_text(encoding="utf-8"))
    selected = choose_routes(panel)
    payload = {
        "engine_version": engine_version,
        "source_panel": str(SOURCE_PANEL),
        "source_panel_sha256": sha256(SOURCE_PANEL),
        "source_candidate_sha256": panel.get("candidate_sha256"),
        "base_candidate": str(BASE_CANDIDATE),
        "base_candidate_sha256": sha256(BASE_CANDIDATE),
        "arm_candidate": str(ARM_CANDIDATE),
        "arm_candidate_sha256": sha256(ARM_CANDIDATE),
        "selection": {
            "all_16_B_loss_routes": True,
            "win_controls": "16 smallest positive B paired margins, unique team names",
            "route_count": len(selected),
            "seats_per_arm_route": [0, 1],
            "arms": {
                "B": [
                    ["BUY_PRODUCT", "WHEAT", 8],
                    ["SELL", "WHEAT", 8],
                    ["BUY_PRODUCT", "WHEAT", 5],
                    ["BUY_SEED", "WHEAT", 1],
                ],
                "P": [
                    ["BUY_PRODUCT", "WHEAT", 8],
                    ["BUY_PRODUCT", "WHEAT", 5],
                    ["SELL", "WHEAT", 8],
                    ["BUY_SEED", "WHEAT", 1],
                ],
            },
        },
        "routes": [],
        "games": [],
    }

    old_arm = os.environ.get("KAGG_OPENING_ARM")
    try:
        for index, (stratum, source_route) in enumerate(selected, start=1):
            record = {
                "stratum": stratum,
                "team": source_route["team"],
                "seed": int(source_route["seed"]),
                "opponent_path": source_route["opponent_path"],
                "source_B_pair_margin": float(source_route["pair_margin"]),
            }
            arm_games: dict[str, list[dict]] = {arm: [] for arm in ARMS}
            opponent = "rawroute:" + str(source_route["opponent_path"])
            for arm in ARMS:
                os.environ["KAGG_OPENING_ARM"] = arm
                for seat in (0, 1):
                    game = run_game(
                        str(ARM_CANDIDATE), opponent, int(source_route["seed"]), seat,
                        False, None, {},
                    )
                    telemetry = game.get("candidate_telemetry") or {}
                    if telemetry.get("opening_arm") != arm or telemetry.get("opening_arm_applied") != 1:
                        raise RuntimeError(
                            f"Opening arm failed to apply: expected {arm}, got {telemetry}"
                        )
                    game.update(
                        arm=arm,
                        stratum=stratum,
                        team=source_route["team"],
                        opponent_path=source_route["opponent_path"],
                    )
                    arm_games[arm].append(game)
                    payload["games"].append(game)

            record["B_pair_margin"] = sum(float(game["margin"]) for game in arm_games["B"])
            record["P_pair_margin"] = sum(float(game["margin"]) for game in arm_games["P"])
            record["P_minus_B"] = record["P_pair_margin"] - record["B_pair_margin"]
            record["B_seat_results"] = [game["result"] for game in arm_games["B"]]
            record["P_seat_results"] = [game["result"] for game in arm_games["P"]]
            record["all_done"] = all(
                game["candidate_status"] == "DONE" and game["opponent_status"] == "DONE"
                for group in arm_games.values()
                for game in group
            )
            payload["routes"].append(record)
            payload["summary"] = summarize(payload["routes"], payload["games"])
            save_checkpoint(payload, complete=False)
            print(
                f"[{index}/{len(selected)}] {stratum} | {source_route['team']}: "
                f"B={record['B_pair_margin']:+.0f} P={record['P_pair_margin']:+.0f} "
                f"delta={record['P_minus_B']:+.0f} "
                f"seats={'/'.join(record['B_seat_results'])}->{ '/'.join(record['P_seat_results']) }",
                flush=True,
            )

        payload["summary"] = summarize(payload["routes"], payload["games"])
        save_checkpoint(payload, complete=True)
        print("SUMMARY " + json.dumps(payload["summary"], sort_keys=True))
        print(f"wrote={OUTPUT_PATH}")
    finally:
        if old_arm is None:
            os.environ.pop("KAGG_OPENING_ARM", None)
        else:
            os.environ["KAGG_OPENING_ARM"] = old_arm


if __name__ == "__main__":
    main()
