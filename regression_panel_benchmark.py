"""Rerun a prior benchmark panel with a new candidate."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path
from typing import Any

from paired_benchmark import run_game, summarize


def _play(job: tuple[str, str, int, int, str]) -> dict[str, Any]:
    candidate, opponent, seed, seat, key = job
    row = run_game(candidate, opponent, seed, seat, False, None, {})
    row["key"] = key
    row["opponent"] = opponent
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--baseline-report", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    baseline = json.loads(args.baseline_report.read_text(encoding="utf-8"))
    jobs = []
    for group in baseline["rows"]:
        seeds = sorted({int(row["seed"]) for row in group["rows"]})
        for seed in seeds:
            for seat in (0, 1):
                jobs.append((args.candidate, group["opponent"], seed, seat, str(group["key"])))

    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(_play, jobs):
            rows.append(row)
            print(
                f"key={row['key']} seat={row['candidate_seat']} "
                f"margin={row['margin']:+.0f} result={row['result']}",
                flush=True,
            )

    groups = []
    for source in baseline["rows"]:
        key = str(source["key"])
        games = [row for row in rows if row["key"] == key]
        groups.append(
            {
                "key": key,
                "opponent": source["opponent"],
                "rows": games,
                "pair_margin": sum(float(row["margin"]) for row in games),
            }
        )
    payload = {
        "candidate": str(Path(args.candidate).resolve()),
        "baseline_report": str(args.baseline_report.resolve()),
        "rows": groups,
        "summary": summarize(rows),
        "opponent_paired_results": {
            "wins": sum(group["pair_margin"] > 0 for group in groups),
            "draws": sum(group["pair_margin"] == 0 for group in groups),
            "losses": sum(group["pair_margin"] < 0 for group in groups),
        },
    }
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("SUMMARY " + json.dumps(payload["summary"], sort_keys=True))
    print("OPPONENTS " + json.dumps(payload["opponent_paired_results"], sort_keys=True))
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
