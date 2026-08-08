"""Screen every unique compatible replay route against one target opponent."""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import json
from pathlib import Path

from paired_benchmark import run_game


def _actions(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)["actions"]


def _play(job):
    candidate, opponent, seed, seat = job
    row = run_game(candidate, opponent, seed, seat, False, None, {})
    row["candidate_spec"] = candidate
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, nargs="+", required=True)
    parser.add_argument("--opening-reference", type=Path, required=True)
    parser.add_argument("--opponent", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--candidate-prefix", default="v26-route")
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    opening = _actions(args.opening_reference)[0]
    entries = []
    for summary_path in args.summary:
        entries.extend(json.loads(summary_path.read_text(encoding="utf-8")))
    candidates = []
    seen = set()
    for entry in entries:
        digest = entry["action_sha256"]
        path = Path(entry["path"]).resolve()
        if digest in seen or _actions(path)[0] != opening:
            continue
        seen.add(digest)
        candidates.append(entry)

    jobs = [
        (f"{args.candidate_prefix}:{Path(entry['path']).resolve()}", args.opponent, args.seed, seat)
        for entry in candidates
        for seat in (0, 1)
    ]
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(_play, jobs):
            rows.append(row)

    groups = []
    for entry in candidates:
        spec = f"{args.candidate_prefix}:{Path(entry['path']).resolve()}"
        games = [row for row in rows if row["candidate_spec"] == spec]
        groups.append(
            {
                "episode_id": entry["episode_id"],
                "source_seat": entry["source_seat"],
                "team": entry["team"],
                "path": entry["path"],
                "games": games,
                "pair_margin": sum(row["margin"] for row in games),
            }
        )
    groups.sort(key=lambda group: group["pair_margin"], reverse=True)
    args.json_out.write_text(json.dumps({"rows": groups}, indent=2), encoding="utf-8")
    for group in groups:
        print(
            f"margin={group['pair_margin']:+.0f} episode={group['episode_id']} "
            f"seat={group['source_seat']} team={group['team']}",
            flush=True,
        )
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
