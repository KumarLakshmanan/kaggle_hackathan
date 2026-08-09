#!/usr/bin/env python3
"""Stream the 20 newest public games for each live top-10 team.

Only compact action routes are retained. Full replay JSONs are intentionally
not accumulated: ten teams x twenty games can exceed the local disk budget.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


COMPETITION = "kaggriculture"
PASS = {"farmer": ["PASS"], "hands": [], "market": []}


def kaggle_json(kaggle: Path, *args: str) -> list[dict[str, Any]]:
    output = subprocess.check_output([str(kaggle), *args, "--format", "json"], text=True)
    start = output.find("[")
    if start < 0:
        raise ValueError(f"No JSON returned for {' '.join(args)}")
    value, _ = json.JSONDecoder().raw_decode(output[start:])
    if not isinstance(value, list):
        raise TypeError(f"Expected list for {' '.join(args)}")
    return value


def write_route(
    destination: Path, replay: dict[str, Any], seat: int, episode_id: int
) -> dict[str, Any]:
    names = list(replay.get("info", {}).get("TeamNames", []))
    rewards = [float(v or 0.0) for v in replay.get("rewards", [0.0, 0.0])]
    actions = [frame[seat].get("action") or PASS for frame in replay.get("steps", [])[1:]]
    canonical = json.dumps(actions, sort_keys=True, separators=(",", ":")).encode()
    metadata = {
        "episode_id": episode_id,
        "seed": replay.get("info", {}).get("seed"),
        "team": names[seat],
        "source_seat": seat,
        "reward": rewards[seat],
        "opponent_team": names[1 - seat],
        "opponent_reward": rewards[1 - seat],
        "team_margin": rewards[seat] - rewards[1 - seat],
        "action_count": len(actions),
        "action_sha256": hashlib.sha256(canonical).hexdigest(),
    }
    payload = {"metadata": metadata, "actions": actions}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8") as text:
                json.dump(payload, text, sort_keys=True, separators=(",", ":"))
    metadata["path"] = str(destination.resolve())
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kaggle", type=Path, default=Path(".venv/bin/kaggle"))
    parser.add_argument("--output", type=Path, default=Path("best_replay/top10_recent20"))
    parser.add_argument("--games", type=int, default=20)
    args = parser.parse_args()

    leaderboard = kaggle_json(
        args.kaggle,
        "competitions",
        "leaderboard",
        "-c",
        COMPETITION,
        "--show",
        "--page-size",
        "20",
    )[:10]
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "leaderboard_snapshot.json").write_text(
        json.dumps(leaderboard, indent=2, ensure_ascii=False) + "\n"
    )

    team_rows: list[dict[str, Any]] = []
    selected_by_episode: dict[int, list[dict[str, Any]]] = {}
    for rank, team in enumerate(leaderboard, 1):
        team_id = str(team["teamId"])
        submissions = kaggle_json(args.kaggle, "competitions", "team-submissions", team_id)
        scored = [row for row in submissions if row.get("publicScore") not in (None, "")]
        submission = max(scored, key=lambda row: float(row["publicScore"]))
        episodes = [
            row
            for row in kaggle_json(args.kaggle, "competitions", "episodes", str(submission["id"]))
            if row.get("state") == "EpisodeState.COMPLETED"
            and row.get("type") == "EpisodeType.EPISODE_TYPE_PUBLIC"
        ]
        episodes.sort(key=lambda row: row.get("createTime", ""), reverse=True)
        chosen = episodes[: args.games]
        for index, episode in enumerate(chosen, 1):
            selected_by_episode.setdefault(int(episode["id"]), []).append(
                {
                    "rank": rank,
                    "teamId": int(team_id),
                    "teamName": team.get("teamName"),
                    "leaderboardScore": team.get("score"),
                    "submissionId": int(submission["id"]),
                    "submissionScore": submission["publicScore"],
                    "episodeId": int(episode["id"]),
                    "recencyIndex": index,
                }
            )

    # Resume safely when a previous run was interrupted.  Existing compact
    # routes are sufficient to populate the manifest; never retain full
    # replay JSONs in memory (a 200-game corpus can otherwise exceed RAM).
    existing_by_team: dict[tuple[int, str], dict[str, Any]] = {}
    for path in sorted((args.output / "routes").glob("*.json.gz")):
        try:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                metadata = dict(json.load(handle).get("metadata", {}))
            episode = int(metadata.get("episode_id"))
            team_name = str(metadata.get("team", ""))
            if team_name:
                metadata["path"] = str(path.resolve())
                existing_by_team[(episode, team_name)] = metadata
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue

    route_cache: dict[tuple[int, int], dict[str, Any]] = {}
    for episode_id, requests in selected_by_episode.items():
        missing: list[dict[str, Any]] = []
        for request in requests:
            cached = existing_by_team.get((episode_id, str(request["teamName"])))
            if cached is None:
                missing.append(request)
                continue
            request.update(cached)
            request["result"] = (
                "win"
                if float(cached.get("team_margin", 0.0)) > 0
                else "loss"
                if float(cached.get("team_margin", 0.0)) < 0
                else "draw"
            )
        if not missing:
            print(f"episode={episode_id} cached teams={len(requests)} routes={len(existing_by_team)}", flush=True)
            continue
        with tempfile.TemporaryDirectory(prefix="kaggriculture-recent20-") as temp:
            subprocess.run(
                [str(args.kaggle), "competitions", "replay", str(episode_id), "-p", temp, "-q"],
                check=True,
            )
            replay_path = next(Path(temp).glob("*.json"))
            replay = json.loads(replay_path.read_text(encoding="utf-8"))
        names = list(replay.get("info", {}).get("TeamNames", []))
        for request in missing:
            try:
                seat = names.index(request["teamName"])
            except ValueError:
                request["error"] = f"team absent from replay: {names}"
                continue
            key = (episode_id, seat)
            if key not in route_cache:
                path = args.output / "routes" / f"episode-{episode_id}-seat{seat}.json.gz"
                route_cache[key] = write_route(path, replay, seat, episode_id)
            request.update(route_cache[key])
            request["result"] = "win" if request["team_margin"] > 0 else "loss" if request["team_margin"] < 0 else "draw"
        print(f"episode={episode_id} teams={len(requests)} routes={len(route_cache)}", flush=True)

    manifest = args.output / "manifest.json"
    manifest.write_text(json.dumps([row for rows in selected_by_episode.values() for row in rows], indent=2, ensure_ascii=False) + "\n")
    print(f"teams={len(leaderboard)} requests={sum(len(v) for v in selected_by_episode.values())} unique_routes={len(route_cache)}")
    print(f"wrote={manifest}")


if __name__ == "__main__":
    main()
