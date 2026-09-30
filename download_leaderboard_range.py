"""Fetch public replay histories for a rank interval from a Kaggle snapshot.

This wrapper is read-only with respect to Kaggle. It downloads the selected
teams' public submission manifests and delegates episode/replay extraction to
``download_top_leaderboard_routes.py``.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from download_top_leaderboard_routes import _run_json


def _leaderboard_range(path: Path, rank_start: int, rank_end: int) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        rows = [
            {
                "rank": int(row["rank"]),
                "teamId": int(row["teamId"]),
                "teamName": str(row["teamName"]),
                "score": float(row["score"]),
            }
            for row in json.loads(path.read_text(encoding="utf-8"))
            if rank_start <= int(row["rank"]) <= rank_end
        ]
        rows.sort(key=lambda row: row["rank"])
        return rows
    with zipfile.ZipFile(path) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(f"Expected one leaderboard CSV in {path}, found {csv_names}")
        with archive.open(csv_names[0]) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            rows = [
                {
                    "rank": int(row["Rank"]),
                    "teamId": int(row["TeamId"]),
                    "teamName": str(row["TeamName"]),
                    "score": float(row["Score"]),
                }
                for row in csv.DictReader(text)
                if rank_start <= int(row["Rank"]) <= rank_end
            ]
    rows.sort(key=lambda row: row["rank"])
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kaggle", required=True)
    parser.add_argument("--leaderboard-zip", type=Path, required=True)
    parser.add_argument("--rank-start", type=int, required=True)
    parser.add_argument("--rank-end", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--competition", default="kaggriculture")
    parser.add_argument("--episodes-per-team", type=int, default=1)
    args = parser.parse_args()

    if args.rank_start < 1 or args.rank_end < args.rank_start:
        parser.error("rank range must be positive and ordered")
    leaders = _leaderboard_range(args.leaderboard_zip, args.rank_start, args.rank_end)
    if not leaders:
        raise RuntimeError("The requested rank range is absent from the leaderboard snapshot")

    args.output.mkdir(parents=True, exist_ok=True)
    leaderboard_snapshot = args.output / "leaderboard_snapshot.json"
    submissions_snapshot = args.output / "team_submissions_snapshot.json"
    can_resume = leaderboard_snapshot.is_file() and submissions_snapshot.is_file()
    if can_resume:
        saved_leaders = json.loads(leaderboard_snapshot.read_text(encoding="utf-8"))
        same_snapshot = [
            (int(row["rank"]), int(row["teamId"]), str(row["teamName"]), float(row["score"]))
            for row in saved_leaders
        ] == [
            (int(row["rank"]), int(row["teamId"]), str(row["teamName"]), float(row["score"]))
            for row in leaders
        ]
        if same_snapshot:
            leaders = saved_leaders
            submissions = json.loads(submissions_snapshot.read_text(encoding="utf-8"))
            print(
                f"reusing saved snapshots: {len(leaders)} teams, "
                f"{len(submissions)} public submissions",
                flush=True,
            )
        else:
            can_resume = False

    if not can_resume:
        submissions = []
        for index, leader in enumerate(leaders, start=1):
            try:
                public_rows = _run_json(
                    args.kaggle,
                    ["competitions", "team-submissions", str(leader["teamId"])],
                )
            except ValueError as error:
                if "No submissions found" not in str(error):
                    raise
                public_rows = []
            print(
                f"[{index:02d}/{len(leaders):02d}] rank={leader['rank']} "
                f"team_id={leader['teamId']} public_submissions={len(public_rows)}",
                flush=True,
            )
            for row in public_rows:
                submissions.append(
                    {
                        "TeamId": leader["teamId"],
                        "SubmissionId": int(row["id"]),
                        "PublicScore": row.get("publicScore", 0),
                        "Submitted": row.get("dateSubmitted", ""),
                    }
                )
        leaderboard_snapshot.write_text(
            json.dumps(leaders, indent=2), encoding="utf-8"
        )
        submissions_snapshot.write_text(
            json.dumps(submissions, indent=2), encoding="utf-8"
        )

    downloader = Path(__file__).resolve().with_name("download_top_leaderboard_routes.py")
    with tempfile.TemporaryDirectory(prefix="kaggriculture-rank-range-") as temp_name:
        temp = Path(temp_name)
        leaderboard_path = temp / "leaderboard.json"
        submissions_path = temp / "submissions.json"
        leaderboard_path.write_text(json.dumps(leaders), encoding="utf-8")
        submissions_path.write_text(json.dumps(submissions), encoding="utf-8")
        subprocess.run(
            [
                sys.executable,
                str(downloader),
                "--kaggle",
                args.kaggle,
                "--competition",
                args.competition,
                "--leaderboard-json",
                str(leaderboard_path),
                "--submissions-json",
                str(submissions_path),
                "--output",
                str(args.output.resolve()),
                "--top-teams",
                str(len(leaders)),
                "--episodes-per-team",
                str(max(1, args.episodes_per_team)),
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
