"""Verify downloaded source hashes and runner route payloads without game runs."""

from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def decoded(raw: bytes):
    value = json.loads(raw.decode("utf-8-sig"))
    for _ in range(2):
        if not isinstance(value, str):
            return value
        value = json.loads(value)
    return value


def route_actions(replay: dict, seat: int) -> list:
    return [frame[seat].get("action") or {"farmer": ["PASS"], "hands": [], "market": []}
            for frame in replay["steps"][1:]]


def check_entry(row: dict) -> None:
    route_path = Path(row["path"])
    route = json.loads(gzip.decompress(route_path.read_bytes()))
    route_action_hash = sha(canonical(route["actions"]))
    assert route_action_hash == row["action_sha256"], (row["episode_id"], "route action hash")
    assert len(route["actions"]) == row["num_actions"] == 719, (row["episode_id"], "route action count")

    replay_path = Path(row["replay_path"])
    replay_raw = gzip.decompress(replay_path.read_bytes())
    assert sha(replay_raw) == row["replay_sha256"], (row["episode_id"], "raw replay hash")
    replay = decoded(replay_raw)
    assert len(replay["steps"]) == row["frames"] == 720, (row["episode_id"], "frame count")
    assert replay.get("statuses") == ["DONE", "DONE"] == row["source_statuses"], (row["episode_id"], "statuses")
    assert replay.get("module_version") == row["engine_version"] == "1.32.7", (row["episode_id"], "engine")
    source_seat = int(row["source_seat"])
    opponent_seat = int(row["opponent_seat"])
    assert opponent_seat == 1 - source_seat
    names = list((replay.get("info") or {}).get("TeamNames") or [])
    assert names[source_seat] == row["team"], (row["episode_id"], "source seat")
    assert names[opponent_seat] == row["opponent_team"], (row["episode_id"], "opponent seat")
    assert canonical(route["actions"]) == canonical(route_actions(replay, source_seat)), (row["episode_id"], "source actions")

    index = json.loads(gzip.decompress(Path(row["public_state_index_path"]).read_bytes()))
    action_hashes = index["action_sha256_by_seat"]
    assert action_hashes[str(source_seat)] == row["action_sha256"], (row["episode_id"], "indexed source actions")
    assert action_hashes[str(opponent_seat)] == row["opponent_action_sha256"], (row["episode_id"], "indexed opponent actions")
    state_raw = gzip.decompress(Path(row["public_state_path"]).read_bytes())
    assert sha(state_raw) == row["public_state_sha256"], (row["episode_id"], "public state hash")
    timeline = json.loads(state_raw)
    assert len(timeline) == 720, (row["episode_id"], "public state frame count")
    assert all(len(frame["states"]) == 2 for frame in timeline), (row["episode_id"], "public state seats")


def main() -> None:
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["complete"] and manifest["team_rows"] == 100
    rows_checked = 0
    tier_receipts = {}
    for tier, relative in {
        "development_latest": "routes/development_latest/summary.json",
        "reserved_second": "routes/episode_2/summary.json",
        "reserved_third": "routes/episode_3/summary.json",
    }.items():
        path = HERE / relative
        rows = json.loads(path.read_text(encoding="utf-8"))
        assert len(rows) == 100, (tier, len(rows))
        assert len({int(row["rank"]) for row in rows}) == 100, (tier, "rank coverage")
        assert all(row["runner_eligible"] for row in rows), (tier, "ineligible route")
        for row in rows:
            check_entry(row)
        tier_receipts[tier] = {"summary_path": str(path.resolve()),
                               "summary_sha256": sha(path.read_bytes()),
                               "routes": len(rows),
                               "unique_episode_ids": len({int(row["episode_id"]) for row in rows}),
                               "engine_versions": sorted({row["engine_version"] for row in rows})}
        rows_checked += len(rows)

    own = json.loads((HERE / "current_submission_56680167.json").read_text(encoding="utf-8"))
    assert own["submission_status"]["ref"] == 56680167
    assert own["submission_status"]["status"] == "SubmissionStatus.COMPLETE"
    assert int(own["completed_public_episode_count"]) == 27
    assert len(own["routes"]) == 27 and not own["download_errors"]
    for row in own["routes"]:
        check_entry(row)
    own_ids = set(own["public_episode_ids"])
    assert own_ids == {int(row["episode_id"]) for row in own["routes"]}

    retry = json.loads((HERE / "listing_retries.json").read_text(encoding="utf-8"))
    assert retry["initial_failed_teams"] == 64 and retry["recovered"] == 64 and retry["unrecovered"] == 0
    errors = json.loads((HERE / "collection_errors.json").read_text(encoding="utf-8"))
    assert not errors["listing_rows_unavailable"]
    assert not errors["episode_slots_unavailable"]
    assert not errors["current_submission_errors"]

    replay_files = sorted((HERE / "raw_archive").glob("episode-*-replay.json.gz"))
    assert len(replay_files) == 267, len(replay_files)
    for archive in replay_files:
        episode_id = int(archive.name.split("-")[1])
        raw = gzip.decompress(archive.read_bytes())
        receipt = json.loads((HERE / "raw_archive" / f"episode-{episode_id}-receipt.json").read_text(encoding="utf-8"))
        assert sha(raw) == receipt["source_sha256"], (episode_id, "raw archive receipt")

    receipt = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
               "no_games_run": True, "all_checks_passed": True,
               "top100_latest_three_tiers_checked": rows_checked,
               "current_submission_id": 56680167,
               "current_submission_status": own["submission_status"]["status"],
               "current_submission_public_episodes_checked": len(own["routes"]),
               "raw_unique_replay_archives_checked": len(replay_files),
               "listing_retry_recovered": retry["recovered"],
               "listing_retry_unrecovered": retry["unrecovered"],
               "tiers": tier_receipts}
    output = HERE / "verification_receipt.json"
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
