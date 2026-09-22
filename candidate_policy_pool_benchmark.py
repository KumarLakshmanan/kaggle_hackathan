"""Benchmark a selected pool of extracted Kaggle agent sources."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from paired_benchmark import run_game


ROOT = Path(__file__).resolve().parent


def _key(row):
    path = str(row.get("opponent_path") or row.get("path") or "")
    route = Path(path)
    if not route.is_absolute():
        route = ROOT / route
    return str(route.resolve()), int(row.get("seed", 0))


def _entries(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, list):
        source_rows = payload
    elif "rows" in payload:
        source_rows = payload["rows"]
    else:
        source_rows = payload.get("loss_routes", [])
    seen = set()
    result = []
    for row in source_rows:
        route, seed = _key(row)
        if (route, seed) in seen:
            continue
        seen.add((route, seed))
        result.append({"route": route, "seed": seed, "team": row.get("team")})
    return result


def _candidates(manifests: list[Path], ranks: set[int]):
    by_digest = {}
    for manifest in manifests:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        for row in payload.get("agents", []):
            if row.get("status") != "extracted":
                continue
            notebook_value = row.get("notebook") or row.get("source") or ""
            notebook = Path(notebook_value)
            rank_value = row.get("rank")
            if rank_value is not None:
                try:
                    rank = int(rank_value)
                except (TypeError, ValueError):
                    continue
            else:
                try:
                    rank = int(notebook.parts[-2].split("-", 1)[0])
                except (IndexError, ValueError):
                    continue
            if ranks and rank not in ranks:
                continue
            source_value = row.get("source_path") or row.get("path") or row.get("source")
            if not source_value:
                continue
            source = Path(source_value)
            if not source.is_absolute():
                source = ROOT / source
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            by_digest.setdefault(digest, {
                "rank": rank,
                "source": str(source.resolve()),
                "notebook": str(notebook),
            })
    return sorted(by_digest.values(), key=lambda row: (row["rank"], row["source"]))


def _play(job):
    candidate, route, seed, seat = job
    try:
        row = run_game(
            candidate=candidate,
            opponent=f"rawroute:{route}",
            seed=seed,
            candidate_seat=seat,
            debug=False,
            capture_step=None,
            candidate_overrides={},
        )
        return {**row, "candidate": candidate, "opponent_path": route}
    except Exception as error:  # noqa: BLE001 - preserve pool progress
        return {
            "candidate": candidate,
            "opponent_path": route,
            "seed": seed,
            "candidate_seat": seat,
            "error": f"{type(error).__name__}: {error}",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        action="append",
        required=True,
        help="Agent manifest to include; repeat for additional extracted corpora.",
    )
    parser.add_argument("--ranks", nargs="*", type=int, default=[])
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--limit-routes",
        type=int,
        default=0,
        help="Use N evenly spaced routes from the deterministic input panel.",
    )
    parser.add_argument(
        "--loss-only",
        action="store_true",
        help="When input is a paired-panel benchmark JSON, keep only routes the incumbent lost.",
    )
    args = parser.parse_args()
    candidates = _candidates(args.manifest, set(args.ranks))
    routes = _entries(args.input)
    if args.loss_only:
        payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
        rows = payload.get("rows", []) if isinstance(payload, dict) else []
        margins: dict[tuple[str, int], float] = {}
        for row in rows:
            key = (str(Path(row.get("opponent_path", "")).resolve()), int(row.get("seed", 0)))
            value = row.get("pair_margin")
            if value is None:
                value = row.get("margin", 0)
            margins[key] = margins.get(key, 0.0) + float(value or 0)
        lost = {key for key, margin in margins.items() if margin < 0}
        routes = [route for route in routes if (route["route"], route["seed"]) in lost]
    if args.limit_routes > 0:
        if len(routes) > args.limit_routes:
            if args.limit_routes == 1:
                routes = [routes[len(routes) // 2]]
            else:
                last = len(routes) - 1
                indices = [round(i * last / (args.limit_routes - 1)) for i in range(args.limit_routes)]
                routes = [routes[index] for index in indices]
    jobs = [
        (candidate["source"], route["route"], route["seed"], seat)
        for candidate in candidates
        for route in routes
        for seat in (0, 1)
    ]
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for index, row in enumerate(pool.map(_play, jobs), 1):
            rows.append(row)
            if index % 50 == 0:
                print(f"completed={index}/{len(jobs)}", flush=True)

    groups = []
    for candidate in candidates:
        cr = [row for row in rows if row.get("candidate") == candidate["source"] and "margin" in row]
        margins = [float(row["margin"]) for row in cr]
        paired = {}
        for row in cr:
            paired.setdefault((row["opponent_path"], int(row["seed"])), 0.0)
            paired[(row["opponent_path"], int(row["seed"]))] += float(row["margin"])
        groups.append({
            **candidate,
            "games": len(cr),
            "errors": sum(row.get("candidate") == candidate["source"] and "error" in row for row in rows),
            "wins": sum(value > 0 for value in margins),
            "losses": sum(value < 0 for value in margins),
            "mean_margin": sum(margins) / len(margins) if margins else None,
            "paired_wins": sum(value > 0 for value in paired.values()),
            "paired_losses": sum(value < 0 for value in paired.values()),
            "paired_mean_margin": sum(paired.values()) / len(paired) if paired else None,
        })
    groups.sort(key=lambda row: (row["paired_wins"], row["paired_mean_margin"] or float("-inf")), reverse=True)
    payload = {"input": str(args.input), "candidates": candidates, "groups": groups, "rows": rows}
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for group in groups:
        mean_text = (
            f"{group['paired_mean_margin']:+.0f}"
            if group["paired_mean_margin"] is not None
            else "n/a"
        )
        print(
            f"rank={group['rank']:03d} games={group['games']} errors={group['errors']} "
            f"wins={group['wins']} losses={group['losses']} "
            f"paired={group['paired_wins']}/{group['paired_wins'] + group['paired_losses']} "
            f"mean={mean_text}",
            flush=True,
        )
    print(f"wrote={args.output}")


if __name__ == "__main__":
    main()
