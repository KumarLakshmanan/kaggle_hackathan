"""Run a candidate against local adaptive/online opponent agents."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path

from paired_benchmark import run_game


def _play(job: tuple[str, str, int, int]) -> dict:
    candidate, opponent, seed, seat = job
    row = run_game(
        candidate=candidate,
        opponent=opponent,
        seed=seed,
        candidate_seat=seat,
        debug=False,
        capture_step=None,
        candidate_overrides={},
    )
    row["opponent"] = opponent
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--opponents", nargs="+", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    jobs = [
        (str(Path(args.candidate).resolve()), str(path.resolve()), seed, seat)
        for path in args.opponents
        for seed in args.seeds
        for seat in (0, 1)
    ]
    rows = []
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=max(1, args.workers)
    ) as pool:
        for row in pool.map(_play, jobs):
            rows.append(row)
            print(
                f"opponent={Path(row['opponent']).name} seed={row['seed']} "
                f"seat={row['candidate_seat']} margin={row['margin']:+.0f} "
                f"result={row['result']}",
                flush=True,
            )

    summaries = {}
    for opponent in sorted({row["opponent"] for row in rows}):
        subset = [row for row in rows if row["opponent"] == opponent]
        margins = [float(row["margin"]) for row in subset]
        paired = {}
        for row in subset:
            paired.setdefault(int(row["seed"]), 0.0)
            paired[int(row["seed"])] += float(row["margin"])
        summaries[opponent] = {
            "games": len(subset),
            "wins": sum(m > 0 for m in margins),
            "draws": sum(m == 0 for m in margins),
            "losses": sum(m < 0 for m in margins),
            "paired_wins": sum(m > 0 for m in paired.values()),
            "paired_draws": sum(m == 0 for m in paired.values()),
            "paired_losses": sum(m < 0 for m in paired.values()),
            "mean_margin": sum(margins) / len(margins) if margins else 0.0,
            "paired_margins": paired,
        }

    payload = {
        "candidate": str(Path(args.candidate).resolve()),
        "seeds": args.seeds,
        "opponents": [str(path.resolve()) for path in args.opponents],
        "rows": rows,
        "summaries": summaries,
    }
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("SUMMARIES " + json.dumps(summaries, sort_keys=True))
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()

