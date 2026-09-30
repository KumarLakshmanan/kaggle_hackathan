"""Download current top-team public replays for local Kaggriculture tests.

Read-only utility.  It calls leaderboard/team-submissions/episodes/replay and
never invokes the Kaggle submission endpoint.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def _run_json(kaggle: str, args: list[str]) -> Any:
    completed = subprocess.run(
        [kaggle, *args, "--format", "json", "-q"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    # The CLI may print a pagination token before the JSON body even with -q.
    output = completed.stdout
    starts = [index for index in (output.find("["), output.find("{")) if index >= 0]
    if not starts:
        raise RuntimeError(f"No JSON body returned for {' '.join(args)}: {output[:500]}")
    return json.loads(output[min(starts):])


def _safe(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value)).strip("-")
    return result[:80] or "team"


def _score(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")


def _write_route(
    output_dir: Path,
    team_name: str,
    team_id: int,
    submission_id: int,
    episode: dict[str, Any],
    replay: dict[str, Any],
) -> dict[str, Any]:
    info = replay.get("info", {}) or {}
    names = list(info.get("TeamNames", []) or [])
    if team_name not in names:
        raise RuntimeError(f"{team_name!r} not found in TeamNames={names!r} for episode {episode['id']}")
    seat = names.index(team_name)
    steps = list(replay.get("steps", []) or [])
    actions = [
        frame[seat].get("action") or {"farmer": ["PASS"], "hands": [], "market": []}
        for frame in steps[1:]
    ]
    if len(actions) != 719:
        raise RuntimeError(f"Episode {episode['id']} has {len(actions)} actions for {team_name}; expected 719")
    digest = hashlib.sha256(
        json.dumps(actions, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    route_name = f"{_safe(team_name)}-submission-{submission_id}-episode-{int(episode['id'])}-seat{seat}.json.gz"
    route_path = output_dir / route_name
    payload = {
        "actions": actions,
        "metadata": {
            "team": team_name,
            "team_id": team_id,
            "submission_id": submission_id,
            "episode_id": int(episode["id"]),
            "create_time": episode.get("createTime"),
            "end_time": episode.get("endTime"),
            "seed": info.get("seed"),
            "seat": seat,
            "team_names": names,
            "action_sha256": digest,
            "engine_version": replay.get("module_version"),
        },
    }
    with gzip.open(route_path, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"))
    return {
        "path": str(route_path.resolve()),
        "team": team_name,
        "team_id": team_id,
        "submission_id": submission_id,
        "episode_id": int(episode["id"]),
        "create_time": episode.get("createTime"),
        "seed": info.get("seed"),
        "source_seat": seat,
        "num_actions": len(actions),
        "action_sha256": digest,
    }


def main() -> None:
    # Windows PowerShell may expose a cp1252 stdout even though leaderboard
    # team names contain emoji/non-Latin characters.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser()
    parser.add_argument("--kaggle", required=True)
    parser.add_argument("--leaderboard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--top-teams", type=int, default=20)
    parser.add_argument(
        "--start-rank",
        type=int,
        default=1,
        help="One-based leaderboard rank to begin downloading (useful for extending an existing panel).",
    )
    parser.add_argument("--episodes-per-team", type=int, default=3)
    args = parser.parse_args()

    raw = args.leaderboard.read_text(encoding="utf-8-sig")
    start = min(index for index in (raw.find("["), raw.find("{")) if index >= 0)
    leaderboard = json.loads(raw[start:])
    start = max(0, int(args.start_rank) - 1)
    teams = leaderboard[start : start + max(1, int(args.top_teams))]
    args.output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for rank, team in enumerate(teams, start=max(1, int(args.start_rank))):
        team_id = int(team["teamId"])
        team_name = str(team["teamName"])
        submissions = _run_json(args.kaggle, ["competitions", "team-submissions", str(team_id)])
        public_submissions = [item for item in submissions if _score(item.get("publicScore")) > float("-inf")]
        if not public_submissions:
            print(f"[{rank:02d}] {team_name}: no public submissions", flush=True)
            continue
        selected = max(public_submissions, key=lambda item: (_score(item.get("publicScore")), str(item.get("dateSubmitted", ""))))
        submission_id = int(selected["id"])
        episodes = _run_json(args.kaggle, ["competitions", "episodes", str(submission_id)])
        public = [item for item in episodes if "PUBLIC" in str(item.get("type", "")) and str(item.get("state", "")).endswith("COMPLETED")]
        public.sort(key=lambda item: str(item.get("createTime", "")), reverse=True)
        chosen = public[: max(1, int(args.episodes_per_team))]
        print(
            f"[{rank:02d}] {team_name} score={team.get('score')} submission={submission_id} episodes={len(chosen)}",
            flush=True,
        )
        for episode in chosen:
            episode_id = int(episode["id"])
            with tempfile.TemporaryDirectory(prefix="kaggriculture-top-replay-") as temporary:
                subprocess.run(
                    [args.kaggle, "competitions", "replay", str(episode_id), "-p", temporary, "-q"],
                    check=True,
                )
                replay_paths = list(Path(temporary).glob("*.json"))
                if len(replay_paths) != 1:
                    raise RuntimeError(f"Expected one replay for {episode_id}, found {replay_paths}")
                replay = json.loads(replay_paths[0].read_text(encoding="utf-8"))
            rows.append(_write_route(args.output, team_name, team_id, submission_id, episode, replay))
            print(f"  downloaded episode={episode_id}", flush=True)

    rows.sort(key=lambda row: (str(row.get("create_time", "")), row["team"], row["episode_id"]), reverse=True)
    summary = args.output / "summary.json"
    summary.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "teams_requested": len(teams),
        "start_rank": max(1, int(args.start_rank)),
        "routes_written": len(rows),
        "unique_action_hashes": len({row["action_sha256"] for row in rows}),
        "summary": str(summary.resolve()),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
