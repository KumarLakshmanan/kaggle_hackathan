"""Extract deterministic, compact action routes from saved replay JSON files."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
from typing import Any


def _digest(actions: list[dict[str, Any]]) -> str:
    payload = json.dumps(actions, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def extract(replay_path: Path, destination: Path, seats: list[int]) -> list[dict[str, Any]]:
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    names = list(replay.get("info", {}).get("TeamNames", []))
    rewards = list(replay.get("rewards", [0, 0]))
    episode_id = int(replay.get("info", {}).get("EpisodeId") or replay_path.stem)
    rows: list[dict[str, Any]] = []
    destination.mkdir(parents=True, exist_ok=True)

    for seat in seats:
        actions = [
            frame[seat].get("action")
            or {"farmer": ["PASS"], "hands": [], "market": []}
            for frame in replay["steps"][1:]
        ]
        metadata = {
            "episode_id": episode_id,
            "seed": replay.get("info", {}).get("seed"),
            "team": names[seat],
            "source_seat": seat,
            "reward": rewards[seat],
            "action_count": len(actions),
            "action_sha256": _digest(actions),
        }
        output = destination / f"episode-{episode_id}-seat{seat}.json.gz"
        with output.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as zipped:
                with io.TextIOWrapper(zipped, encoding="utf-8") as text:
                    json.dump(
                        {"metadata": metadata, "actions": actions},
                        text,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
        metadata["path"] = str(output.resolve())
        rows.append(metadata)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("replays", nargs="+", type=Path)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--seats", nargs="+", type=int, choices=(0, 1), default=[0, 1])
    parser.add_argument(
        "--exclude-team",
        action="append",
        default=[],
        help="Drop extracted seats whose team name exactly matches this value",
    )
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for replay in args.replays:
        rows.extend(extract(replay.resolve(), args.destination.resolve(), args.seats))
    excluded = set(args.exclude_team)
    rows = [row for row in rows if row.get("team") not in excluded]
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"routes={len(rows)} summary={args.summary.resolve()}")


if __name__ == "__main__":
    main()
