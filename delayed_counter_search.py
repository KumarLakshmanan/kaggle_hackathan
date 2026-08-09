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


def _play(
    job: tuple[str, str, int, int, str, str, int | None, dict[str, Any]]
) -> dict[str, Any]:
    (
        candidate, opponent, seed, seat, target_key, candidate_key,
        capture_step, candidate_overrides,
    ) = job
    row = run_game(
        candidate, opponent, seed, seat, False, capture_step, candidate_overrides
    )
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
        "--opening-hires",
        type=int,
        choices=range(0, 13),
        help="Restrict targets to opponents buying this many workers on turn zero",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path("best_replay/routes/episode-90631991-seat1.json.gz"),
    )
    parser.add_argument(
        "--no-opening-filter",
        action="store_true",
        help="Screen complete books even when their first 144 worker moves differ",
    )
    parser.add_argument(
        "--opening-steps",
        type=int,
        default=144,
        help="Number of initial actions required to match the reference",
    )
    parser.add_argument(
        "--match-market",
        action="store_true",
        help="Include market orders in the opening compatibility check",
    )
    parser.add_argument(
        "--per-team-limit",
        type=int,
        help="Keep at most this many highest-reward unique books per source team",
    )
    parser.add_argument("--switch-prefix", default="v32-switch")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--capture-step",
        type=int,
        help="Capture candidate public state immediately before this decision turn",
    )
    parser.add_argument(
        "--seats",
        type=int,
        nargs="+",
        choices=(0, 1),
        default=[0, 1],
        help="Candidate seats to screen (default: both)",
    )
    parser.add_argument(
        "--candidate-override",
        action="append",
        default=[],
        metavar="NAME=JSON",
        help="Override a candidate module setting after import",
    )
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help="Persist completed games so a long search can be resumed",
    )
    args = parser.parse_args()

    candidate_overrides: dict[str, Any] = {}
    for raw in args.candidate_override:
        if "=" not in raw:
            parser.error(f"invalid override {raw!r}; expected NAME=JSON")
        name, value = raw.split("=", 1)
        try:
            candidate_overrides[name] = json.loads(value)
        except json.JSONDecodeError:
            candidate_overrides[name] = value

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
    if args.opening_hires is not None:
        targets = [
            row for row in targets
            if sum(
                bool(order) and order[0] == "HIRE"
                for order in _actions(Path(row["opponent_path"]))[0].get("market", []) or []
            ) == args.opening_hires
        ]
    summary = []
    for summary_path in args.summary:
        summary.extend(json.loads(summary_path.read_text(encoding="utf-8")))
    reference = None if args.no_opening_filter else _actions(args.reference)
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
        workers_match = reference is None or all(
            (
                left.get("farmer"),
                left.get("hands"),
                left.get("market") if args.match_market else None,
            )
            == (
                right.get("farmer"),
                right.get("hands"),
                right.get("market") if args.match_market else None,
            )
            for left, right in zip(
                reference[: max(0, args.opening_steps)],
                actions[: max(0, args.opening_steps)],
            )
        )
        if workers_match:
            candidates.append({**entry, "absolute_path": str(path)})
    candidates.sort(
        key=lambda row: float(row.get("reward", 0.0) or 0.0),
        reverse=True,
    )
    if args.per_team_limit:
        kept = []
        team_counts: dict[str, int] = {}
        for candidate in candidates:
            team = str(candidate.get("team", "unknown"))
            if team_counts.get(team, 0) >= args.per_team_limit:
                continue
            team_counts[team] = team_counts.get(team, 0) + 1
            kept.append(candidate)
        candidates = kept

    rows = []
    if args.checkpoint and args.checkpoint.exists():
        rows = json.loads(args.checkpoint.read_text(encoding="utf-8")).get("rows", [])
    completed = {
        (str(row["target_key"]), str(row["candidate_key"]), int(row["candidate_seat"]))
        for row in rows
    }
    jobs = []
    for candidate in candidates:
        candidate_key = Path(candidate["absolute_path"]).name
        for target in targets:
            target_path = str(Path(target["opponent_path"]).resolve())
            target_key = Path(target_path).name
            candidate_key = Path(candidate["absolute_path"]).name
            for seat in args.seats:
                if (target_key, candidate_key, seat) in completed:
                    continue
                jobs.append(
                    (
                        f"{args.switch_prefix}:{candidate['absolute_path']}",
                        f"route:{target_path}",
                        int(target["seed"]),
                        seat,
                        target_key,
                        candidate_key,
                        args.capture_step,
                        candidate_overrides,
                    )
                )

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for index, row in enumerate(pool.map(_play, jobs), start=1):
            rows.append(row)
            if args.checkpoint and (index % 10 == 0 or index == len(jobs)):
                args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
                args.checkpoint.write_text(
                    json.dumps({"rows": rows}, separators=(",", ":")),
                    encoding="utf-8",
                )

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
