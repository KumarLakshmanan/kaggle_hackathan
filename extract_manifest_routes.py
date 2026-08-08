#!/usr/bin/env python3
"""Extract exactly the team/seat associated with each replay manifest row."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from extract_local_replay_routes import extract


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    routes: list[dict[str, object]] = []
    seen: set[tuple[int, int]] = set()
    for row in manifest:
        replay_path = Path(row["replay"])
        replay = json.loads(replay_path.read_text())
        names = replay.get("info", {}).get("TeamNames", [])
        try:
            seat = names.index(row["teamName"])
        except ValueError as exc:
            raise RuntimeError(f"{row['teamName']!r} is not in {replay_path}: {names}") from exc
        key = (int(row["episodeId"]), seat)
        if key in seen:
            continue
        seen.add(key)
        extracted = extract(replay_path.resolve(), args.destination.resolve(), [seat])
        for route in extracted:
            route.update(
                {
                    "leaderboard_rank": row["rank"],
                    "leaderboard_score": row["leaderboardScore"],
                    "submission_id": row["submissionId"],
                }
            )
        routes.extend(extracted)

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(routes, indent=2, ensure_ascii=False) + "\n")
    print(f"routes={len(routes)} summary={args.summary.resolve()}")


if __name__ == "__main__":
    main()
