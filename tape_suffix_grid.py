"""Small offline grid for V47-preserving downloaded action-book suffixes."""

from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path

from paired_benchmark import run_game


ROOT = Path(__file__).resolve().parent
ROUTES = [
    (60782271, ROOT / "live_top_leaderboard_routes_2026-09-21" / "Otter-Vibe-submission-56353982-episode-111618299-seat0.json.gz"),
    (198061245, ROOT / "live_top_leaderboard_routes_2026-09-21" / "THIRD-FARM-CLUB-submission-56372014-episode-111617135-seat1.json.gz"),
]
TAPES = ("v43", "amey", "v49", "frontier", "main")
SWITCHES = (1, 2, 4, 8, 16, 24, 48, 72, 88, 120, 150, 168, 192, 216, 240, 288, 360, 480, 600)


def _play(job):
    otter_tape, third_tape, switch, seed, route, seat = job
    return {
        "otter_tape": otter_tape,
        "third_tape": third_tape,
        "switch": switch,
        "seed": seed,
        "candidate_seat": seat,
        **run_game(
            candidate=str(ROOT / "hybrid_v47_route_tape_probe.py"),
            opponent=f"rawroute:{route.resolve()}",
            seed=seed,
            candidate_seat=seat,
            debug=False,
            capture_step=None,
            candidate_overrides={
                "_OTTER_TAPE": otter_tape,
                "_THIRD_TAPE": third_tape,
                "_SWITCH_STEP": switch,
            },
        ),
    }


def main():
    jobs = [
        (otter_tape, third_tape, switch, seed, route, seat)
        for otter_tape in TAPES
        for third_tape in TAPES
        for switch in SWITCHES
        for seed, route in ROUTES
        for seat in (0, 1)
    ]
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=12) as pool:
        for index, row in enumerate(pool.map(_play, jobs), 1):
            rows.append(row)
            if index % 200 == 0:
                print(f"completed={index}/{len(jobs)}", flush=True)

    grouped = {}
    for row in rows:
        key = (row["otter_tape"], row["third_tape"], row["switch"])
        item = grouped.setdefault(key, {"rows": [], "paired": {}})
        item["rows"].append(row)
        item["paired"].setdefault(row["seed"], 0.0)
        item["paired"][row["seed"]] += float(row["margin"])

    result = []
    for key, item in grouped.items():
        margins = [float(row["margin"]) for row in item["rows"]]
        paired = list(item["paired"].values())
        result.append(
            {
                "otter_tape": key[0],
                "third_tape": key[1],
                "switch": key[2],
                "wins": sum(value > 0 for value in margins),
                "losses": sum(value < 0 for value in margins),
                "paired_wins": sum(value > 0 for value in paired),
                "paired_losses": sum(value < 0 for value in paired),
                "otter_margin": item["paired"].get(60782271),
                "third_margin": item["paired"].get(198061245),
                "mean_margin": sum(margins) / len(margins),
            }
        )
    result.sort(key=lambda item: (item["paired_losses"], -item["mean_margin"]))
    payload = {"jobs": len(jobs), "rows": rows, "results": result}
    output = ROOT / "benchmark_v47_route_tape_suffix_grid_2026-09-21.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for item in result[:40]:
        print(item)
    print(f"wrote={output}")


if __name__ == "__main__":
    main()

