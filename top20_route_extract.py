"""Extract replay actions into the route format used by paired benchmarks.

The Kaggle replay JSON contains an initial state frame followed by one action
frame for each player at every engine step.  The local benchmark's route proxy
expects the 719 decision frames, so the initial state frame is intentionally
excluded here.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any


def _canonical_digest(actions: list[dict[str, Any]]) -> str:
    encoded = json.dumps(actions, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _replay_path(root: Path, source: str, filename: str) -> Path:
    path = root / source / filename
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replays", type=Path, default=Path("top20_replays"))
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("mined_top20_routes_summary.json"),
        help="Rows with source/file/seat fields; defaults to the selected 30-route panel.",
    )
    parser.add_argument("--output", type=Path, default=Path("top20_routes_2026-09-21"))
    parser.add_argument(
        "--all",
        action="store_true",
        help="Extract all seat-specific rows in mined_top20_summary.json instead of the selected panel.",
    )
    args = parser.parse_args()

    summary_path = (
        Path("mined_top20_summary.json")
        if args.all
        else args.summary
    )
    entries = json.loads(summary_path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise TypeError(f"Expected a list in {summary_path}")

    args.output.mkdir(parents=True, exist_ok=True)
    replay_cache: dict[Path, dict[str, Any]] = {}
    output_entries: list[dict[str, Any]] = []
    for entry in entries:
        source = str(entry["source"])
        filename = str(entry["file"])
        # The mined summary uses ``seat``; the later route-panel summaries
        # use ``source_seat``.  Accept both so every downloaded replay can be
        # re-extracted with the same 1.32.7-compatible path.
        seat = int(entry.get("seat", entry.get("source_seat")))
        replay_file = _replay_path(args.replays, source, filename)
        replay = replay_cache.get(replay_file)
        if replay is None:
            replay = json.loads(replay_file.read_text(encoding="utf-8"))
            replay_cache[replay_file] = replay

        steps = replay.get("steps", [])
        if len(steps) < 2:
            raise ValueError(f"Replay has too few steps: {replay_file}")
        actions = [step[seat]["action"] for step in steps[1:]]
        if len(actions) != 719:
            raise ValueError(f"Expected 719 actions in {replay_file}, found {len(actions)}")

        info = replay.get("info", {})
        episode_id = int(info.get("EpisodeId", 0))
        seed = int(info["seed"])
        digest = _canonical_digest(actions)
        route_file = args.output / f"episode-{episode_id}-seat{seat}.json.gz"
        payload = {
            "actions": actions,
            "metadata": {
                "episode_id": episode_id,
                "source": source,
                "file": filename,
                "seat": seat,
                "seed": seed,
                "score": float(entry.get("score", 0.0)),
                "action_sha256": digest,
            },
        }
        with gzip.open(route_file, "wt", encoding="utf-8") as handle:
            json.dump(payload, handle, separators=(",", ":"))
        output_entries.append(
            {
                "path": str(route_file.resolve()),
                "episode_id": episode_id,
                "team": (info.get("TeamNames") or [source])[seat],
                "source_seat": seat,
                "source": source,
                "file": filename,
                "seed": seed,
                "score": float(entry.get("score", 0.0)),
                "num_actions": len(actions),
                "action_sha256": digest,
            }
        )

    summary_out = args.output / "summary.json"
    summary_out.write_text(json.dumps(output_entries, indent=2), encoding="utf-8")
    print(json.dumps({
        "summary": str(summary_out.resolve()),
        "entries": len(output_entries),
        "unique_action_hashes": len({item["action_sha256"] for item in output_entries}),
        "replays_loaded": len(replay_cache),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
