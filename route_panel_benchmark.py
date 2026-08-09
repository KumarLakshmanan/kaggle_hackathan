"""Run a candidate against every unique route in an extracted replay panel."""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import json
from pathlib import Path
from typing import Any

from paired_benchmark import run_game, summarize


def _play(job: tuple[str, str, int, int, int | None, dict[str, Any]]) -> dict[str, Any]:
    candidate, opponent_path, seed, seat, capture_step, candidate_overrides = job
    row = run_game(
        candidate=candidate,
        opponent=f"route:{opponent_path}",
        seed=seed,
        candidate_seat=seat,
        debug=False,
        capture_step=capture_step,
        candidate_overrides=candidate_overrides,
    )
    row["opponent_path"] = opponent_path
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--summary", type=Path, nargs="+", required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument(
        "--seats",
        type=int,
        nargs="+",
        choices=(0, 1),
        default=[0, 1],
        help="Candidate seats to run (default: both; use one seat for a fast screen)",
    )
    parser.add_argument("--capture-step", type=int)
    parser.add_argument(
        "--candidate-override",
        action="append",
        default=[],
        metavar="NAME=JSON",
        help="Override a candidate module setting after import",
    )
    parser.add_argument(
        "--losses-from",
        type=Path,
        help="Restrict the summary to routes with negative pair margins in a prior panel",
    )
    parser.add_argument(
        "--episode-ids",
        type=int,
        nargs="+",
        help="Restrict the panel to the listed replay episode IDs",
    )
    parser.add_argument(
        "--opening-hires",
        type=int,
        choices=range(0, 13),
        help="Restrict opponents to routes buying this many workers on turn zero",
    )
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    candidate_overrides: dict[str, Any] = {}
    for raw in args.candidate_override:
        if "=" not in raw:
            parser.error(f"Invalid override {raw!r}; expected NAME=JSON")
        name, value = raw.split("=", 1)
        try:
            candidate_overrides[name] = json.loads(value)
        except json.JSONDecodeError:
            candidate_overrides[name] = value

    entries = []
    for summary_path in args.summary:
        entries.extend(json.loads(summary_path.read_text(encoding="utf-8")))
    if args.episode_ids:
        episode_ids = set(args.episode_ids)
        entries = [
            entry for entry in entries if int(entry["episode_id"]) in episode_ids
        ]
    if args.opening_hires is not None:
        filtered = []
        for entry in entries:
            with gzip.open(Path(entry["path"]), "rt", encoding="utf-8") as handle:
                opening = (json.load(handle).get("actions", [{}]) or [{}])[0]
            hires = sum(
                bool(order) and order[0] == "HIRE"
                for order in opening.get("market", []) or []
            )
            if hires == args.opening_hires:
                filtered.append(entry)
        entries = filtered
    if args.losses_from:
        prior = json.loads(args.losses_from.read_text(encoding="utf-8"))
        losing_digests = {
            str(row["action_sha256"])
            for row in prior["rows"]
            if float(row["pair_margin"]) < 0
        }
        entries = [entry for entry in entries if str(entry["action_sha256"]) in losing_digests]
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
            candidate_overrides,
        )
        for entry in unique
        for seat in args.seats
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
                "team": entry.get("team", entry.get("opponent_team", "unknown")),
                "source_seat": entry.get("source_seat"),
                "seed": entry["seed"],
                "action_sha256": entry["action_sha256"],
                "opponent_path": opponent_path,
                "games": games,
                "pair_margin": sum(float(row["margin"]) for row in games),
            }
        )

    payload = {
        "candidate": str(Path(args.candidate).resolve()),
        "summary_source": [str(path.resolve()) for path in args.summary],
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
