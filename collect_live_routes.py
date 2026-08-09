"""Collect compact public action tapes from this team's Kaggle episodes."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def _run_json(command: list[str]) -> Any:
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    start = completed.stdout.find("[")
    if start < 0:
        raise ValueError(f"Kaggle returned no JSON: {completed.stdout[:200]!r}")
    return json.JSONDecoder().raw_decode(completed.stdout[start:])[0]


def _result(margin: float) -> str:
    return "win" if margin > 0 else "loss" if margin < 0 else "draw"


def collect_episode(
    kaggle: str,
    episode_id: int,
    own_team: str,
    output_dir: Path,
    failed_raw_dir: Path | None = None,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="kaggriculture-replay-") as temporary:
        subprocess.run(
            [
                kaggle,
                "competitions",
                "replay",
                str(episode_id),
                "-p",
                temporary,
                "-q",
            ],
            check=True,
        )
        replay_paths = list(Path(temporary).glob("*.json"))
        if len(replay_paths) != 1:
            raise RuntimeError(f"Expected one replay for {episode_id}, found {replay_paths}")
        raw_replay_bytes = replay_paths[0].read_bytes()
        replay = json.loads(raw_replay_bytes)

    names = list(replay.get("info", {}).get("TeamNames", []))
    try:
        own_seat = names.index(own_team)
    except ValueError as error:
        raise RuntimeError(f"Team {own_team!r} not present in episode {episode_id}: {names}") from error
    opponent_seat = 1 - own_seat
    rewards = [float(value or 0.0) for value in replay.get("rewards", [0, 0])]
    steps = list(replay.get("steps", []))
    actions = [
        frame[opponent_seat].get("action")
        or {"farmer": ["PASS"], "hands": [], "market": []}
        for frame in steps[1:]
    ]
    canonical_actions = json.dumps(actions, separators=(",", ":"), sort_keys=True).encode("utf-8")
    own_reward = rewards[own_seat]
    opponent_reward = rewards[opponent_seat]
    metadata = {
        "episode_id": episode_id,
        "seed": replay.get("info", {}).get("seed"),
        "own_team": own_team,
        "own_seat": own_seat,
        "own_reward": own_reward,
        "opponent_team": names[opponent_seat],
        "opponent_reward": opponent_reward,
        "margin": own_reward - opponent_reward,
        "result": _result(own_reward - opponent_reward),
        "statuses": replay.get("statuses", []),
        "engine_version": replay.get("module_version"),
        "frames": len(steps),
        "action_count": len(actions),
        "action_sha256": hashlib.sha256(canonical_actions).hexdigest(),
    }
    payload = {"metadata": metadata, "actions": actions}
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"episode-{episode_id}.json.gz"
    with destination.open("wb") as raw_handle:
        with gzip.GzipFile(
            fileobj=raw_handle, mode="wb", compresslevel=9, mtime=0
        ) as gzip_handle:
            with io.TextIOWrapper(gzip_handle, encoding="utf-8") as text_handle:
                json.dump(payload, text_handle, separators=(",", ":"), sort_keys=True)
    metadata["path"] = str(destination)
    metadata["compressed_bytes"] = destination.stat().st_size
    if failed_raw_dir is not None and metadata["result"] == "loss":
        failed_raw_dir.mkdir(parents=True, exist_ok=True)
        raw_destination = failed_raw_dir / f"episode-{episode_id}-replay.json"
        raw_destination.write_bytes(raw_replay_bytes)
        metadata["raw_replay"] = str(raw_destination)
    return metadata


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser()
    parser.add_argument("submission_id", type=int)
    parser.add_argument("--kaggle", required=True)
    parser.add_argument("--own-team", default="Lakshmanan R")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--failed-raw-dir",
        type=Path,
        help="Preserve the full replay JSON only when our team loses",
    )
    parser.add_argument("--limit", type=int, default=0, help="0 collects every public episode")
    args = parser.parse_args()

    episodes = _run_json(
        [
            args.kaggle,
            "competitions",
            "episodes",
            str(args.submission_id),
            "--format",
            "json",
            "-q",
        ]
    )
    public = [item for item in episodes if "PUBLIC" in str(item.get("type", ""))]
    if args.limit > 0:
        public = public[: args.limit]

    rows = []
    for index, episode in enumerate(public, start=1):
        episode_id = int(episode["id"])
        destination = args.output_dir / f"episode-{episode_id}.json.gz"
        if destination.exists():
            with gzip.open(destination, "rt", encoding="utf-8") as handle:
                row = json.load(handle)["metadata"]
            row["path"] = str(destination)
            row["compressed_bytes"] = destination.stat().st_size
        else:
            row = collect_episode(
                args.kaggle,
                episode_id,
                args.own_team,
                args.output_dir,
                args.failed_raw_dir,
            )
        rows.append(row)
        print(
            f"[{index:02d}/{len(public):02d}] episode={episode_id} "
            f"result={row['result']:4s} margin={row['margin']:+9.0f} "
            f"opponent={row['opponent_team']} route={row['action_sha256'][:12]}",
            flush=True,
        )

    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    counts = {name: sum(row["result"] == name for row in rows) for name in ("win", "draw", "loss")}
    print(f"summary={summary_path} results={counts}")


if __name__ == "__main__":
    main()
