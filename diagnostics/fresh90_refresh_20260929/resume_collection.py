"""Resume the 2026-09-29 read-only replay collection after rate limiting."""

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import shutil
import sys
import time
from pathlib import Path

import collect as c

HERE = Path(__file__).resolve().parent
MAX_DOWNLOAD_WORKERS = 2
MAX_LIST_RETRIES = 2


def write_json(path: Path, value: object) -> None:
    c.write_json(path, value)


def robust_run_json(args, label, raw_path, parsed_path, *, timeout=90):
    """Retry 429s at low request concurrency and preserve every response attempt."""
    attempts = []
    for attempt in range(1, 4):
        attempt_raw = raw_path.with_name(raw_path.stem + f".retry{attempt}" + raw_path.suffix)
        process = c.run([*args, "--format", "json"], timeout=timeout)
        raw_bytes = process.stdout.encode("utf-8")
        c.write_bytes(attempt_raw, raw_bytes)
        stderr_path = attempt_raw.with_suffix(attempt_raw.suffix + ".stderr.txt")
        c.write_bytes(stderr_path, process.stderr.encode("utf-8"))
        attempt_row = {"attempt": attempt, "checked_at_utc": c.now(),
                       "stdout_path": str(attempt_raw.resolve()),
                       "stderr_path": str(stderr_path.resolve()),
                       "exit_code": process.returncode,
                       "stdout_sha256": c.sha256(raw_bytes),
                       "stderr_sha256": c.sha256(process.stderr.encode("utf-8"))}
        attempts.append(attempt_row)
        if process.returncode == 0:
            value = c.decode_json(process.stdout, label)
            write_json(parsed_path, value)
            attempt_row["parsed_sha256"] = c.sha256(parsed_path.read_bytes())
            return value, {"stdout_sha256": attempt_row["stdout_sha256"],
                           "parsed_sha256": attempt_row["parsed_sha256"],
                           "checked_at_utc": attempt_row["checked_at_utc"],
                           "raw_stdout_path": str(attempt_raw.resolve()),
                           "parsed_path": str(parsed_path.resolve()),
                           "retry_attempts": attempts}
        message = (process.stderr or process.stdout)[:600]
        attempt_row["error"] = message
        if "429" not in message and "Too Many Requests" not in message:
            break
        if attempt < 3:
            time.sleep(8 * attempt)
    raise RuntimeError(f"Kaggle read failed for {label} after {len(attempts)} retries: "
                       f"{attempts[-1].get('error', 'unknown error')}")


def preserve_prior_artifacts(row: dict) -> None:
    team_id = int(row["team_id"])
    folder = HERE / "retry_preserved" / f"team-{team_id}" / "initial"
    if folder.exists():
        return
    folder.mkdir(parents=True, exist_ok=True)
    for base in (HERE / "api_raw", HERE / "listings"):
        for path in base.glob(f"team-{team_id}-*"):
            shutil.copy2(path, folder / path.name)


def routes_for_position(manifest: dict, position: int) -> list[dict]:
    routes = []
    for row in manifest["rows"]:
        for slot in row.get("episodes", []):
            if int(slot.get("position", -1)) == position and slot.get("route"):
                routes.append(slot["route"])
    return sorted(routes, key=lambda entry: (int(entry.get("rank", 999)), int(entry.get("team_id", 0))))


def write_summaries(manifest: dict) -> None:
    for position in (1, 2, 3):
        routes = routes_for_position(manifest, position)
        write_json(HERE / "routes" / f"episode_{position}" / "summary.json", routes)
        if position == 1:
            write_json(HERE / "routes" / "development_latest" / "summary.json", routes)
            write_json(HERE / "routes" / "development_top20" / "summary.json",
                       [row for row in routes if int(row.get("rank", 999)) <= 20])
    manifest["latest_episode_routes"] = len(routes_for_position(manifest, 1))
    manifest["reserved_episode_2_routes"] = len(routes_for_position(manifest, 2))
    manifest["reserved_episode_3_routes"] = len(routes_for_position(manifest, 3))


def update_slots(manifest: dict, teams_by_id: dict[int, dict], positions: set[int]) -> None:
    rows_by_id = {int(row["team_id"]): row for row in manifest["rows"]}
    users = defaultdict(list)
    for team_id, row in rows_by_id.items():
        for slot in row.get("episodes", []):
            if int(slot.get("position", -1)) in positions and "episode" in slot:
                users[int(slot["episode"]["id"])].append((row, slot))
    episode_ids = sorted(users)
    downloads = {}
    with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) as pool:
        futures = {pool.submit(c.download_episode, eid): eid for eid in episode_ids}
        for future in as_completed(futures):
            eid = futures[future]
            try:
                downloads[eid] = future.result()
            except Exception as error:
                message = f"{type(error).__name__}: {error}"
                manifest.setdefault("errors", []).append({"episode_id": eid, "error": message,
                                                           "failed_at_utc": c.now()})
                for row, slot in users[eid]:
                    slot.update(download_status="unavailable", download_error=message)
                continue
            archive, raw, receipt, replay = downloads[eid]
            try:
                sidecar = c.build_sidecar(eid, replay, archive, receipt)
                for row, slot in users[eid]:
                    try:
                        slot.update(c.add_episode_record(row, slot, downloads[eid], {eid: sidecar}))
                    except Exception as error:
                        slot.update(download_status="unavailable",
                                    download_error=f"{type(error).__name__}: {error}")
            except Exception as error:
                message = f"{type(error).__name__}: {error}"
                manifest.setdefault("errors", []).append({"episode_id": eid, "error": message,
                                                           "failed_at_utc": c.now()})
                for row, slot in users[eid]:
                    slot.update(download_status="unavailable", download_error=message)
            write_summaries(manifest)
            manifest["rows"] = sorted(rows_by_id.values(), key=lambda row: int(row["rank"]))
            manifest["routes_updated_at_utc"] = c.now()
            write_json(HERE / "manifest.json", manifest)
            print(f"ROUTES position={min(positions)} episode={eid} rows="
                  f"{manifest['latest_episode_routes']}/100", flush=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    teams = json.loads((HERE / "top100_teams.json").read_text(encoding="utf-8"))
    teams_by_id = {int(team["teamId"]): team for team in teams}
    rows_by_id = {int(row["team_id"]): row for row in manifest["rows"]}

    # Build the already listed latest tape panel first so the root can start its
    # development benchmark while transiently rate-limited listings are repaired.
    update_slots(manifest, teams_by_id, {1})
    top20 = json.loads((HERE / "routes" / "development_top20" / "summary.json").read_text(encoding="utf-8"))
    if len(top20) == 20:
        ready = {"ready_at_utc": c.now(), "routes": len(top20),
                 "summary_path": str((HERE / "routes" / "development_top20" / "summary.json").resolve()),
                 "leaderboard_snapshot_utc": manifest["leaderboard_snapshot_utc"]}
        write_json(HERE / "top20_ready.json", ready)
        print("TOP20_READY " + json.dumps(ready), flush=True)

    # Retry only failed or missing listing rows, serially. Keep initial failures and
    # each CLI attempt so rate limits remain visible in the provenance record.
    c.run_json = robust_run_json
    retry_rows = [row for row in manifest["rows"] if row.get("unavailable") == "Team listing retrieval failed"
                  or row.get("listing_errors")]
    retry_log = {"started_at_utc": c.now(), "concurrency": 1, "max_http_retries_per_request": 3,
                 "teams": [], "complete": False}
    write_json(HERE / "listing_retries.json", retry_log)
    for index, row in enumerate(retry_rows, 1):
        preserve_prior_artifacts(row)
        team = teams_by_id[int(row["team_id"])]
        initial_errors = list(row.get("listing_errors", []))
        attempts = [{"attempt": 0, "result": "initial_failure", "errors": initial_errors,
                     "recorded_at_utc": row.get("checked_at_utc")}]
        replacement = None
        for attempt in range(1, MAX_LIST_RETRIES + 1):
            retry_row = c.fetch_team_selection(team)
            ok = bool(retry_row.get("episodes") and retry_row.get("submission_id")
                      and any("episode" in slot for slot in retry_row["episodes"]))
            attempts.append({"attempt": attempt, "success": ok,
                             "errors": retry_row.get("listing_errors", []),
                             "unavailable": retry_row.get("unavailable"),
                             "checked_at_utc": retry_row.get("checked_at_utc")})
            replacement = retry_row
            if ok:
                break
            error_text = " ".join(retry_row.get("listing_errors", []))
            if "429" in error_text or "Too Many Requests" in error_text:
                time.sleep(12 * attempt)
        if replacement is not None and not replacement.get("listing_errors"):
            replacement["retry_attempts"] = attempts
            rows_by_id[int(row["team_id"])] = replacement
        else:
            row["retry_attempts"] = attempts
        manifest["rows"] = sorted(rows_by_id.values(), key=lambda item: int(item["rank"]))
        retry_log["teams"].append({"rank": row["rank"], "team_id": row["team_id"],
                                   "team": row["team"], "attempts": attempts,
                                   "recovered": replacement is not None and not replacement.get("listing_errors")})
        retry_log["completed_teams"] = index
        write_json(HERE / "listing_retries.json", retry_log)
        write_json(manifest_path, manifest)
        print(f"RETRY_LISTING {index}/{len(retry_rows)} rank={row['rank']} "
              f"recovered={retry_log['teams'][-1]['recovered']}", flush=True)

    retry_log.update(completed_at_utc=c.now(), complete=True,
                     recovered=sum(entry["recovered"] for entry in retry_log["teams"]),
                     unrecovered=sum(not entry["recovered"] for entry in retry_log["teams"]))
    write_json(HERE / "listing_retries.json", retry_log)

    # Refresh every available route after listing repairs, then fill reserved rows.
    update_slots(manifest, teams_by_id, {1})
    update_slots(manifest, teams_by_id, {2})
    update_slots(manifest, teams_by_id, {3})

    # The exact uploaded submission is separate from the leaderboard-selected
    # historical version. Download every completed public episode in its listing.
    own = json.loads((HERE / "current_submission_56680167.json").read_text(encoding="utf-8"))
    own_slots = own.get("public_episode_slots", [])
    own_routes = []
    own_errors = []
    own_ids = sorted({int(slot["episode"]["id"]) for slot in own_slots if "episode" in slot})
    own_data = {}
    with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) as pool:
        futures = {pool.submit(c.download_episode, eid): eid for eid in own_ids}
        for future in as_completed(futures):
            eid = futures[future]
            try:
                own_data[eid] = future.result()
            except Exception as error:
                own_errors.append({"episode_id": eid, "error": f"{type(error).__name__}: {error}"})
            print(f"CURRENT_REPLAY {len(own_data)+len(own_errors)}/{len(own_ids)} episode={eid}", flush=True)
    for slot in own_slots:
        episode = slot["episode"]
        eid = int(episode["id"])
        if eid not in own_data:
            continue
        try:
            archive, raw, receipt, replay = own_data[eid]
            names = list((replay.get("info") or {}).get("TeamNames") or [])
            if names.count(c.OUR_TEAM_NAME) != 1:
                raise RuntimeError(f"Replay does not contain our team name {c.OUR_TEAM_NAME!r}: {names!r}")
            sidecar = c.build_sidecar(eid, replay, archive, receipt)
            seat = names.index(c.OUR_TEAM_NAME)
            route_dir = HERE / "routes" / "current_submission_56680167"
            route_dir.mkdir(parents=True, exist_ok=True)
            route = c._write_route(route_dir, c.OUR_TEAM_NAME, c.OUR_TEAM_ID,
                                   c.CURRENT_SUBMISSION_ID, episode, replay)
            actions = c.safe_actions(replay["steps"], seat)
            route.update({"episode_position": slot["position"], "team": c.OUR_TEAM_NAME,
                          "team_id": c.OUR_TEAM_ID,
                          "rank": next((team["rank"] for team in teams if int(team["teamId"]) == c.OUR_TEAM_ID), None),
                          "source_seat": seat, "opponent_seat": 1-seat,
                          "opponent_team": names[1-seat], "seed": (replay.get("info") or {}).get("seed"),
                          "engine_version": replay.get("module_version"),
                          "source_statuses": replay.get("statuses"),
                          "frames": len(replay.get("steps") or []),
                          "runner_eligible": (len(replay.get("steps") or []) == 720
                                              and replay.get("statuses") == ["DONE", "DONE"]
                                              and route.get("num_actions") == 719),
                          "replay_path": str(archive.resolve()), "replay_sha256": receipt["source_sha256"],
                          "replay_archive_sha256": receipt["archive_sha256"],
                          "action_sha256": c.sha256(c.canonical_bytes(actions)),
                          "opponent_action_sha256": sidecar["action_sha256_by_seat"][str(1-seat)],
                          "public_state_path": sidecar["public_state_path"],
                          "public_state_sha256": sidecar["public_state_sha256"],
                          "public_state_index_path": sidecar["sidecar_path"],
                          "public_state_index_sha256": sidecar["sidecar_sha256"],
                          "market_fields": sidecar["market_fields"],
                          "town_fields": sidecar["town_fields"]})
            own_routes.append(route)
        except Exception as error:
            own_errors.append({"episode_id": eid, "error": f"{type(error).__name__}: {error}"})
    own.update({"downloaded_episode_ids": sorted(own_data), "download_errors": own_errors,
                "routes": sorted(own_routes, key=lambda route: int(route["episode_position"]))})
    write_json(HERE / "current_submission_56680167.json", own)
    write_json(HERE / "routes" / "current_submission_56680167" / "summary.json", own_routes)

    # Repeated episode IDs are expected when both ranked teams share a public game.
    uses = defaultdict(list)
    for row in manifest["rows"]:
        for slot in row.get("episodes", []):
            if "episode" in slot:
                uses[int(slot["episode"]["id"])].append({"rank": row["rank"], "team": row["team"],
                                                          "team_id": row["team_id"],
                                                          "episode_position": slot["position"]})
    duplicates = [{"episode_id": eid, "uses": value} for eid, value in sorted(uses.items()) if len(value) > 1]
    write_json(HERE / "duplicate_episodes.json", {"selected_episode_slots": sum(map(len, uses.values())),
                                                     "unique_selected_episode_ids": len(uses),
                                                     "duplicate_episode_id_count": len(duplicates),
                                                     "duplicates": duplicates})
    write_summaries(manifest)
    manifest["current_submission_status"] = own
    manifest["listing_retry_summary"] = {"initial_failed_teams": len(retry_rows),
                                         "recovered": retry_log["recovered"],
                                         "unrecovered": retry_log["unrecovered"]}
    manifest["completed_at_utc"] = c.now()
    manifest["complete"] = len(manifest["rows"]) == 100
    manifest["team_rows"] = len(manifest["rows"])
    manifest["selected_team_episode_slots"] = sum(1 for row in manifest["rows"]
        for slot in row.get("episodes", []) if "episode" in slot)
    manifest["unique_team_episode_ids"] = len(uses)
    manifest["duplicate_episode_id_count"] = len(duplicates)
    manifest["engine_versions_observed"] = sorted({
        str(slot["route"].get("engine_version"))
        for row in manifest["rows"] for slot in row.get("episodes", []) if slot.get("route")
    } | {str(route.get("engine_version")) for route in own_routes if route.get("engine_version")})
    write_json(manifest_path, manifest)
    write_json(HERE / "collection_errors.json", {
        "listing_rows_unavailable": [{"rank": row["rank"], "team": row["team"],
                                       "errors": row.get("listing_errors", [])}
                                      for row in manifest["rows"] if row.get("listing_errors")],
        "episode_slots_unavailable": [{"rank": row["rank"], "team": row["team"],
                                       "position": slot.get("position"),
                                       "episode_id": slot.get("episode", {}).get("id"),
                                       "error": slot.get("download_error")}
                                      for row in manifest["rows"] for slot in row.get("episodes", [])
                                      if slot.get("download_status") == "unavailable"],
        "current_submission_errors": own_errors,
    })
    print("RESUME_COMPLETE " + json.dumps({"rows": len(manifest["rows"]),
          "latest_routes": manifest["latest_episode_routes"],
          "episode2_routes": manifest["reserved_episode_2_routes"],
          "episode3_routes": manifest["reserved_episode_3_routes"],
          "listing_retry": manifest["listing_retry_summary"],
          "own_submission_public_completed": own.get("completed_public_episode_count"),
          "own_submission_downloaded": len(own_routes),
          "engine_versions": manifest["engine_versions_observed"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
