"""One-at-a-time market-order mutations on the current V47 tapes."""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import gzip
import json
from pathlib import Path

from paired_benchmark import run_game


ROOT = Path(__file__).resolve().parent
ROUTES = {
    "brunch": (1282331517, ROOT / "live_top_leaderboard_routes_2026-09-21" / "KawattaTaido-submission-56417128-episode-111618298-seat0.json.gz"),
    "otter": (60782271, ROOT / "live_top_leaderboard_routes_2026-09-21" / "Otter-Vibe-submission-56353982-episode-111618299-seat0.json.gz"),
    "third": (198061245, ROOT / "live_top_leaderboard_routes_2026-09-21" / "THIRD-FARM-CLUB-submission-56372014-episode-111617135-seat1.json.gz"),
}


def _tape(name):
    path = ROOT / f"record_main_{name}_2026-09-21.json.gz"
    if name == "brunch":
        path = ROOT / "record_main_brunch.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)["actions"]


def _jobs(name, start=0, end=668):
    actions = _tape(name)
    for step, action in enumerate(actions[start:end], start):
        for index, order in enumerate(action.get("market") or []):
            if len(order) < 3 or order[0] not in {"SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"}:
                continue
            try:
                quantity = int(order[2])
            except (TypeError, ValueError):
                continue
            if quantity <= 0 or quantity > 100:
                continue
            for mode, delta in (("delta", -5), ("delta", -2), ("delta", -1), ("delta", 1), ("delta", 2), ("delta", 5), ("drop", 0)):
                if mode == "delta" and quantity + delta < 0:
                    continue
                yield {"tape": name, "step": step, "index": index, "mode": mode, "delta": delta}


def _play(job):
    seed, route = ROUTES[job["tape"]]
    try:
        return {
            **job,
            **run_game(
                candidate=str(ROOT / "mutable_tape_agent.py"),
                opponent=f"rawroute:{route.resolve()}",
                seed=seed,
                candidate_seat=0,
                debug=False,
                capture_step=None,
                candidate_overrides={
                    "_TAPE_NAME": job["tape"],
                    "_MUTATION_STEP": job["step"],
                    "_MUTATION_INDEX": job["index"],
                    "_MUTATION_MODE": job["mode"],
                    "_MUTATION_DELTA": job["delta"],
                },
            ),
        }
    except Exception as error:  # noqa: BLE001 - preserve search progress
        return {**job, "error": f"{type(error).__name__}: {error}"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=sorted(ROUTES), required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=668)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    jobs = list(_jobs(args.target, args.start, args.end))
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for index, row in enumerate(pool.map(_play, jobs), 1):
            rows.append(row)
            if index % 200 == 0:
                print(f"completed={index}/{len(jobs)}", flush=True)
    rows.sort(key=lambda row: float(row.get("margin", float("-inf"))), reverse=True)
    baseline = {
        "tape": args.target,
        **run_game(
            candidate=str(ROOT / "mutable_tape_agent.py"),
            opponent=f"rawroute:{ROUTES[args.target][1].resolve()}",
            seed=ROUTES[args.target][0],
            candidate_seat=0,
            debug=False,
            capture_step=None,
            candidate_overrides={"_TAPE_NAME": args.target},
        ),
    }
    output = ROOT / f"benchmark_mutable_tape_{args.target}_2026-09-21.json"
    output.write_text(json.dumps({"target": args.target, "baseline": baseline, "rows": rows}, indent=2), encoding="utf-8")
    print("BASELINE", baseline)
    print("TOP")
    for row in rows[:40]:
        print({key: row.get(key) for key in ("tape", "step", "index", "mode", "delta", "margin", "result", "candidate_reward", "opponent_reward")})
    print(f"wrote={output}")


if __name__ == "__main__":
    main()
