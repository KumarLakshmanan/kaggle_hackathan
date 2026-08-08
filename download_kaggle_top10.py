#!/usr/bin/env python3
"""Download one current public replay for each top Kaggriculture team.

The selected submission is the team's highest public-score submission.  The
selected episode is its newest completed public episode.  A manifest records
the live leaderboard snapshot and every selected identifier so the corpus is
auditable and can be refreshed later.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


COMPETITION = "kaggriculture"


def kaggle_json(kaggle: Path, *args: str) -> list[dict[str, Any]]:
    output = subprocess.check_output([str(kaggle), *args, "--format", "json"], text=True)
    json_start = output.find("[")
    if json_start < 0:
        raise ValueError(f"Kaggle returned no JSON for {' '.join(args)}: {output[:200]!r}")
    value, _ = json.JSONDecoder().raw_decode(output[json_start:])
    if not isinstance(value, list):
        raise TypeError(f"Expected a JSON list from {' '.join(args)}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kaggle", type=Path, default=Path(".venv/bin/kaggle"))
    parser.add_argument("--output", type=Path, default=Path("best_replay/top10_raw"))
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument(
        "--teams-from",
        type=Path,
        help="Reuse the ranked team snapshot from an existing replay manifest",
    )
    parser.add_argument(
        "--require-win",
        action="store_true",
        help="Walk newest episodes until the selected team has a strict win",
    )
    args = parser.parse_args()

    if args.teams_from:
        snapshot = json.loads(args.teams_from.read_text())[: args.limit]
        leaderboard = [
            {
                "teamId": row["teamId"],
                "teamName": row["teamName"],
                "score": row["leaderboardScore"],
            }
            for row in snapshot
        ]
    else:
        leaderboard = kaggle_json(
            args.kaggle,
            "competitions",
            "leaderboard",
            "-c",
            COMPETITION,
            "--show",
            "--page-size",
            str(max(args.limit, 20)),
        )[: args.limit]
    args.output.mkdir(parents=True, exist_ok=True)
    selections: list[dict[str, Any]] = []

    for rank, team in enumerate(leaderboard, 1):
        team_id = str(team["teamId"])
        submissions = kaggle_json(args.kaggle, "competitions", "team-submissions", team_id)
        scored = [row for row in submissions if row.get("publicScore") not in (None, "")]
        if not scored:
            raise RuntimeError(f"Team {team_id} has no scored submission")
        submission = max(scored, key=lambda row: float(row["publicScore"]))
        episodes = kaggle_json(args.kaggle, "competitions", "episodes", str(submission["id"]))
        completed_public = [
            row
            for row in episodes
            if row.get("state") == "EpisodeState.COMPLETED"
            and row.get("type") == "EpisodeType.EPISODE_TYPE_PUBLIC"
        ]
        if not completed_public:
            raise RuntimeError(f"Submission {submission['id']} has no completed public episode")
        completed_public.sort(key=lambda row: row.get("createTime", ""), reverse=True)
        episode: dict[str, Any] | None = None
        expected: Path | None = None
        cache_dir = args.output.parent / "top10_raw"
        for candidate in completed_public:
            episode_id = int(candidate["id"])
            filename = f"episode-{episode_id}-replay.json"
            cached = next(
                (path for path in (args.output / filename, cache_dir / filename) if path.exists()),
                None,
            )
            if cached is not None:
                replay = json.loads(cached.read_text())
            else:
                with tempfile.TemporaryDirectory(prefix="kaggriculture-replay-") as temp:
                    subprocess.run(
                        [
                            str(args.kaggle),
                            "competitions",
                            "replay",
                            str(episode_id),
                            "-p",
                            temp,
                            "-q",
                        ],
                        check=True,
                    )
                    downloaded = Path(temp) / filename
                    replay = json.loads(downloaded.read_text())
                    if not args.require_win:
                        shutil.copy2(downloaded, args.output / filename)
            names = replay.get("info", {}).get("TeamNames", [])
            rewards = replay.get("rewards", [])
            try:
                seat = names.index(team.get("teamName"))
            except ValueError:
                continue
            won = len(rewards) == 2 and rewards[seat] > rewards[1 - seat]
            if args.require_win and not won:
                continue
            expected = args.output / filename
            if not expected.exists():
                if cached is not None:
                    shutil.copy2(cached, expected)
                else:
                    # The temporary download was removed above; fetch the selected replay once.
                    subprocess.run(
                        [
                            str(args.kaggle),
                            "competitions",
                            "replay",
                            str(episode_id),
                            "-p",
                            str(args.output),
                            "-q",
                        ],
                        check=True,
                    )
            episode = candidate
            break
        if episode is None or expected is None:
            raise RuntimeError(f"No qualifying public episode for submission {submission['id']}")
        episode_id = int(episode["id"])
        selections.append(
            {
                "rank": rank,
                "teamId": int(team_id),
                "teamName": team.get("teamName"),
                "leaderboardScore": team.get("score"),
                "submissionId": int(submission["id"]),
                "submissionScore": submission["publicScore"],
                "episodeId": episode_id,
                "episodeCreateTime": episode.get("createTime"),
                "replay": str(expected),
            }
        )
        print(f"#{rank:02d} {team.get('teamName')}: submission {submission['id']}, episode {episode_id}")

    manifest_name = "top10_winning_manifest.json" if args.require_win else "top10_manifest.json"
    manifest = args.output.parent / manifest_name
    manifest.write_text(json.dumps(selections, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {manifest}")


if __name__ == "__main__":
    main()
