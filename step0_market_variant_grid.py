"""Search robust step-zero market openings against the known loss routes."""

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
    "pet": (1240527069, ROOT / "live_top_leaderboard_routes_2026-09-21" / "KawattaTaido-submission-56417128-episode-111625003-seat1.json.gz"),
    "otter": (60782271, ROOT / "live_top_leaderboard_routes_2026-09-21" / "Otter-Vibe-submission-56353982-episode-111618299-seat0.json.gz"),
    "third": (198061245, ROOT / "live_top_leaderboard_routes_2026-09-21" / "THIRD-FARM-CLUB-submission-56372014-episode-111617135-seat1.json.gz"),
}


def _variants():
    base = [["BUY_PRODUCT", "WHEAT", 10], ["SELL", "WHEAT", 10]]
    amey = [["BUY_PRODUCT", "WHEAT", 4], ["HIRE"], ["HIRE"], ["BUY_SEED", "MELON", 7], ["BUY_SEED", "WHEAT", 5], ["BUY_ANIMAL", "SHEEP", 4]]
    result = {"main": base, "amey": amey}
    extras = [
        ["HIRE"], ["HIRE"], ["BUY_SEED", "MELON", 7], ["BUY_SEED", "WHEAT", 5], ["BUY_ANIMAL", "SHEEP", 1],
        ["BUY_ANIMAL", "SHEEP", 2], ["BUY_ANIMAL", "SHEEP", 3], ["BUY_ANIMAL", "SHEEP", 4],
    ]
    for name, extra in (
        ("base_hires", extras[:2]),
        ("base_hires_sheep4", extras[:2] + [extras[7]]),
        ("base_hires_melon", extras[:2] + [extras[2]]),
        ("base_hires_wheat", extras[:2] + [extras[3]]),
        ("base_hires_melon_sheep", extras[:2] + [extras[2], extras[7]]),
        ("base_hires_wheat_sheep", extras[:2] + [extras[3], extras[7]]),
        ("base_all_extras", extras[:4] + [extras[7]]),
    ):
        result[name] = base + extra
    for quantity in (1, 2, 3, 4):
        result[f"base_sheep{quantity}"] = base + [["BUY_ANIMAL", "SHEEP", quantity]]
    for melon in (1, 2, 4, 7):
        result[f"base_melon{melon}"] = base + [["BUY_SEED", "MELON", melon]]
    for wheat in (1, 2, 5):
        result[f"base_wheat{wheat}"] = base + [["BUY_SEED", "WHEAT", wheat]]
    # Keep the Amey opening shape but use main's neutral net-wheat trade.
    for sheep in (1, 2, 3, 4):
        result[f"amey_net_sheep{sheep}"] = [["BUY_PRODUCT", "WHEAT", 10], ["SELL", "WHEAT", 10], ["HIRE"], ["HIRE"], ["BUY_SEED", "MELON", 7], ["BUY_SEED", "WHEAT", 5], ["BUY_ANIMAL", "SHEEP", sheep]]
    return result


VARIANTS = _variants()


def _play(job):
    name, route_name = job
    seed, route = ROUTES[route_name]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            row = run_game(
                candidate=str(ROOT / "step0_market_variant_agent.py"),
                opponent=f"rawroute:{route.resolve()}",
                seed=seed,
                candidate_seat=0,
                debug=False,
                capture_step=None,
                candidate_overrides={"_STEP0_MARKET": VARIANTS[name]},
            )
        return {"variant": name, "route": route_name, **row}
    except Exception as error:  # noqa: BLE001 - preserve grid progress
        return {"variant": name, "route": route_name, "error": f"{type(error).__name__}: {error}"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    jobs = [(name, route) for name in VARIANTS for route in ROUTES]
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for index, row in enumerate(pool.map(_play, jobs), 1):
            rows.append(row)
            if index % 40 == 0:
                print(f"completed={index}/{len(jobs)}", flush=True)
    grouped = {}
    for row in rows:
        if "error" not in row:
            grouped.setdefault(row["variant"], []).append(float(row["margin"]))
    summary = [
        {"variant": name, "wins": sum(m > 0 for m in margins), "losses": sum(m < 0 for m in margins), "mean_margin": sum(margins) / len(margins), "margins": margins}
        for name, margins in grouped.items()
    ]
    summary.sort(key=lambda item: (item["wins"], item["mean_margin"]), reverse=True)
    args.output.write_text(json.dumps({"variants": VARIANTS, "rows": rows, "summary": summary}, indent=2), encoding="utf-8")
    for item in summary[:20]:
        print(item)
    print(f"wrote={args.output}")


if __name__ == "__main__":
    main()
