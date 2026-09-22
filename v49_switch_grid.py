"""Benchmark V49 continuation entry points against selected replay routes."""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import io
import json
from pathlib import Path

from paired_benchmark import run_game


ROOT = Path(__file__).resolve().parent
ROUTES = {
    "brunch": (1282331517, ROOT / "live_top_leaderboard_routes_2026-09-21" / "KawattaTaido-submission-56417128-episode-111618298-seat0.json.gz"),
    "otter": (60782271, ROOT / "live_top_leaderboard_routes_2026-09-21" / "Otter-Vibe-submission-56353982-episode-111618299-seat0.json.gz"),
    "pet": (1240527069, ROOT / "live_top_leaderboard_routes_2026-09-21" / "KawattaTaido-submission-56417128-episode-111625003-seat1.json.gz"),
    "third": (198061245, ROOT / "live_top_leaderboard_routes_2026-09-21" / "THIRD-FARM-CLUB-submission-56372014-episode-111617135-seat1.json.gz"),
}


def _play(job):
    name, step, seat = job
    seed, route = ROUTES[name]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            row = run_game(
                candidate=str(ROOT / "hybrid_main_v49_late.py"),
                opponent=f"rawroute:{route.resolve()}",
                seed=seed,
                candidate_seat=seat,
                debug=False,
                capture_step=None,
                candidate_overrides={"_SWITCH_STEP": step},
            )
        return {"route": name, "switch_step": step, **row}
    except Exception as error:  # noqa: BLE001 - preserve grid progress
        return {"route": name, "switch_step": step, "candidate_seat": seat,
                "error": f"{type(error).__name__}: {error}"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--routes", nargs="+", choices=sorted(ROUTES), required=True)
    parser.add_argument("--steps", nargs="+", type=int, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    jobs = [(route, step, seat) for route in args.routes for step in args.steps for seat in (0, 1)]
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for index, row in enumerate(pool.map(_play, jobs), 1):
            rows.append(row)
            if index % 4 == 0:
                print(f"completed={index}/{len(jobs)}", flush=True)
    good = [row for row in rows if "error" not in row]
    grouped = {}
    for row in good:
        grouped.setdefault((row["route"], row["switch_step"]), []).append(row)
    summary = []
    for (route, step), items in grouped.items():
        margins = [float(item["margin"]) for item in items]
        summary.append({
            "route": route,
            "switch_step": step,
            "wins": sum(margin > 0 for margin in margins),
            "losses": sum(margin < 0 for margin in margins),
            "mean_margin": sum(margins) / len(margins),
            "paired_margin": sum(margins),
        })
    summary.sort(key=lambda item: (item["route"], -item["paired_margin"]))
    payload = {"rows": rows, "summary": summary}
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for item in summary:
        print(item)
    print(f"wrote={args.output}")


if __name__ == "__main__":
    main()
