"""Search shop-aware action-tape splices on the two indistinguishable routes."""

from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path

from paired_benchmark import run_game


ROOT = Path(__file__).resolve().parent
SUMMARY = ROOT / "live_top_leaderboard_loss_routes_summary_2026-09-21.json"


def _play(job):
    prefix, brunch, pet, switch, route, seed, seat = job
    row = run_game(
        candidate=str(ROOT / "splice_tape_agent.py"),
        opponent=f"rawroute:{Path(route).resolve()}",
        seed=seed,
        candidate_seat=seat,
        debug=False,
        capture_step=None,
        candidate_overrides={
            "_PREFIX_TAPE": prefix,
            "_BRUNCH_TAPE": brunch,
            "_PET_TAPE": pet,
            "_SWITCH_STEP": switch,
        },
    )
    return {"prefix": prefix, "brunch": brunch, "pet": pet, "switch": switch, "route": route, **row}


def main() -> None:
    entries = json.loads(SUMMARY.read_text(encoding="utf-8"))
    routes = [(entry["team"], entry["path"], int(entry["seed"])) for entry in entries]
    prefixes = ("main", "v49", "amey")
    brunch_choices = ("amey", "v49")
    pet_choices = ("v49", "amey")
    jobs = []
    for prefix in prefixes:
        for brunch in brunch_choices:
            for pet in pet_choices:
                for switch in (150, 168, 192, 216, 240, 288, 360, 480, 600):
                    for _team, route, seed in routes[:2]:
                        for seat in (0, 1):
                            jobs.append((prefix, brunch, pet, switch, route, seed, seat))
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=14) as pool:
        for index, row in enumerate(pool.map(_play, jobs), 1):
            rows.append(row)
            if index % 200 == 0:
                print(f"completed={index}/{len(jobs)}", flush=True)

    grouped = {}
    for row in rows:
        key = (row["prefix"], row["brunch"], row["pet"], row["switch"])
        item = grouped.setdefault(key, {"margins": [], "routes": {}})
        item["margins"].append(float(row["margin"]))
        item["routes"].setdefault(row["seed"], 0.0)
        item["routes"][row["seed"]] += float(row["margin"])
    result = []
    for key, item in grouped.items():
        paired = list(item["routes"].values())
        result.append(
            {
                "prefix": key[0], "brunch": key[1], "pet": key[2], "switch": key[3],
                "games": len(item["margins"]),
                "wins": sum(value > 0 for value in item["margins"]),
                "losses": sum(value < 0 for value in item["margins"]),
                "paired_wins": sum(value > 0 for value in paired),
                "paired_losses": sum(value < 0 for value in paired),
                "brunch_margin": paired[0] if len(paired) > 0 else None,
                "pet_margin": paired[1] if len(paired) > 1 else None,
                "mean_margin": sum(item["margins"]) / len(item["margins"]),
            }
        )
    result.sort(key=lambda item: (item["paired_losses"], -item["mean_margin"]))
    payload = {"jobs": len(jobs), "results": result}
    (ROOT / "benchmark_splice_tape_grid_late_live_losses_2026-09-21.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for item in result[:30]:
        print(item)


if __name__ == "__main__":
    main()
