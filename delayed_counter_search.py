"""Search turn-144-compatible action books for the remaining V31 losses."""

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
    parser.add_argument("--summary", type=Path, nargs="+", required=True)
    parser.add_argument(
        "--candidate-path",
        type=Path,
        action="append",
        help="Only screen these action books (repeatable); defaults to every compatible book",
    )
    parser.add_argument(
        "--target-episode",
        type=int,
        action="append",
        help="Only screen losing routes from these episodes (repeatable)",
    )
    parser.add_argument(
        "--target-source-seat",
        type=int,
        choices=(0, 1),
        help="Restrict targets to the replay source seat",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path("best_replay/routes/episode-90631991-seat1.json.gz"),
    )
    parser.add_argument("--switch-prefix", default="v32-switch")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    panel = json.loads(args.panel.read_text(encoding="utf-8"))
    targets = [row for row in panel["rows"] if float(row["pair_margin"]) < 0]
    if args.target_episode:
        allowed_episodes = set(args.target_episode)
        targets = [row for row in targets if int(row["episode_id"]) in allowed_episodes]
    if args.target_source_seat is not None:
        targets = [
            row for row in targets
            if int(row.get("source_seat", -1)) == args.target_source_seat
        ]
    summary = []
    for summary_path in args.summary:
        summary.extend(json.loads(summary_path.read_text(encoding="utf-8")))
    reference = _actions(args.reference)
    requested_paths = (
        {str(path.resolve()) for path in args.candidate_path}
        if args.candidate_path
        else None
    )

    candidates = []
    seen = set()
    for entry in summary:
        if entry["action_sha256"] in seen:
            continue
        seen.add(entry["action_sha256"])
        path = Path(entry["path"]).resolve()
        if requested_paths is not None and str(path) not in requested_paths:
            continue
        actions = _actions(path)
        workers_match = all(
            (left.get("farmer"), left.get("hands"))
            == (right.get("farmer"), right.get("hands"))
            for left, right in zip(reference[:144], actions[:144])
        )
        if workers_match:
            candidates.append({**entry, "absolute_path": str(path)})

    jobs = []
    for target in targets:
        target_path = str(Path(target["opponent_path"]).resolve())
        target_key = Path(target_path).name
        for candidate in candidates:
            candidate_key = Path(candidate["absolute_path"]).name
            for seat in (0, 1):
                jobs.append(
                    (
                        f"{args.switch_prefix}:{candidate['absolute_path']}",
                        f"route:{target_path}",
                        int(target["seed"]),
                        seat,
                        target_key,
                        candidate_key,
                    )
                )

    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(_play, jobs):
            rows.append(row)

    output = []
    for target in targets:
        target_key = Path(target["opponent_path"]).name
        ranked = []
        for candidate in candidates:
            candidate_key = Path(candidate["absolute_path"]).name
            games = [
                row for row in rows
                if row["target_key"] == target_key and row["candidate_key"] == candidate_key
            ]
            ranked.append(
                {
                    "path": candidate["absolute_path"],
                    "episode_id": candidate["episode_id"],
                    "source_seat": candidate["source_seat"],
                    "team": candidate["team"],
                    "pair_margin": sum(float(game["margin"]) for game in games),
                    "games": games,
                }
            )
        ranked.sort(key=lambda row: row["pair_margin"], reverse=True)
        output.append({"target": target, "candidates": ranked})
        best = ranked[0]
        print(
            f"target={target_key} best={best['pair_margin']:+.0f} "
            f"book={Path(best['path']).name}",
            flush=True,
        )

    args.json_out.write_text(json.dumps({"targets": output}, indent=2), encoding="utf-8")
    print(f"candidates={len(candidates)} jobs={len(jobs)} wrote={args.json_out}")


if __name__ == "__main__":
    main()
