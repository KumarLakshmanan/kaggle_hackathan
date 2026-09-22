"""Benchmark extracted replay books as candidate policies against a panel."""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import json
from pathlib import Path
from typing import Any

from paired_benchmark import run_game


def _play(job: tuple[str, str, int, int]) -> dict[str, Any]:
    candidate_path, opponent_path, seed, seat = job
    row = run_game(
        candidate=f"rawroute:{candidate_path}",
        opponent=f"rawroute:{opponent_path}",
        seed=seed,
        candidate_seat=seat,
        debug=False,
        capture_step=None,
        candidate_overrides={},
    )
    row["candidate_path"] = candidate_path
    row["opponent_path"] = opponent_path
    return row


def _unique(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for entry in entries:
        digest = str(entry["action_sha256"])
        if digest in seen:
            continue
        seen.add(digest)
        out.append(entry)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--opponents", type=Path, required=True)
    parser.add_argument("--opponent-seeds", nargs="*", type=int)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()
    candidate_entries = _unique(json.loads(args.candidates.read_text(encoding="utf-8")))
    opponent_entries = _unique(json.loads(args.opponents.read_text(encoding="utf-8")))
    if args.opponent_seeds:
        wanted = set(args.opponent_seeds)
        opponent_entries = [x for x in opponent_entries if int(x["seed"]) in wanted]
    jobs = []
    for candidate in candidate_entries:
        candidate_path = str(Path(candidate["path"]).resolve())
        for opponent in opponent_entries:
            opponent_path = str(Path(opponent["path"]).resolve())
            seed = int(opponent["seed"])
            for seat in (0, 1):
                jobs.append((candidate_path, opponent_path, seed, seat))

    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for row in pool.map(_play, jobs):
            rows.append(row)
    candidate_meta = {str(Path(x["path"]).resolve()): x for x in candidate_entries}
    opponent_meta = {str(Path(x["path"]).resolve()): x for x in opponent_entries}
    groups = []
    for cpath, cmeta in candidate_meta.items():
        cr = [row for row in rows if row["candidate_path"] == cpath]
        margins = [float(row["margin"]) for row in cr]
        by_opp = {}
        for row in cr:
            by_opp.setdefault(row["opponent_path"], 0.0)
            by_opp[row["opponent_path"]] += float(row["margin"])
        groups.append(
            {
                "candidate_episode_id": cmeta.get("episode_id"),
                "candidate_team": cmeta.get("team"),
                "candidate_path": cpath,
                "games": len(cr),
                "wins": sum(v > 0 for v in margins),
                "losses": sum(v < 0 for v in margins),
                "mean_margin": sum(margins) / len(margins) if margins else None,
                "paired_wins": sum(v > 0 for v in by_opp.values()),
                "paired_losses": sum(v < 0 for v in by_opp.values()),
                "paired_mean_margin": sum(by_opp.values()) / len(by_opp) if by_opp else None,
                "opponents": [
                    {
                        "episode_id": opponent_meta[path].get("episode_id"),
                        "team": opponent_meta[path].get("team"),
                        "path": path,
                        "pair_margin": margin,
                    }
                    for path, margin in sorted(by_opp.items())
                ],
            }
        )
    payload = {"groups": sorted(groups, key=lambda x: x["paired_mean_margin"], reverse=True)}
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for group in payload["groups"]:
        print(
            f"candidate={group['candidate_episode_id']} team={group['candidate_team']} "
            f"paired={group['paired_wins']}/{group['paired_wins'] + group['paired_losses']} "
            f"mean={group['paired_mean_margin']:+.0f}",
            flush=True,
        )
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
