"""Summarize every listed public episode for uploaded submission 56680167."""

from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUBMISSION_ID = 56680167
TEAM_NAME = "Lakshmanan R"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def decode(raw: bytes):
    value = json.loads(raw.decode("utf-8-sig"))
    for _ in range(2):
        if not isinstance(value, str):
            return value
        value = json.loads(value)
    return value


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def main() -> None:
    source = HERE / "current_submission_56680167.json"
    own = json.loads(source.read_text(encoding="utf-8"))
    outcomes = []
    updated_routes = []
    for listing_entry in own["public_episode_slots"]:
        episode = listing_entry["episode"]
        episode_id = int(episode["id"])
        replay_archive = HERE / "raw_archive" / f"episode-{episode_id}-replay.json.gz"
        raw = gzip.decompress(replay_archive.read_bytes())
        replay = decode(raw)
        names = list((replay.get("info") or {}).get("TeamNames") or [])
        if names.count(TEAM_NAME) != 1:
            raise RuntimeError(f"Episode {episode_id} has unexpected TeamNames={names!r}")
        seat = names.index(TEAM_NAME)
        other = 1 - seat
        steps = replay["steps"]
        assert len(steps) == 720 and replay.get("statuses") == ["DONE", "DONE"]
        own_reward = steps[-1][seat].get("reward")
        rival_reward = steps[-1][other].get("reward")
        margin = own_reward - rival_reward
        result = "win" if margin > 0 else "loss" if margin < 0 else "draw"
        outcomes.append({"episode_id": episode_id, "create_time": episode.get("createTime"),
                         "opponent": names[other], "source_seat": seat,
                         "opponent_seat": other, "result": result})

        route = next((item for item in own.get("routes", []) if int(item["episode_id"]) == episode_id), None)
        if route is None:
            raise RuntimeError(f"Missing runner route for listed public episode {episode_id}")
        route_payload = json.loads(gzip.decompress(Path(route["path"]).read_bytes()))
        replay_actions = [frame[seat].get("action") or {"farmer": ["PASS"], "hands": [], "market": []}
                          for frame in steps[1:]]
        action_hash = sha(canonical(route_payload["actions"]))
        if canonical(route_payload["actions"]) != canonical(replay_actions):
            raise RuntimeError(f"Runner route does not match 56680167 source actions for episode {episode_id}")
        if action_hash != route["action_sha256"]:
            raise RuntimeError(f"Action hash mismatch for episode {episode_id}")
        state_path = HERE / "episode_index" / f"episode-{episode_id}-public-state.json.gz"
        index_path = HERE / "episode_index" / f"episode-{episode_id}-index.json.gz"
        state_raw = gzip.decompress(state_path.read_bytes())
        state_timeline = json.loads(state_raw)
        index = json.loads(gzip.decompress(index_path.read_bytes()))
        route.update({"source_statuses": replay["statuses"], "frames": len(steps),
                      "runner_eligible": len(replay_actions) == 719,
                      "submission_id": SUBMISSION_ID,
                      "selected_submission": own["submission_status"],
                      "selected_submission_score": own["submission_status"].get("publicScore"),
                      "snapshot_score": own["submission_status"].get("publicScore"),
                      "episode_type": episode.get("type"),
                      "episode_state": episode.get("state"),
                      "episode_end_time": episode.get("endTime"),
                      "public_state_path": str(state_path.resolve()),
                      "public_state_sha256": sha(state_raw),
                      "public_state_index_path": str(index_path.resolve()),
                      "public_state_index_sha256": sha(index_path.read_bytes()),
                      "market_fields": index["market_fields"], "town_fields": index["town_fields"]})
        updated_routes.append(route)

    counts = {name: sum(entry["result"] == name for entry in outcomes) for name in ("win", "draw", "loss")}
    assert sum(counts.values()) == len(outcomes) == 27
    results_by_id = {int(entry["episode_id"]): entry for entry in outcomes}
    for route in updated_routes:
        outcome = results_by_id[int(route["episode_id"])]
        route["wdl_result"] = outcome["result"]
        route["result"] = outcome["result"]
    own["routes"] = sorted(updated_routes, key=lambda row: int(row["episode_position"]))
    own["public_episode_wdl"] = counts
    own["public_episode_wdl_scope"] = "All completed public episodes listed for submission 56680167; no outcome-based episode selection"
    own["public_episode_wdl_checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    (HERE / "current_submission_56680167.json").write_text(
        json.dumps(own, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    wdl = {"submission_id": SUBMISSION_ID, "status": own["submission_status"]["status"],
           "public_score_at_snapshot": own["submission_status"].get("publicScore"),
           "checked_at_utc": own["public_episode_wdl_checked_at_utc"],
           "completed_public_episode_count": len(outcomes), "wdl": counts,
           "selection": own["public_episode_wdl_scope"], "episodes": outcomes}
    (HERE / "current_submission_56680167_wdl.json").write_text(
        json.dumps(wdl, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / "routes" / "current_submission_56680167" / "summary.json").write_text(
        json.dumps(updated_routes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["current_submission_status"] = own
    manifest["current_submission_public_wdl"] = counts
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"submission_id": SUBMISSION_ID, "status": wdl["status"],
                      "score": wdl["public_score_at_snapshot"], "completed_public_episodes": len(outcomes),
                      "wdl": counts, "route_rows": len(updated_routes)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
