"""Freeze the live top 50 and fetch one verified public route per team.

Read-only Kaggle API workflow. No submission endpoint is used.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from refresh_top_leaderboard_routes import _write_route  # noqa: E402

LEADERBOARD = HERE / "leaderboard_snapshot.json"
META = HERE / "snapshot_meta.json"
ROUTES = HERE / "routes"
SUMMARY = ROUTES / "summary.json"
ERRORS = HERE / "fetch_errors.json"


def call(args: list[str], *, json_output: bool = True) -> object:
    command = [sys.executable, "-m", "kaggle", *args]
    if json_output:
        command += ["--format", "json", "-q"]
    else:
        command += ["-q"]
    process = subprocess.run(command, capture_output=True, text=True,
                             encoding="utf8", errors="replace")
    if process.returncode:
        raise RuntimeError(f"Kaggle command failed: {args[:4]}: {process.stderr[:400]}")
    if not json_output:
        return process.stdout
    output = process.stdout
    starts = [index for index in (output.find("["), output.find("{")) if index >= 0]
    if not starts:
        raise RuntimeError(f"No JSON in Kaggle response: {args[:4]}")
    return json.loads(output[min(starts):])


def snapshot() -> list[dict]:
    if LEADERBOARD.is_file():
        teams = json.loads(LEADERBOARD.read_text(encoding="utf8"))
        if len(teams) != 50:
            raise RuntimeError(f"Existing snapshot has {len(teams)} teams")
        return teams
    teams = call(["competitions", "leaderboard", "kaggriculture", "-s",
                  "--page-size", "50"])
    if not isinstance(teams, list) or len(teams) != 50:
        raise RuntimeError(f"Expected 50 leaderboard rows, got {len(teams)}")
    LEADERBOARD.write_text(json.dumps(teams, ensure_ascii=False, indent=2), encoding="utf8")
    META.write_text(json.dumps({
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "competition": "kaggriculture", "requested_ranks": [1, 50],
        "leaderboard_sha256": hashlib.sha256(LEADERBOARD.read_bytes()).hexdigest(),
    }, indent=2), encoding="utf8")
    return teams


def choose_submission(team: dict, submissions: list[dict]) -> tuple[dict, str]:
    # The leaderboard may display the better of a team's recent submissions,
    # while submissionDate points to the latest one. Match the frozen score.
    score = float(team["score"])
    numeric = [item for item in submissions if item.get("publicScore") is not None]
    if not numeric:
        raise RuntimeError("No scored submission")
    best = min(numeric, key=lambda item: (abs(float(item["publicScore"]) - score),
                                           -int(item["id"])))
    return best, "nearest_snapshot_score"


def fetch_route(team: dict, rank: int, selected: dict, method: str) -> dict:
    team_id = int(team["teamId"])
    name = str(team["teamName"])
    submission_id = int(selected["id"])
    episodes = call(["competitions", "episodes", str(submission_id)])
    public = [row for row in episodes
              if "PUBLIC" in str(row.get("type", ""))
              and str(row.get("state", "")).endswith("COMPLETED")]
    public.sort(key=lambda row: str(row.get("createTime", "")), reverse=True)
    if not public:
        raise RuntimeError("No completed public episode")
    last_error = None
    for episode in public[:3]:
        try:
            episode_id = int(episode["id"])
            with tempfile.TemporaryDirectory(prefix="kaggriculture-top50-") as temporary:
                call(["competitions", "replay", str(episode_id), "-p", temporary],
                     json_output=False)
                paths = list(Path(temporary).glob("*.json"))
                if len(paths) != 1:
                    raise RuntimeError(f"Expected one replay JSON, found {len(paths)}")
                replay = json.loads(paths[0].read_text(encoding="utf8"))
            if replay.get("statuses") != ["DONE", "DONE"]:
                raise RuntimeError(f"Replay statuses {replay.get('statuses')}")
            row = _write_route(ROUTES, name, team_id, submission_id, episode, replay)
            row.update({"rank": rank, "leaderboard_score": team.get("score"),
                        "leaderboard_submission_date": team.get("submissionDate"),
                        "selected_submission_score": selected.get("publicScore"),
                        "submission_selection": method})
            return row
        except Exception as exc:
            last_error = str(exc)
    raise RuntimeError(f"First three completed public replays failed: {last_error}")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf8", errors="replace")
    except AttributeError:
        pass
    teams = snapshot()
    ROUTES.mkdir(parents=True, exist_ok=True)
    rows = json.loads(SUMMARY.read_text(encoding="utf8")) if SUMMARY.is_file() else []
    by_id = {int(row["team_id"]): row for row in rows}
    errors = json.loads(ERRORS.read_text(encoding="utf8")) if ERRORS.is_file() else []
    for rank, team in enumerate(teams, start=1):
        team_id = int(team["teamId"])
        try:
            submissions = call(["competitions", "team-submissions", str(team_id)])
            selected, method = choose_submission(team, submissions)
            if (team_id in by_id
                    and int(by_id[team_id]["submission_id"]) == int(selected["id"])
                    and Path(by_id[team_id]["path"]).is_file()):
                row = by_id[team_id]
                row.update({"rank": rank, "leaderboard_score": team.get("score"),
                            "leaderboard_submission_date": team.get("submissionDate"),
                            "selected_submission_score": selected.get("publicScore"),
                            "submission_selection": method})
                print(f"[{rank:02d}/50] cached {team['teamName']}", flush=True)
            else:
                row = fetch_route(team, rank, selected, method)
                print(f"[{rank:02d}/50] updated {row['team']} episode={row['episode_id']}", flush=True)
            by_id[team_id] = row
            rows = [by_id[int(item["teamId"])] for item in teams
                    if int(item["teamId"]) in by_id]
            SUMMARY.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf8")
        except Exception as exc:
            errors.append({"rank": rank, "team": team.get("teamName"),
                           "team_id": team_id, "error": str(exc)})
            ERRORS.write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf8")
            print(f"[{rank:02d}/50] ERROR {team['teamName']}: {exc}", flush=True)
    print(json.dumps({"teams": len(teams), "routes": len(by_id),
                      "distinct_actions": len({row["action_sha256"] for row in by_id.values()}),
                      "errors": len(errors), "summary": str(SUMMARY)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
