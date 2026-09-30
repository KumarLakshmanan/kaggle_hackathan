"""Build runner-compatible rival action tapes from submission 56680167 replays.

The source replay is the current upload's own public episode listing.  These
routes contain only the other seat's actions; the uploaded agent's action
archive remains separately available in routes/current_submission_56680167.
This utility is offline and makes no Kaggle calls or game runs.
"""

from __future__ import annotations

from datetime import datetime, timezone
import csv
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "routes" / "current_submission_56680167_opponents"
OWN_SUBMISSION_ID = 56680167
OWN_TEAM_NAME = "Lakshmanan R"
OWN_TEAM_ID = 16674353


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def decode(raw: bytes):
    value = json.loads(raw.decode("utf-8-sig"))
    for _ in range(2):
        if not isinstance(value, str):
            return value
        value = json.loads(value)
    return value


def main() -> None:
    source = json.loads((HERE / "current_submission_56680167.json").read_text(encoding="utf-8"))
    leaderboard_path = HERE / "leaderboard_source" / "leaderboard.csv"
    team_rows = list(csv.DictReader(leaderboard_path.open(encoding="utf-8-sig", newline="")))
    by_name: dict[str, list[dict[str, str]]] = {}
    for item in team_rows:
        by_name.setdefault(item.get("TeamName", ""), []).append(item)
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    seen_episode_ids = set()
    for ordinal, own_row in enumerate(sorted(source["routes"], key=lambda r: int(r["episode_position"]))):
        episode_id = int(own_row["episode_id"])
        if episode_id in seen_episode_ids:
            raise RuntimeError(f"duplicate current-submission public episode {episode_id}")
        seen_episode_ids.add(episode_id)

        replay_path = Path(own_row["replay_path"])
        replay_archive_raw = replay_path.read_bytes()
        replay_raw = gzip.decompress(replay_archive_raw)
        if sha(replay_raw) != own_row["replay_sha256"]:
            raise RuntimeError(f"raw replay SHA mismatch for episode {episode_id}")
        replay = decode(replay_raw)
        names = list((replay.get("info") or {}).get("TeamNames") or [])
        own_seat = int(own_row["source_seat"])
        rival_seat = int(own_row["opponent_seat"])
        if names[own_seat] != OWN_TEAM_NAME or names[rival_seat] != own_row["opponent_team"]:
            raise RuntimeError(f"seat/name mismatch for episode {episode_id}: {names!r}")
        if rival_seat != 1 - own_seat or len(replay.get("steps") or []) != 720:
            raise RuntimeError(f"seat/frame mismatch for episode {episode_id}")

        actions = [frame[rival_seat].get("action") or {"farmer": ["PASS"], "hands": [], "market": []}
                   for frame in replay["steps"][1:]]
        action_hash = sha(canonical(actions))
        if len(actions) != 719 or action_hash != own_row["opponent_action_sha256"]:
            raise RuntimeError(f"rival tape does not match archived opponent hash for episode {episode_id}")

        index_path = Path(own_row["public_state_index_path"])
        index = json.loads(gzip.decompress(index_path.read_bytes()))
        if index["action_sha256_by_seat"][str(rival_seat)] != action_hash:
            raise RuntimeError(f"rival sidecar hash mismatch for episode {episode_id}")
        if index["action_sha256_by_seat"][str(own_seat)] != own_row["action_sha256"]:
            raise RuntimeError(f"uploaded-agent sidecar hash mismatch for episode {episode_id}")

        opponent_name = names[rival_seat]
        matching = by_name.get(opponent_name, [])
        if len(matching) > 1:
            raise RuntimeError(f"leaderboard name is not unique: {opponent_name!r}")
        leaderboard = matching[0] if matching else None
        opponent_team_id = int(leaderboard["TeamId"]) if leaderboard else None
        leaderboard_rank = int(leaderboard["Rank"]) if leaderboard else None
        # The replay identifies the rival team/action tape, but not its exact
        # Kaggle submission id.  Keep that field null instead of guessing.
        opponent_submission_id = None

        route_name = f"rival-team-{opponent_team_id or 'unknown'}-episode-{episode_id}-seat{rival_seat}.json.gz"
        route_path = OUT / route_name
        metadata = {
            "team": opponent_name,
            "team_id": opponent_team_id,
            "submission_id": opponent_submission_id,
            "episode_id": episode_id,
            "create_time": own_row.get("create_time"),
            "end_time": own_row.get("episode_end_time"),
            "seed": own_row.get("seed"),
            "seat": rival_seat,
            "team_names": names,
            "action_sha256": action_hash,
            "engine_version": own_row.get("engine_version"),
            "source_kind": "opponent actions from uploaded submission public replay",
            "episode_listing_submission_id": OWN_SUBMISSION_ID,
            "opponent_submission_id_verified": False,
            "uploaded_agent_team": OWN_TEAM_NAME,
            "uploaded_agent_team_id": OWN_TEAM_ID,
            "uploaded_agent_submission_id": OWN_SUBMISSION_ID,
            "uploaded_agent_original_seat": own_seat,
            "uploaded_agent_action_sha256": own_row["action_sha256"],
            "uploaded_agent_result": own_row.get("wdl_result"),
        }
        payload = {"actions": actions, "metadata": metadata}
        route_path.write_bytes(gzip.compress(canonical(payload), compresslevel=9, mtime=0))

        row = {
            "path": str(route_path.resolve()),
            "team": opponent_name,
            "team_id": opponent_team_id,
            "submission_id": opponent_submission_id,
            "episode_id": episode_id,
            "create_time": own_row.get("create_time"),
            "episode_end_time": own_row.get("episode_end_time"),
            "seed": own_row.get("seed"),
            "source_seat": rival_seat,
            "num_actions": len(actions),
            "action_sha256": action_hash,
            # Runner bookkeeping only; this is not a leaderboard rank.
            "rank": 101 + ordinal,
            "rank_is_diagnostic_index": True,
            "team_rank_at_snapshot": leaderboard_rank,
            "source_submission_id": OWN_SUBMISSION_ID,
            "episode_listing_submission_id": OWN_SUBMISSION_ID,
            "opponent_submission_id_verified": False,
            "opponent_submission_id_note": "Exact rival submission ID was not present in the downloaded public replay/listing; intentionally left null.",
            "opponent_seat": own_seat,
            "opponent_team": OWN_TEAM_NAME,
            "opponent_team_id": OWN_TEAM_ID,
            "opponent_action_sha256": own_row["action_sha256"],
            "uploaded_agent_original_source_seat": own_seat,
            "uploaded_agent_wdl_result": own_row.get("wdl_result"),
            "uploaded_agent_action_sha256": own_row["action_sha256"],
            "engine_version": own_row.get("engine_version"),
            "replay_path": str(replay_path.resolve()),
            "replay_sha256": own_row["replay_sha256"],
            "replay_archive_sha256": own_row.get("replay_archive_sha256"),
            "source_statuses": replay.get("statuses"),
            "frames": len(replay["steps"]),
            "runner_eligible": len(actions) == 719 and replay.get("statuses") == ["DONE", "DONE"],
            "public_state_path": own_row.get("public_state_path"),
            "public_state_sha256": own_row.get("public_state_sha256"),
            "public_state_index_path": str(index_path.resolve()),
            "public_state_index_sha256": own_row.get("public_state_index_sha256"),
            "market_fields": own_row.get("market_fields"),
            "town_fields": own_row.get("town_fields"),
            "uploaded_agent_result": own_row.get("wdl_result"),
            "rival_result": {"win": "loss", "loss": "win", "draw": "draw"}.get(own_row.get("wdl_result")),
        }
        rows.append(row)

    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "submission_id": OWN_SUBMISSION_ID,
        "source_public_episode_count": len(source["routes"]),
        "rival_action_route_count": len(rows),
        "unique_episode_count": len(seen_episode_ids),
        "hashes_verified_against_opponent_action_sha256": len(rows),
        "hashes_verified_against_public_state_index": len(rows),
        "team_ids_mapped_from_frozen_full_leaderboard": sum(row["team_id"] is not None for row in rows),
        "team_ids_unmapped": [row["team"] for row in rows if row["team_id"] is None],
        "rival_submission_ids_known": sum(row["submission_id"] is not None for row in rows),
        "route_summary_path": str(summary_path.resolve()),
        "route_summary_sha256": sha(summary_path.read_bytes()),
        "no_game_runs": True,
        "no_kaggle_calls": True,
    }
    (OUT / "receipt.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
