"""Build standalone fresh-opening tape routers from development routes only."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import zlib
import base64

HERE = Path(__file__).resolve().parent
SOURCE_DIR = HERE.parents[0] / "fresh90_refresh_20260929"
SUMMARY = SOURCE_DIR / "routes" / "development_latest" / "summary.json"
EXPECTED_SUMMARY_SHA = "9dc48578eb5e828d8038ff39821c8e27ddb12b1a7a4812a87622003c2db63e9c"
EXPECTED_REPLAY_ENGINE = "1.32.7"
MAX_CANDIDATES = 3
CHECKPOINTS = tuple(range(72, 649, 72))


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def decode_replay(raw: bytes):
    value = json.loads(raw.decode("utf-8-sig"))
    for _ in range(2):
        if not isinstance(value, str):
            return value
        value = json.loads(value)
    return value


def projection(action: dict) -> dict:
    # Drop only market trades; preserve every other market order, including
    # relative order, as well as farmer and worker commands.
    return {
        "farmer": action.get("farmer", []),
        "hands": action.get("hands", []),
        "market": [order for order in action.get("market", [])
                   if not order or order[0] not in ("SELL", "BUY_PRODUCT")],
    }


def safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")[:48] or "team"


def load_source() -> tuple[list[dict], dict[str, dict], dict]:
    source_bytes = SUMMARY.read_bytes()
    source_sha = sha(source_bytes)
    if source_sha != EXPECTED_SUMMARY_SHA:
        raise RuntimeError(f"frozen development summary SHA mismatch: {source_sha}")
    rows = json.loads(source_bytes.decode("utf-8"))
    if len(rows) != 100:
        raise RuntimeError(f"expected 100 development rows, found {len(rows)}")

    teams: dict[str, dict] = {}
    for row in rows:
        if not row.get("runner_eligible") or row.get("frames") != 720:
            raise RuntimeError(f"ineligible development route rank {row.get('rank')}")
        if row.get("source_statuses") != ["DONE", "DONE"] or row.get("engine_version") != EXPECTED_REPLAY_ENGINE:
            raise RuntimeError(f"unexpected source status/engine at rank {row.get('rank')}")
        route_path = Path(row["path"])
        payload = json.loads(gzip.decompress(route_path.read_bytes()))
        actions = payload["actions"]
        if len(actions) != 719 or sha(canonical(actions)) != row["action_sha256"]:
            raise RuntimeError(f"action tape/hash mismatch at rank {row.get('rank')}")
        replay_path = Path(row["replay_path"])
        replay_raw = gzip.decompress(replay_path.read_bytes())
        if sha(replay_raw) != row["replay_sha256"]:
            raise RuntimeError(f"raw replay/hash mismatch at rank {row.get('rank')}")
        replay = decode_replay(replay_raw)
        if replay.get("statuses") != ["DONE", "DONE"] or replay.get("module_version") != EXPECTED_REPLAY_ENGINE:
            raise RuntimeError(f"raw replay status/engine mismatch at rank {row.get('rank')}")
        if len(replay.get("steps") or []) != 720:
            raise RuntimeError(f"raw replay frame count mismatch at rank {row.get('rank')}")
        seat = int(row["source_seat"])
        team_names = (replay.get("info") or {}).get("TeamNames") or []
        if len(team_names) != 2 or team_names[seat] != row["team"]:
            raise RuntimeError(f"team/seat mismatch at rank {row.get('rank')}")
        index_path = Path(row["public_state_index_path"])
        index = json.loads(gzip.decompress(index_path.read_bytes()))
        if index["action_sha256_by_seat"][str(seat)] != row["action_sha256"]:
            raise RuntimeError(f"index action hash mismatch at rank {row.get('rank')}")
        state_raw = gzip.decompress(Path(row["public_state_path"]).read_bytes())
        if sha(state_raw) != row["public_state_sha256"]:
            raise RuntimeError(f"public-state hash mismatch at rank {row.get('rank')}")
        timeline = json.loads(state_raw)
        if len(timeline) != 720:
            raise RuntimeError(f"public-state frame count mismatch at rank {row.get('rank')}")
        shop_history = {}
        previous = None
        for step in CHECKPOINTS:
            shops = list(timeline[step]["states"][seat].get("town", {}).get("unlocked_shops", []))
            if previous is not None and shops[:len(previous)] != previous:
                raise RuntimeError(f"shop history not append-only at rank {row.get('rank')} step {step}")
            previous = shops
            shop_history[str(step)] = shops

        episode_id = str(int(row["episode_id"]))
        tape_id = f"{int(row['rank'])}:{episode_id}"
        if tape_id in teams:
            raise RuntimeError(f"duplicate team/episode route key {tape_id}")
        route_projection = [projection(action) for action in actions]
        teams[tape_id] = {
            "tape_id": tape_id,
            "rank": int(row["rank"]),
            "team": row["team"],
            "team_id": row.get("team_id"),
            "submission_id": row.get("submission_id"),
            "episode_id": int(row["episode_id"]),
            "seed": row.get("seed"),
            "source_seat": seat,
            "action_sha256": row["action_sha256"],
            "replay_sha256": row["replay_sha256"],
            "route_path": str(route_path.resolve()),
            "replay_path": str(replay_path.resolve()),
            "shop_history": shop_history,
            "actions": actions,
            "projection": route_projection,
        }
    return rows, teams, {"source_summary_sha256": source_sha}


def select_families(tapes: dict[str, dict]) -> tuple[list[list[dict]], list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for tape in tapes.values():
        digest = sha(canonical(tape["projection"][:72]))
        groups[digest].append(tape)

    family_rows = []
    families = []
    for digest, members in groups.items():
        if len(members) < 2:
            continue
        members = sorted(members, key=lambda item: (item["rank"], item["episode_id"]))
        shared = 72
        for step in CHECKPOINTS[1:]:
            prefix0 = members[0]["projection"][:step]
            if all(member["projection"][:step] == prefix0 for member in members[1:]):
                shared = step
            else:
                break
        family = {
            "physical_prefix72_sha256": digest,
            "member_count": len(members),
            "member_ranks": [item["rank"] for item in members],
            "member_tape_ids": [item["tape_id"] for item in members],
            "member_episode_ids": [item["episode_id"] for item in members],
            "best_rank": members[0]["rank"],
            "maximum_shared_prefix_checkpoint": shared,
            "shop_histories": {str(item["rank"]): item["shop_history"] for item in members},
        }
        family_rows.append(family)
        families.append(members)
    ordered = sorted(zip(family_rows, families),
                     key=lambda pair: (-pair[0]["member_count"],
                                       -pair[0]["maximum_shared_prefix_checkpoint"],
                                       pair[0]["best_rank"],
                                       pair[0]["member_ranks"]))
    return [pair[1] for pair in ordered], [pair[0] for pair in ordered]


ROUTER_TEMPLATE = r'''"""Standalone fresh-opening tape router; static development data only."""
import base64
import copy
import json
import zlib

_PACKED = "__PACKED__"
_TAPES = json.loads(zlib.decompress(base64.b85decode(_PACKED)).decode("utf-8"))
_TAPES = {int(tape["rank"]): tape for tape in _TAPES}
_BASE_RANK = __BASE_RANK__
_ACTIVE_RANK = _BASE_RANK
_CALLS = 0
_CHECKPOINTS = (72, 144, 216, 288, 360, 432, 504, 576, 648)


def _get(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)


def _physical(action):
    market = action.get("market", []) or []
    return {
        "farmer": action.get("farmer", []),
        "hands": action.get("hands", []),
        "market": [order for order in market
                   if not order or order[0] not in ("SELL", "BUY_PRODUCT")],
    }


def _prefix_matches(candidate, active, step):
    return all(_physical(candidate["actions"][i]) == _physical(active["actions"][i])
               for i in range(step))


def _shops_match_only_through_now(candidate, step, visible_shops):
    visible_shops = list(visible_shops or [])
    for checkpoint in _CHECKPOINTS:
        if checkpoint > step:
            break
        visible_count = min(checkpoint // 72, len(visible_shops))
        expected_visible_prefix = visible_shops[:visible_count]
        if candidate["shop_history"].get(str(checkpoint)) != expected_visible_prefix:
            return False
    return True


def agent(observation, configuration=None):
    del configuration
    global _ACTIVE_RANK, _CALLS
    raw_step = _get(observation, "step", None)
    try:
        step = int(raw_step) if raw_step is not None else _CALLS
    except (TypeError, ValueError):
        step = _CALLS
    _CALLS += 1
    step = max(0, min(step, 718))
    if step == 0:
        _ACTIVE_RANK = _BASE_RANK
    elif step in _CHECKPOINTS:
        town = _get(observation, "town", {}) or {}
        visible_shops = _get(town, "unlocked_shops", []) or []
        active = _TAPES[_ACTIVE_RANK]
        eligible = [
            tape for tape in _TAPES.values()
            if _prefix_matches(tape, active, step)
            and _shops_match_only_through_now(tape, step, visible_shops)
        ]
        if eligible:
            selected = min(eligible, key=lambda tape: int(tape["rank"]))
            _ACTIVE_RANK = int(selected["rank"])
    return copy.deepcopy(_TAPES[_ACTIVE_RANK]["actions"][step])


def kaggle_fresh_opening_router_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''


def main() -> None:
    _, tapes, load_receipt = load_source()
    ordered_families, family_rows = select_families(tapes)
    if not ordered_families:
        raise RuntimeError("No multi-tape coherent physical opening family exists; stop.")
    selected_families = ordered_families[:MAX_CANDIDATES]
    selected_family_rows = family_rows[:MAX_CANDIDATES]
    candidate_receipts = []

    for index, (members, family_info) in enumerate(zip(selected_families, selected_family_rows), start=1):
        base = members[0]
        # Keep episode identity in the provenance manifest only.  The
        # executable candidate's filename and embedded policy data should not
        # carry source episode IDs.
        label = f"family{index:02d}_rank{base['rank']}"
        candidate_path = HERE / f"candidate_{index:02d}_{safe_slug(label)}.py"
        packed_data = []
        for tape in members:
            packed_data.append({key: tape[key] for key in ("rank", "shop_history", "actions")})
        packed = base64.b85encode(zlib.compress(canonical(packed_data), level=9)).decode("ascii")
        source = ROUTER_TEMPLATE.replace("__PACKED__", packed).replace("__BASE_RANK__", str(base["rank"]))
        candidate_path.write_text(source, encoding="utf-8")
        candidate_bytes = candidate_path.read_bytes()
        candidate_receipts.append({
            "candidate_id": index,
            "candidate_path": str(candidate_path.resolve()),
            "candidate_sha256": sha(candidate_bytes),
            "candidate_bytes": len(candidate_bytes),
            "base_rank": base["rank"],
            "base_tape_id": base["tape_id"],
            "base_team": base["team"],
            "base_team_id": base["team_id"],
            "base_episode_id": base["episode_id"],
            "family": family_info,
            "embedded_tape_count": len(packed_data),
            "policy_payload_fields": ["rank", "shop_history", "actions"],
            "policy_uses_seed_or_opponent_identity": False,
            "embedded_tapes": [{key: tape[key] for key in (
                "tape_id", "rank", "team", "team_id", "submission_id", "episode_id", "seed",
                "source_seat", "action_sha256", "replay_sha256", "route_path", "replay_path")}
                for tape in packed_data],
        })

    analysis = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Static development-tape architecture analysis only; no episode outcomes, reserved tiers, games, or network calls.",
        "source_summary": str(SUMMARY.resolve()),
        "source_summary_sha256": load_receipt["source_summary_sha256"],
        "source_snapshot_utc": "2026-09-29T17:04:25.099949+00:00",
        "source_rows": len(tapes),
        "physical_projection": "Per action preserve farmer and hands; preserve the ordered market list after dropping only SELL and BUY_PRODUCT. All other orders and their relative order are retained.",
        "family_count_ge2": len(family_rows),
        "all_multi_tape_families": family_rows,
        "family_selection_order": "descending family size; descending maximum shared physical-prefix unlock checkpoint; ascending best frozen leaderboard rank; ascending rank list",
        "selected_candidates": candidate_receipts,
        "limitations": [
            "Families are based on fixed public action tapes and are architecture input only, not validation.",
            "Selecting a historical tape is a fixed schedule; future behavior is only revised at visible shop-unlock boundaries when the stated prefix/shop guards pass.",
            "No outcomes, seed identity, opponent identity/actions, or future shops are embedded as selection keys.",
            "Exact rival submission IDs are irrelevant to these already sourced top-100 team routes and are not used.",
        ],
    }
    analysis_path = HERE / "family_analysis.json"
    analysis_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"family_count_ge2": len(family_rows),
                      "family_order": [{"ranks": x["member_ranks"],
                                        "shared_prefix": x["maximum_shared_prefix_checkpoint"],
                                        "best_rank": x["best_rank"]} for x in family_rows],
                      "selected": [{"path": x["candidate_path"], "sha256": x["candidate_sha256"],
                                    "base_rank": x["base_rank"], "family_ranks": x["family"]["member_ranks"]}
                                   for x in candidate_receipts],
                      "analysis": str(analysis_path.resolve())}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
