"""Capture compact public branch signals for the downloaded route panel.

Local analysis helper only.  It never submits or changes a production agent.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path
from typing import Any

from paired_benchmark import run_game


def _play(job: tuple[str, str, int, int, int]) -> dict[str, Any]:
    candidate, opponent_path, seed, seat, capture_step = job
    result = run_game(
        candidate=candidate,
        opponent=f"rawroute:{opponent_path}",
        seed=seed,
        candidate_seat=seat,
        debug=False,
        capture_step=capture_step,
        candidate_overrides={},
    )
    capture = result.get("candidate_capture") or {}
    farms = capture.get("farms") or []
    mine = farms[seat] if seat < len(farms) else {}
    other = farms[1 - seat] if len(farms) > 1 else {}
    return {
        "seed": seed,
        "seat": seat,
        "capture_step": capture_step,
        "episode_id": None,
        "path": opponent_path,
        "shops": capture.get("shops", []),
        "prices": capture.get("prices", {}),
        "mine_money": mine.get("money", 0),
        "opponent_money": other.get("money", 0),
        "mine_hands": mine.get("hands", 0),
        "opponent_hands": other.get("hands", 0),
        "mine_land": mine.get("land", 0),
        "opponent_land": other.get("land", 0),
        "mine_weeds": mine.get("weeds", 0),
        "opponent_weeds": other.get("weeds", 0),
        "mine_counts": mine.get("counts", {}),
        "opponent_counts": other.get("counts", {}),
        "mine_occupied": mine.get("occupied", []),
        "opponent_occupied": other.get("occupied", []),
        "margin": result.get("margin"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", default="main_v43_current.py")
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--steps", nargs="+", type=int, default=[88, 153])
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=None,
        help="Optional deterministic route seeds to capture; defaults to the full panel.",
    )
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    entries = json.loads(args.summary.read_text(encoding="utf-8"))
    selected_seeds = set(args.seeds or [])
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        if selected_seeds and int(entry["seed"]) not in selected_seeds:
            continue
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
            step,
        )
        for entry in unique
        for seat in (0, 1)
        for step in args.steps
    ]
    by_path = {str(Path(entry["path"]).resolve()): entry for entry in unique}
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for row in pool.map(_play, jobs):
            row["episode_id"] = by_path[row["path"]]["episode_id"]
            row["team"] = by_path[row["path"]]["team"]
            rows.append(row)
            print(
                f"seed={row['seed']} seat={row['seat']} step={row['capture_step']} "
                f"shops={row['shops']} me={row['mine_money']:.0f} "
                f"op={row['opponent_money']:.0f}",
                flush=True,
            )

    rows.sort(key=lambda row: (int(row["seed"]), int(row["seat"]), int(row["capture_step"])))
    args.json_out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"wrote={args.json_out}")


if __name__ == "__main__":
    main()
