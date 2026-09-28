"""Freeze local live-loss and current-top20 regression fixtures and baselines."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
COHORT = ROOT / "diagnostics/new_live_56609430_20260927/cohort_180951.json"
LOSS_LEDGER = HERE / "live_loss_ledgers_180951.json"
TOP_DIR = ROOT / "diagnostics/current_top20_20260927_172258"
TOP_MANIFEST = TOP_DIR / "manifest.json"
TOP_ASSESSMENT = TOP_DIR / "assessment.json"
OUT = HERE / "local_target_manifest_180951.json"
TAPE_BASELINE = HERE / "live_loss_tape_baseline_180951.json"
EXPECTED_MAIN = "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def action_hash(actions: list) -> str:
    return sha(json.dumps(actions, separators=(",", ":")).encode("utf-8"))


def result_from_margin(margin: float) -> str:
    return "win" if margin > 0 else "loss" if margin < 0 else "draw"


def fixture_set_digest(entries: list[dict]) -> str:
    payload = [{key: entry[key] for key in (
        "fixture_id", "episode_id", "seed", "source_replay_sha256",
        "source_opponent_action_sha256")}
        for entry in sorted(entries, key=lambda row: int(row["episode_id"]))]
    return sha(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def main() -> None:
    cohort_bytes = COHORT.read_bytes()
    cohort = json.loads(cohort_bytes)
    loss_ledger = json.loads(LOSS_LEDGER.read_text(encoding="utf-8"))
    top_manifest_bytes = TOP_MANIFEST.read_bytes()
    top_manifest = json.loads(top_manifest_bytes)
    top_assessment_bytes = TOP_ASSESSMENT.read_bytes()
    top_assessment = json.loads(top_assessment_bytes)
    tape_baseline = json.loads(TAPE_BASELINE.read_text(encoding="utf-8")) if TAPE_BASELINE.exists() else None

    assert loss_ledger["candidate_sha256"] == EXPECTED_MAIN
    assert top_manifest["candidate_sha256"] == EXPECTED_MAIN
    assert top_assessment["candidate_sha256"] == EXPECTED_MAIN
    if tape_baseline is not None:
        assert tape_baseline["candidate_sha256"] == EXPECTED_MAIN
        assert tape_baseline["complete"] and tape_baseline["game_count"] == 60
    assert len([g for g in cohort["games"] if g["result"] == "loss"]) == 30
    assert len(top_manifest["rows"]) == 20 and len(top_assessment["games"]) == 40

    loss_by_episode = {int(row["episode_id"]): row for row in loss_ledger["rows"]}
    tape_by_episode: dict[int, list[dict]] = {}
    if tape_baseline is not None:
        for row in tape_baseline["games"]:
            tape_by_episode.setdefault(int(row["episode_id"]), []).append(row)
        assert len(tape_by_episode) == 30
    source_replay_parity_count = 0
    cohort_losses = [g for g in cohort["games"] if g["result"] == "loss"]
    live_entries = []
    for game in sorted(cohort_losses, key=lambda row: int(row["episode_id"])):
        episode_id = int(game["episode_id"])
        ledger = loss_by_episode[episode_id]
        assert ledger["margin"] == game["margin"]
        assert ledger["candidate_reward"] == game["own_cash"]
        assert ledger["opponent_reward"] == game["opponent_cash"]
        replay_path = Path(game["replay_path"])
        replay_bytes = gzip.decompress(replay_path.read_bytes())
        replay_sha = sha(replay_bytes)
        assert replay_sha == game["replay_sha256"]
        replay = json.loads(replay_bytes)
        assert replay["module_version"] == "1.32.7"
        candidate_seat = int(game["candidate_seat"])
        rival_seat = 1 - candidate_seat
        actions = [frame[rival_seat].get("action") or {}
                   for frame in replay["steps"][1:720]]
        route_path = Path(ledger["route_path"])
        route_actions = json.loads(gzip.open(route_path, "rt", encoding="utf-8").read())["actions"]
        digest = action_hash(actions)
        assert digest == action_hash(route_actions), episode_id
        rewards = [float(value) for value in game["rewards"]]
        margins_by_seat = [rewards[0] - rewards[1], rewards[1] - rewards[0]]
        seat_outcomes = [{
            "seat": seat,
            "candidate_reward": rewards[seat],
            "opponent_reward": rewards[1-seat],
            "margin": margins_by_seat[seat],
            "result": result_from_margin(margins_by_seat[seat]),
        } for seat in (0, 1)]
        entry = {
            "fixture_id": f"live-{episode_id}",
            "panel": "official_live_cohort_180951",
            "episode_id": episode_id,
            "team": game["opponent"],
            "rank_at_snapshot": (game.get("opponent_snapshot_ranks") or [{}])[0].get("rank"),
            "seed": int(game["seed"]),
            "source_candidate_seat": candidate_seat,
            "source_replay_path": str(replay_path.resolve()),
            "source_replay_sha256": replay_sha,
            "source_action_tape_path": str(route_path.resolve()),
            "source_opponent_action_sha256": digest,
            "source_candidate_action_sha256": action_hash([
                frame[candidate_seat].get("action") or {}
                for frame in replay["steps"][1:720]
            ]),
            "source_public_game_both_seat_outcomes": seat_outcomes,
            "source_statuses": game["statuses"],
            "source_frames": game["frames"],
        }
        if tape_baseline is not None:
            reruns = sorted(tape_by_episode[episode_id], key=lambda row: row["candidate_seat"])
            assert [row["candidate_seat"] for row in reruns] == [0, 1]
            assert all(row["opponent_action_sha256"] == digest for row in reruns)
            original_run = reruns[candidate_seat]
            assert original_run["candidate_reward"] == float(game["own_cash"]), episode_id
            assert original_run["opponent_reward"] == float(game["opponent_cash"]), episode_id
            assert original_run["margin"] == float(game["margin"]), episode_id
            source_replay_parity_count += 1
            entry["baseline_frozen_tape_both_seat_outcomes"] = [{
                "seat": int(row["candidate_seat"]),
                "candidate_reward": float(row["candidate_reward"]),
                "opponent_reward": float(row["opponent_reward"]),
                "margin": float(row["margin"]),
                "result": row["result"],
                "candidate_status": row["candidate_status"],
                "opponent_status": row["opponent_status"],
                "frames": int(row["frames"]),
            } for row in reruns]
        live_entries.append(entry)

    assessment_by_key: dict[tuple[str, int, int], list[dict]] = {}
    if tape_baseline is not None:
        assert tape_baseline["fixture_set_sha256"] == fixture_set_digest(live_entries)
    for row in top_assessment["games"]:
        key = (str(row["team"]), int(row["episode_id"]), int(row["seed"]))
        assessment_by_key.setdefault(key, []).append(row)

    top_entries = []
    for item in sorted(top_manifest["rows"], key=lambda row: (int(row["rank"]), row["team"])):
        replay_path = Path(item["replay_path"])
        replay_bytes = gzip.decompress(replay_path.read_bytes())
        replay_sha = sha(replay_bytes)
        assert replay_sha == item["replay_sha256"], item["episode_id"]
        replay = json.loads(replay_bytes)
        assert replay["module_version"] == "1.32.7"
        route_path = Path(item["path"])
        route_actions = json.loads(gzip.open(route_path, "rt", encoding="utf-8").read())["actions"]
        digest = action_hash(route_actions)
        assert digest == item["action_sha256"], item["episode_id"]
        key = (str(item["team"]), int(item["episode_id"]), int(item["seed"]))
        baseline_rows = sorted(assessment_by_key[key], key=lambda row: int(row["candidate_seat"]))
        assert [int(row["candidate_seat"]) for row in baseline_rows] == [0, 1], key
        assert all(row["candidate_status"] == row["opponent_status"] == "DONE"
                   and row["frames"] == 720 for row in baseline_rows), key
        top_entries.append({
            "fixture_id": f"top20-{int(item['rank']):02d}-{item['team']}-{int(item['episode_id'])}",
            "panel": "current_top20_20260927_172258",
            "team": item["team"],
            "rank_at_snapshot": int(item["rank"]),
            "episode_id": int(item["episode_id"]),
            "seed": int(item["seed"]),
            "source_seat": int(item["source_seat"]),
            "submission_id": int(item["submission_id"]),
            "source_replay_path": str(replay_path.resolve()),
            "source_replay_sha256": replay_sha,
            "source_action_tape_path": str(route_path.resolve()),
            "source_opponent_action_sha256": digest,
            "baseline_frozen_tape_both_seat_outcomes": [{
                "seat": int(row["candidate_seat"]),
                "candidate_reward": float(row["candidate_reward"]),
                "opponent_reward": float(row["opponent_reward"]),
                "margin": float(row["margin"]),
                "result": row["result"],
                "candidate_status": row["candidate_status"],
                "opponent_status": row["opponent_status"],
                "frames": int(row["frames"]),
            } for row in baseline_rows],
        })

    payload = {
        "candidate_baseline_sha256": EXPECTED_MAIN,
        "cohort_path": str(COHORT.resolve()),
        "cohort_sha256": sha(cohort_bytes),
        "top20_manifest_path": str(TOP_MANIFEST.resolve()),
        "top20_manifest_sha256": sha(top_manifest_bytes),
        "top20_assessment_path": str(TOP_ASSESSMENT.resolve()),
        "top20_assessment_sha256": sha(top_assessment_bytes),
        "live_tape_baseline_path": str(TAPE_BASELINE.resolve()) if tape_baseline is not None else None,
        "live_tape_baseline_sha256": sha(TAPE_BASELINE.read_bytes()) if tape_baseline is not None else None,
        "live_fixture_set_sha256": fixture_set_digest(live_entries),
        "live_tape_baseline_summary": ({
            "candidate_sha256": tape_baseline["candidate_sha256"],
            "completed_games": tape_baseline["game_count"],
            "both_seat_pairs": len(live_entries),
            "original_seat_source_reward_parity": source_replay_parity_count,
            "original_seat_outcomes": {
                "wins": sum(row["result"] == "win" for row in tape_baseline["games"]
                            if row["candidate_seat"] == next(
                                entry["source_candidate_seat"] for entry in live_entries
                                if entry["episode_id"] == row["episode_id"])),
                "draws": sum(row["result"] == "draw" for row in tape_baseline["games"]
                             if row["candidate_seat"] == next(
                                 entry["source_candidate_seat"] for entry in live_entries
                                 if entry["episode_id"] == row["episode_id"])),
                "losses": sum(row["result"] == "loss" for row in tape_baseline["games"]
                              if row["candidate_seat"] == next(
                                  entry["source_candidate_seat"] for entry in live_entries
                                  if entry["episode_id"] == row["episode_id"])),
            },
            "opposite_seat_outcomes": {
                "wins": sum(row["result"] == "win" for row in tape_baseline["games"]
                            if row["candidate_seat"] != next(
                                entry["source_candidate_seat"] for entry in live_entries
                                if entry["episode_id"] == row["episode_id"])),
                "draws": sum(row["result"] == "draw" for row in tape_baseline["games"]
                             if row["candidate_seat"] != next(
                                 entry["source_candidate_seat"] for entry in live_entries
                                 if entry["episode_id"] == row["episode_id"])),
                "losses": sum(row["result"] == "loss" for row in tape_baseline["games"]
                              if row["candidate_seat"] != next(
                                  entry["source_candidate_seat"] for entry in live_entries
                                  if entry["episode_id"] == row["episode_id"])),
            },
            "all_statuses_done_720": all(row["candidate_status"] == row["opponent_status"] == "DONE"
                                           and row["frames"] == 720 for row in tape_baseline["games"]),
        } if tape_baseline is not None else None),
        "interpretation": (
            "For each live loss, source_public_game_both_seat_outcomes are the two rewards from the "
            "original public game, while baseline_frozen_tape_both_seat_outcomes are current 4ee "
            "reruns in both seats against that saved rival action tape. These tape reruns are "
            "diagnostic, not reactive validation. The 20 top-team rows preserve the baseline "
            "assessment against their frozen saved action tapes in both seats. Separate local "
            "reacting-reference games are required for policy validation."
        ),
        "live_loss_count": len(live_entries),
        "top20_entry_count": len(top_entries),
        "unique_episode_count": len({row["episode_id"] for row in live_entries + top_entries}),
        "live_losses": live_entries,
        "current_top20": top_entries,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "output": str(OUT.resolve()),
        "live_losses": len(live_entries),
        "top20_entries": len(top_entries),
        "unique_episodes": payload["unique_episode_count"],
        "all_live_replay_hashes_verified": len(live_entries) == 30,
        "all_top20_replay_and_action_hashes_verified": len(top_entries) == 20,
        "all_live_frozen_tape_both_seat_outcomes_present": tape_baseline is not None and all(
            len(entry.get("baseline_frozen_tape_both_seat_outcomes", [])) == 2 for entry in live_entries),
        "candidate_baseline_sha256": EXPECTED_MAIN,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
