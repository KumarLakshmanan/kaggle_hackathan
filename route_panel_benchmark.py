"""Run a candidate against every unique route in an extracted replay panel."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
from typing import Any

from kaggle_environments import __version__ as engine_version
from paired_benchmark import run_game, summarize


def _play(
    job: tuple[str, str, int, int, int | None, str | None, str | None, str | None, str | None, dict[str, Any]]
) -> dict[str, Any]:
    candidate, opponent_path, seed, seat, capture_step, forced_route, forced_book, rank90_yarn, h6_demand_rank, extra_overrides = job
    row = run_game(
        candidate=candidate,
        opponent=f"rawroute:{opponent_path}",
        seed=seed,
        candidate_seat=seat,
        debug=False,
        capture_step=capture_step,
        candidate_overrides={
            **({"_FORCED_ROUTE": forced_route} if forced_route else {}),
            **({"_FORCE_BOOK": forced_book} if forced_book else {}),
            **({"_EARLY_YARN_ENABLED": rank90_yarn == "on"} if rank90_yarn else {}),
            **({"ENABLE_H6_DEMAND_RANK": h6_demand_rank == "on"} if h6_demand_rank else {}),
            **extra_overrides,
        },
    )
    row["opponent_path"] = opponent_path
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=None,
        help="Optional deterministic route seeds to benchmark; defaults to the full panel.",
    )
    parser.add_argument(
        "--limit-routes",
        type=int,
        default=0,
        help="Use N evenly spaced routes after action/seed/source-seat deduplication.",
    )
    parser.add_argument(
        "--route-slice",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        help="Use half-open [START, END) route positions after action/seed/source-seat deduplication.",
    )
    parser.add_argument("--capture-step", type=int)
    parser.add_argument("--forced-route", choices=("hozuma", "qq", "tetsuya"))
    parser.add_argument(
        "--forced-book",
        choices=("primary", "alternate", "thunder", "aastik", "seb202", "seb210"),
    )
    parser.add_argument("--rank90-yarn", choices=("on", "off"))
    parser.add_argument("--h6-demand-rank", choices=("on", "off"))
    parser.add_argument(
        "--candidate-override", action="append", default=[], metavar="NAME=JSON",
        help="Override a candidate module setting; repeat for multiple settings.",
    )
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    extra_overrides: dict[str, Any] = {}
    for raw in args.candidate_override:
        if "=" not in raw:
            parser.error(f"invalid candidate override {raw!r}; expected NAME=JSON")
        name, value = raw.split("=", 1)
        if not name or name in extra_overrides:
            parser.error(f"empty or duplicate candidate override name: {name!r}")
        try:
            extra_overrides[name] = json.loads(value)
        except json.JSONDecodeError:
            extra_overrides[name] = value

    entries = json.loads(args.summary.read_text(encoding="utf-8"))
    selected_seeds = set(args.seeds or [])
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for entry in entries:
        if selected_seeds and int(entry["seed"]) not in selected_seeds:
            continue
        # Identical action tapes can produce different games under different
        # simulator seeds.  Keep each physical seed/seat route in the panel.
        identity = (
            str(entry["action_sha256"]),
            int(entry["seed"]),
            int(entry.get("source_seat", -1)),
        )
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(entry)

    if args.route_slice is not None:
        start, end = args.route_slice
        if start < 0 or end < start:
            parser.error("route-slice must be a nonnegative half-open range")
        unique = unique[start:end]

    if args.limit_routes > 0 and len(unique) > args.limit_routes:
        if args.limit_routes == 1:
            unique = [unique[len(unique) // 2]]
        else:
            last = len(unique) - 1
            indices = [
                round(index * last / (args.limit_routes - 1))
                for index in range(args.limit_routes)
            ]
            unique = [unique[index] for index in indices]

    jobs = [
        (
            args.candidate,
            str(Path(entry["path"]).resolve()),
            int(entry["seed"]),
            seat,
            args.capture_step,
            args.forced_route,
            args.forced_book,
            args.rank90_yarn,
            args.h6_demand_rank,
            extra_overrides,
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
        "candidate_sha256": hashlib.sha256(Path(args.candidate).resolve().read_bytes()).hexdigest(),
        "summary_source": str(args.summary.resolve()),
        "summary_sha256": hashlib.sha256(args.summary.resolve().read_bytes()).hexdigest(),
        "engine_version": engine_version,
        "selection": {
            "seeds": sorted(selected_seeds) if selected_seeds else None,
            "limit_routes": args.limit_routes,
            "route_slice": args.route_slice,
            "capture_step": args.capture_step,
        },
        "candidate_settings": {
            **({"rank90_early_yarn": args.rank90_yarn} if args.rank90_yarn else {}),
            **({"h6_demand_rank": args.h6_demand_rank} if args.h6_demand_rank else {}),
            **({"forced_route": args.forced_route} if args.forced_route else {}),
            **({"forced_book": args.forced_book} if args.forced_book else {}),
            **({"candidate_overrides": extra_overrides} if extra_overrides else {}),
        },
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
