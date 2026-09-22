"""Extract compact action tapes for recent official top-team replays.

The maintained top-10 archive stores complete replay JSON bodies in Parquet.
This utility reads one body at a time, keeps only the selected team's 719
decision frames, and writes small gzip route files suitable for local paired
benchmarks.  It intentionally uses only replay metadata and public replay
contents; the resulting tapes are test fixtures, not runtime inputs for the
submitted agent.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq


def _digest(actions: list[dict[str, Any]]) -> str:
    payload = json.dumps(actions, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _leaderboard_teams(path: Path, limit: int) -> set[str]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: int(row.get("Rank", 10**9)))
    return {str(row["TeamName"]) for row in rows[:limit] if row.get("TeamName")}


def _select_metadata(
    rows: list[dict[str, Any]],
    teams: set[str],
    dates: set[str],
    per_team_date: int,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if str(row.get("date")) not in dates:
            continue
        if str(row.get("team_name")) not in teams:
            continue
        if int(row.get("daily_rank", 10**9) or 10**9) > 10:
            continue
        grouped[(str(row["date"]), str(row["team_name"]))].append(row)

    selected: list[dict[str, Any]] = []
    for key in sorted(grouped):
        candidates = sorted(
            grouped[key],
            key=lambda row: int(row.get("episode_id", 0) or 0),
            reverse=True,
        )
        seen_opponents: set[str] = set()
        chosen: list[dict[str, Any]] = []
        for row in candidates:
            opponent = str(row.get("opponent", ""))
            if opponent in seen_opponents and len(chosen) < per_team_date:
                continue
            chosen.append(row)
            seen_opponents.add(opponent)
            if len(chosen) >= per_team_date:
                break
        selected.extend(chosen)
    return selected


def _write_route(
    output: Path,
    replay: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    info = replay.get("info", {}) or {}
    names = list(info.get("TeamNames", []) or [])
    team = str(metadata["team_name"])
    try:
        seat = names.index(team)
    except ValueError as exc:
        raise ValueError(
            f"team {team!r} is not present in replay TeamNames={names!r}"
        ) from exc
    steps = replay.get("steps", []) or []
    actions = [step[seat].get("action", {}) for step in steps[1:]]
    if len(actions) != 719:
        raise ValueError(
            f"episode {metadata['episode_id']} has {len(actions)} decisions; expected 719"
        )
    digest = _digest(actions)
    route_name = f"episode-{int(metadata['episode_id'])}-team{seat}.json.gz"
    route_path = output / route_name
    payload = {
        "actions": actions,
        "metadata": {
            "date": str(metadata["date"]),
            "episode_id": int(metadata["episode_id"]),
            "team": team,
            "opponent": str(metadata.get("opponent", "")),
            "daily_rank": int(metadata.get("daily_rank", 0) or 0),
            "daily_score_proxy": float(metadata.get("daily_score_proxy", 0.0) or 0.0),
            "source_shard": str(metadata["replay_shard"]),
            "seat": seat,
            "seed": int(info.get("seed", 0) or 0),
            "action_sha256": digest,
        },
    }
    with gzip.open(route_path, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"))
    return {
        "path": str(route_path.resolve()),
        "date": str(metadata["date"]),
        "episode_id": int(metadata["episode_id"]),
        "team": team,
        "opponent": str(metadata.get("opponent", "")),
        "daily_rank": int(metadata.get("daily_rank", 0) or 0),
        "daily_score_proxy": float(metadata.get("daily_score_proxy", 0.0) or 0.0),
        "source_seat": seat,
        "seed": int(info.get("seed", 0) or 0),
        "num_actions": len(actions),
        "action_sha256": digest,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--leaderboard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--days", nargs="+", required=True)
    parser.add_argument("--leaderboard-limit", type=int, default=10)
    parser.add_argument("--per-team-day", type=int, default=3)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    teams = _leaderboard_teams(args.leaderboard, args.leaderboard_limit)
    episodes_path = args.root / "episodes.parquet"
    table = pq.read_table(
        episodes_path,
        columns=[
            "date",
            "episode_id",
            "team_name",
            "daily_rank",
            "daily_score_proxy",
            "opponent",
            "replay_shard",
        ],
    )
    metadata_rows = _select_metadata(
        table.to_pylist(),
        teams,
        {str(day) for day in args.days},
        max(1, int(args.per_team_day)),
    )
    by_shard: dict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in metadata_rows:
        by_shard[str(row["replay_shard"])][int(row["episode_id"])] = row

    output_rows: list[dict[str, Any]] = []
    for shard_name, wanted in sorted(by_shard.items()):
        shard_path = args.root / shard_name
        if not shard_path.exists():
            raise FileNotFoundError(shard_path)
        found: set[int] = set()
        parquet = pq.ParquetFile(shard_path)
        for batch in parquet.iter_batches(
            batch_size=1,
            columns=["episode_id", "replay_json"],
        ):
            episode_id = int(batch.column("episode_id")[0].as_py())
            metadata = wanted.get(episode_id)
            if metadata is None:
                continue
            replay = json.loads(batch.column("replay_json")[0].as_py())
            output_rows.append(_write_route(args.output, replay, metadata))
            found.add(episode_id)
            print(
                f"extracted {metadata['date']} {metadata['team_name']} "
                f"episode={episode_id} ({len(output_rows)}/{len(metadata_rows)})",
                flush=True,
            )
            del replay
        missing = set(wanted) - found
        if missing:
            raise RuntimeError(f"missing replay rows in {shard_name}: {sorted(missing)}")

    output_rows.sort(key=lambda row: (row["date"], row["team"], row["episode_id"]))
    summary_path = args.output / "summary.json"
    summary_path.write_text(json.dumps(output_rows, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "teams": sorted(teams),
                "metadata_rows": len(metadata_rows),
                "routes_written": len(output_rows),
                "unique_action_hashes": len({row["action_sha256"] for row in output_rows}),
                "summary": str(summary_path.resolve()),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
