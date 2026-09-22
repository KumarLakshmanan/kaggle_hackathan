"""Search one market-order mutation on the current production replay tape."""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import copy
import gzip
import io
import json
from pathlib import Path

from paired_benchmark import run_game


ROOT = Path(__file__).resolve().parent
ROUTES = {
    "brunch": (1282331517, ROOT / "live_top_leaderboard_routes_2026-09-21" / "KawattaTaido-submission-56417128-episode-111618298-seat0.json.gz", ROOT / "analysis_artifacts" / "main_v49_brunch_seat0.json.gz"),
    "otter": (60782271, ROOT / "live_top_leaderboard_routes_2026-09-21" / "Otter-Vibe-submission-56353982-episode-111618299-seat0.json.gz", ROOT / "analysis_artifacts" / "main_v49_otter_seat0.json.gz"),
}


def _jobs(name, start, end):
    tape = json.load(gzip.open(ROUTES[name][2], "rt", encoding="utf-8"))["actions"]
    for step in range(max(0, start), min(len(tape), end)):
        for index, order in enumerate(tape[step].get("market") or []):
            # Keep the first order position: changing later orders often only
            # changes an order that the shared market never reaches.
            if index != 0 or not isinstance(order, list) or len(order) < 3:
                continue
            if order[0] not in {"SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"}:
                continue
            try:
                quantity = int(order[2])
            except (TypeError, ValueError):
                continue
            if quantity <= 0 or quantity > 100:
                continue
            for mode, delta in (("delta", -5), ("delta", -1), ("delta", 1), ("delta", 5), ("drop", 0)):
                if mode == "delta" and quantity + delta < 0:
                    continue
                yield {"route": name, "step": step, "index": index, "mode": mode, "delta": delta}


def _play(job):
    seed, route, tape = ROUTES[job["route"]]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            row = run_game(
                candidate=str(ROOT / "recorded_tape_mutation_agent.py"),
                opponent=f"rawroute:{route.resolve()}",
                seed=seed,
                candidate_seat=0,
                debug=False,
                capture_step=None,
                candidate_overrides={
                    "_TAPE_PATH": str(tape.resolve()),
                    "_MUTATION_STEP": job["step"],
                    "_MUTATION_INDEX": job["index"],
                    "_MUTATION_MODE": job["mode"],
                    "_MUTATION_DELTA": job["delta"],
                },
            )
        return {**job, **row}
    except Exception as error:  # noqa: BLE001 - preserve search progress
        return {**job, "error": f"{type(error).__name__}: {error}"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", choices=sorted(ROUTES), required=True)
    parser.add_argument("--start", type=int, default=480)
    parser.add_argument("--end", type=int, default=580)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    jobs = list(_jobs(args.route, args.start, args.end))
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for index, row in enumerate(pool.map(_play, jobs), 1):
            rows.append(row)
            if index % 100 == 0:
                print(f"completed={index}/{len(jobs)}", flush=True)
    rows.sort(key=lambda row: float(row.get("margin", float("-inf"))), reverse=True)
    payload = {"route": args.route, "start": args.start, "end": args.end, "rows": rows}
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("TOP")
    for row in rows[:30]:
        print({key: row.get(key) for key in ("step", "index", "mode", "delta", "margin", "result")})
    print(f"wrote={args.output}")


if __name__ == "__main__":
    main()
