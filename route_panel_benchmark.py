"""Run a candidate against every unique route in an extracted replay panel."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path
from typing import Any

from paired_benchmark import run_game, summarize


def _play(job: tuple[str, str, int, int, int | None]) -> dict[str, Any]:
    candidate, opponent_path, seed, seat, capture_step = job
    row = run_game(
        candidate=candidate,
        opponent=f"route:{opponent_path}",
        seed=seed,
        candidate_seat=seat,
        debug=False,
        capture_step=capture_step,
        candidate_overrides={},
    )
    row["opponent_path"] = opponent_path
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--capture-step", type=int)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    entries = json.loads(args.summary.read_text(encoding="utf-8"))
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        digest = str(entry["action_sha256"])
        if digest in seen:
            continue
        seen.add(digest)
        unique.append(entry)

    jobs = [
        (
            args.candidate,
            str(Path(entry["path"]).resolve()),
            int(entry["seed"]),
            seat,
            args.capture_step,
        )
        for entry in unique
        for seat in (0, 1)
    ]
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(_play, job): job for job in jobs}
        for future in concurrent.futures.as_completed(futures):
            row = future.result()
            rows.append(row)
            print(
                f"seed={row['seed']} seat={row['candidate_seat']} "
                f"margin={row['margin']:+.0f} result={row['result']} "
                f"route={Path(row['opponent_path']).name}",
                flush=True,
            )

    rows.sort(key=lambda row: (row["opponent_path"], row["candidate_seat"]))
    entry_by_path = {str(Path(entry["path"]).resolve()): entry for entry in unique}
    groups = []
    for opponent_path in sorted(entry_by_path):
        games = [row for row in rows if row["opponent_path"] == opponent_path]
        entry = entry_by_path[opponent_path]
        groups.append(
            {
                "episode_id": entry["episode_id"],
                "team": entry["team"],
                "source_seat": entry["source_seat"],
                "seed": entry["seed"],
                "action_sha256": entry["action_sha256"],
                "opponent_path": opponent_path,
                "games": games,
                "pair_margin": sum(float(row["margin"]) for row in games),
            }
        )

    payload = {
        "candidate": str(Path(args.candidate).resolve()),
        "summary_source": str(args.summary.resolve()),
        "unique_routes": len(unique),
        "rows": groups,
        "summary": summarize(rows),
        "route_paired_results": {
            "wins": sum(group["pair_margin"] > 0 for group in groups),
            "draws": sum(group["pair_margin"] == 0 for group in groups),
            "losses": sum(group["pair_margin"] < 0 for group in groups),
        },
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("SUMMARY " + json.dumps(payload["summary"], sort_keys=True))
    print("ROUTES " + json.dumps(payload["route_paired_results"], sort_keys=True))
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
