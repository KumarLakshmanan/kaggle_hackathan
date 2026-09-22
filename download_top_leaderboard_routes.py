"""Download compact action tapes from current public Kaggriculture leaders.

This utility is intentionally read-only with respect to Kaggle: it calls the
public ``team-submissions``/``episodes``/``replay`` endpoints and stores only
the selected team's 719 action frames plus provenance.  It never submits a
file.  The resulting ``summary.json`` is compatible with
``route_panel_benchmark.py``.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def _json_from_cli(stdout: str) -> Any:
    """Parse Kaggle JSON even when the CLI prefixes a pagination line."""
    text = stdout.strip()
    first = min((i for i in (text.find("["), text.find("{")) if i >= 0), default=-1)
    if first < 0:
        raise ValueError(f"Kaggle did not return JSON: {text[:200]!r}")
    return json.loads(text[first:])


def _run_json(kaggle: str, args: list[str]) -> Any:
    completed = subprocess.run(
        [kaggle, *args, "--format", "json", "--quiet"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return _json_from_cli(completed.stdout)


def _number(value: Any, default: float = float("-inf")) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return value[:80] or "team"


def _load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8-sig")
    return _json_from_cli(text)


def _select_submissions(
    leaderboard: list[dict[str, Any]],
    submissions: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for standing in leaderboard[: max(1, limit)]:
        team_id = int(standing["teamId"])
        team_rows = [row for row in submissions if int(row["TeamId"]) == team_id]
        if not team_rows:
            continue
        best = max(
            team_rows,
            key=lambda row: (
                _number(row.get("PublicScore")),
                str(row.get("Submitted", "")),
            ),
        )
        selected.append(
            {
                "team_id": team_id,
                "team": str(standing["teamName"]),
                "leaderboard_score": _number(standing.get("score"), 0.0),
                "submission_id": int(best["SubmissionId"]),
                "public_score": _number(best.get("PublicScore"), 0.0),
            }
        )
    return selected


def _write_route(
    output: Path,
    replay: dict[str, Any],
    leader: dict[str, Any],
    episode: dict[str, Any],
) -> dict[str, Any]:
    info = replay.get("info", {}) or {}
    names = list(info.get("TeamNames", []) or [])
    team = leader["team"]
    if team not in names:
        raise ValueError(f"team {team!r} not present in TeamNames={names!r}")
    seat = names.index(team)
    steps = list(replay.get("steps", []) or [])
    actions = [step[seat].get("action", {}) for step in steps[1:]]
    if len(actions) != 719:
        raise ValueError(
            f"episode {episode['id']} has {len(actions)} decisions; expected 719"
        )
    digest = hashlib.sha256(
        json.dumps(actions, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    path = output / (
        f"{_safe(team)}-submission-{leader['submission_id']}-"
        f"episode-{int(episode['id'])}-seat{seat}.json.gz"
    )
    rewards = [float(value or 0.0) for value in replay.get("rewards", [0, 0])]
    opponent = names[1 - seat] if len(names) == 2 else ""
    payload = {
        "actions": actions,
        "metadata": {
            "episode_id": int(episode["id"]),
            "team": team,
            "opponent": opponent,
            "source_seat": seat,
            "seed": int(info.get("seed", 0) or 0),
            "submission_id": leader["submission_id"],
            "team_id": leader["team_id"],
            "leaderboard_score": leader["leaderboard_score"],
            "public_score": leader["public_score"],
            "team_reward": rewards[seat] if seat < len(rewards) else 0.0,
            "opponent_reward": rewards[1 - seat] if len(rewards) == 2 else 0.0,
            "action_sha256": digest,
        },
    }
    with path.open("wb") as raw_handle:
        with gzip.GzipFile(
            fileobj=raw_handle, mode="wb", compresslevel=9, mtime=0
        ) as gzip_handle:
            with io.TextIOWrapper(gzip_handle, encoding="utf-8") as handle:
                json.dump(payload, handle, separators=(",", ":"))
    return {
        "path": str(path.resolve()),
        "episode_id": int(episode["id"]),
        "team": team,
        "source_seat": seat,
        "seed": int(info.get("seed", 0) or 0),
        "submission_id": leader["submission_id"],
        "team_id": leader["team_id"],
        "leaderboard_score": leader["leaderboard_score"],
        "public_score": leader["public_score"],
        "action_sha256": digest,
        "num_actions": len(actions),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kaggle", required=True)
    parser.add_argument("--competition", default="kaggriculture")
    parser.add_argument("--leaderboard-json", type=Path, required=True)
    parser.add_argument("--submissions-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top-teams", type=int, default=10)
    parser.add_argument("--episodes-per-team", type=int, default=3)
    args = parser.parse_args()

    leaderboard = list(_load(args.leaderboard_json))
    submissions = list(_load(args.submissions_json))
    leaders = _select_submissions(leaderboard, submissions, args.top_teams)
    if not leaders:
        raise RuntimeError("No leaderboard team had a public submission in the manifest")

    args.output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for index, leader in enumerate(leaders, start=1):
        episodes = list(
            _run_json(
                args.kaggle,
                ["competitions", "episodes", str(leader["submission_id"])],
            )
        )
        public = [
            episode
            for episode in episodes
            if "PUBLIC" in str(episode.get("type", "")).upper()
            and "COMPLETED" in str(episode.get("state", "")).upper()
        ]
        public.sort(key=lambda episode: str(episode.get("createTime", "")), reverse=True)
        chosen = public[: max(1, args.episodes_per_team)]
        print(
            f"[{index:02d}/{len(leaders):02d}] {leader['team']} "
            f"submission={leader['submission_id']} episodes={len(chosen)}",
            flush=True,
        )
        for episode in chosen:
            with tempfile.TemporaryDirectory(prefix="kaggriculture-top-replay-") as temporary:
                subprocess.run(
                    [
                        args.kaggle,
                        "competitions",
                        "replay",
                        str(int(episode["id"])),
                        "-p",
                        temporary,
                        "-q",
                    ],
                    check=True,
                )
                replay_paths = list(Path(temporary).glob("*.json"))
                if len(replay_paths) != 1:
                    raise RuntimeError(
                        f"Expected one replay for {episode['id']}, found {replay_paths}"
                    )
                replay = json.loads(replay_paths[0].read_text(encoding="utf-8"))
            try:
                row = _write_route(args.output, replay, leader, episode)
            except ValueError as error:
                print(f"skip episode={episode['id']}: {error}", flush=True)
                continue
            rows.append(row)
            print(
                f"  extracted episode={row['episode_id']} seed={row['seed']} "
                f"seat={row['source_seat']} hash={row['action_sha256'][:12]}",
                flush=True,
            )

    rows.sort(key=lambda row: (row["team"], row["episode_id"]))
    summary = args.output / "summary.json"
    summary.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "leaders": len(leaders),
                "routes_written": len(rows),
                "unique_action_hashes": len({row["action_sha256"] for row in rows}),
                "summary": str(summary.resolve()),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
