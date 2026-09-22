"""Try pairs of the strongest single market mutations on a loss route."""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import io
import itertools
import json
from pathlib import Path

from paired_benchmark import run_game


ROOT = Path(__file__).resolve().parent
ROUTES = {
    "brunch": (1282331517, ROOT / "live_top_leaderboard_routes_2026-09-21" / "KawattaTaido-submission-56417128-episode-111618298-seat0.json.gz", ROOT / "analysis_artifacts" / "main_v49_brunch_seat0.json.gz"),
    "otter": (60782271, ROOT / "live_top_leaderboard_routes_2026-09-21" / "Otter-Vibe-submission-56353982-episode-111618299-seat0.json.gz", ROOT / "analysis_artifacts" / "main_v49_otter_seat0.json.gz"),
}


def _play(job):
    name, mutations = job
    seed, route, tape = ROUTES[name]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            row = run_game(
                candidate=str(ROOT / "recorded_tape_multi_mutation_agent.py"),
                opponent=f"rawroute:{route.resolve()}",
                seed=seed,
                candidate_seat=0,
                debug=False,
                capture_step=None,
                candidate_overrides={"_TAPE_PATH": str(tape.resolve()), "_MUTATIONS": mutations},
            )
        return {"route": name, "mutations": mutations, **row}
    except Exception as error:  # noqa: BLE001 - preserve search progress
        return {"route": name, "mutations": mutations, "error": f"{type(error).__name__}: {error}"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", choices=sorted(ROUTES), required=True)
    parser.add_argument("--single-output", type=Path, required=True)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.single_output.read_text(encoding="utf-8"))["rows"]
    candidates = []
    seen = set()
    for row in sorted(source, key=lambda item: float(item.get("margin", float("-inf"))), reverse=True):
        if "error" in row:
            continue
        mutation = {key: row[key] for key in ("step", "index", "mode", "delta")}
        key = json.dumps(mutation, sort_keys=True)
        if key not in seen:
            seen.add(key)
            candidates.append(mutation)
        if len(candidates) >= args.top:
            break
    jobs = [(args.route, list(pair)) for pair in itertools.combinations(candidates, 2)]
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for index, row in enumerate(pool.map(_play, jobs), 1):
            rows.append(row)
            if index % 50 == 0:
                print(f"completed={index}/{len(jobs)}", flush=True)
    rows.sort(key=lambda row: float(row.get("margin", float("-inf"))), reverse=True)
    args.output.write_text(json.dumps({"route": args.route, "candidates": candidates, "rows": rows}, indent=2), encoding="utf-8")
    print("TOP")
    for row in rows[:25]:
        print({key: row.get(key) for key in ("mutations", "margin", "result")})
    print(f"wrote={args.output}")


if __name__ == "__main__":
    main()
