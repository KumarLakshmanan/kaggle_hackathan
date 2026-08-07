"""Search compatible replay-derived books against routes a baseline loses to."""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import json
from pathlib import Path
from typing import Any

from paired_benchmark import run_game


def _actions(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)["actions"]


def _play(job: tuple[str, str, int, int, str, str]) -> dict[str, Any]:
    candidate, opponent, seed, seat, target_key, candidate_key = job
    row = run_game(candidate, opponent, seed, seat, False, None, {})
    row["target_key"] = target_key
    row["candidate_key"] = candidate_key
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    panel = json.loads(args.panel.read_text(encoding="utf-8"))
    targets = [row for row in panel["rows"] if float(row["pair_margin"]) < 0]
    entries = json.loads(args.summary.read_text(encoding="utf-8"))

    unique_entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        digest = str(entry["action_sha256"])
        if digest in seen:
            continue
        seen.add(digest)
        item = dict(entry)
        item["absolute_path"] = str(Path(entry["path"]).resolve())
        item["opening"] = _actions(Path(item["absolute_path"]))[0]
        unique_entries.append(item)

    jobs: list[tuple[str, str, int, int, str, str]] = []
    metadata: dict[tuple[str, str], dict[str, Any]] = {}
    for target in targets:
        target_path = Path(target["opponent_path"]).resolve()
        target_key = target_path.name
        opening = _actions(target_path)[0]
        for entry in unique_entries:
            if entry["opening"] != opening:
                continue
            candidate_key = Path(entry["absolute_path"]).name
            metadata[(target_key, candidate_key)] = entry
            for seat in (0, 1):
                jobs.append(
                    (
                        f"v26-route:{entry['absolute_path']}",
                        f"route:{target_path}",
                        int(target["seed"]),
                        seat,
                        target_key,
                        candidate_key,
                    )
                )

    rows: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(_play, jobs):
            rows.append(row)

    results: list[dict[str, Any]] = []
    for target in targets:
        target_key = Path(target["opponent_path"]).name
        candidates = []
        for (key, candidate_key), entry in metadata.items():
            if key != target_key:
                continue
            games = [
                row
                for row in rows
                if row["target_key"] == target_key
                and row["candidate_key"] == candidate_key
            ]
            candidates.append(
                {
                    "episode_id": entry["episode_id"],
                    "source_seat": entry["source_seat"],
                    "team": entry["team"],
                    "path": entry["absolute_path"],
                    "pair_margin": sum(float(game["margin"]) for game in games),
                    "games": games,
                }
            )
        candidates.sort(key=lambda row: row["pair_margin"], reverse=True)
        result = {
            "target": target,
            "candidates": candidates,
            "winning_candidates": sum(row["pair_margin"] > 0 for row in candidates),
        }
        results.append(result)
        best = candidates[0]
        print(
            f"target={target_key} winners={result['winning_candidates']}/{len(candidates)} "
            f"best={best['pair_margin']:+.0f} {Path(best['path']).name}",
            flush=True,
        )

    payload = {"targets": results, "jobs": len(jobs)}
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
