"""AST/embedded-data and first-action checks; no simulator or game is run."""

from __future__ import annotations

from datetime import datetime, timezone
import ast
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCE_DIR = HERE.parents[0] / "fresh90_refresh_20260929"
SUMMARY_PATH = SOURCE_DIR / "routes" / "development_latest" / "summary.json"
EXPECTED_SUMMARY_SHA = "9dc48578eb5e828d8038ff39821c8e27ddb12b1a7a4812a87622003c2db63e9c"
ALLOWED_IMPORTS = {"base64", "copy", "json", "zlib"}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    frozen_plan_sha = sha((HERE / "PLAN.md").read_bytes())
    plan_record = (HERE / "PLAN_SHA256.txt").read_text(encoding="utf-8").splitlines()[0].split()[0].lower()
    if frozen_plan_sha != plan_record:
        raise RuntimeError("PLAN.md hash changed after freeze")
    source_sha = sha(SUMMARY_PATH.read_bytes())
    if source_sha != EXPECTED_SUMMARY_SHA:
        raise RuntimeError("development source summary hash changed")
    source_rows = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    source_by_key = {(int(row["rank"]), int(row["episode_id"])): row for row in source_rows}
    analysis = json.loads((HERE / "family_analysis.json").read_text(encoding="utf-8"))
    if analysis["source_summary_sha256"] != source_sha:
        raise RuntimeError("family analysis source hash mismatch")
    sys.path.insert(0, str(HERE))
    import build_candidates

    verified_sources = {}

    def verify_input_source(row, descriptor, declared):
        key = (int(row["rank"]), int(row["episode_id"]))
        if key in verified_sources:
            return verified_sources[key]
        if not row.get("runner_eligible") or row.get("frames") != 720:
            raise RuntimeError(f"source row is not runner-eligible: {key}")
        if row.get("source_statuses") != ["DONE", "DONE"] or row.get("engine_version") != "1.32.7":
            raise RuntimeError(f"source engine/status mismatch: {key}")

        route_path = Path(row["path"])
        route_payload = json.loads(gzip.decompress(route_path.read_bytes()))
        actions = route_payload["actions"]
        action_hash = sha(json.dumps(actions, sort_keys=True, separators=(",", ":"),
                                  ensure_ascii=False).encode("utf-8"))
        if len(actions) != 719 or action_hash != row["action_sha256"]:
            raise RuntimeError(f"source route/hash mismatch: {key}")

        replay_path = Path(row["replay_path"])
        replay_archive_sha = sha(replay_path.read_bytes())
        replay_raw = gzip.decompress(replay_path.read_bytes())
        replay_sha = sha(replay_raw)
        replay = build_candidates.decode_replay(replay_raw)
        seat = int(row["source_seat"])
        team_names = (replay.get("info") or {}).get("TeamNames") or []
        if replay_archive_sha != row["replay_archive_sha256"] or replay_sha != row["replay_sha256"]:
            raise RuntimeError(f"source replay hash mismatch: {key}")
        if replay.get("statuses") != ["DONE", "DONE"] or replay.get("module_version") != "1.32.7":
            raise RuntimeError(f"raw replay status/engine mismatch: {key}")
        if len(replay.get("steps") or []) != 720 or len(team_names) != 2 or team_names[seat] != row["team"]:
            raise RuntimeError(f"raw replay frame/seat mismatch: {key}")

        index_path = Path(row["public_state_index_path"])
        index_archive_sha = sha(index_path.read_bytes())
        index_raw = gzip.decompress(index_path.read_bytes())
        index_sha = sha(index_raw)
        index = json.loads(index_raw)
        if index_archive_sha != row["public_state_index_sha256"]:
            raise RuntimeError(f"public-state index hash mismatch: {key}")
        if index["action_sha256_by_seat"][str(seat)] != action_hash:
            raise RuntimeError(f"public-state index action mismatch: {key}")

        state_path = Path(row["public_state_path"])
        state_archive_sha = sha(state_path.read_bytes())
        state_raw = gzip.decompress(state_path.read_bytes())
        state_sha = sha(state_raw)
        timeline = json.loads(state_raw)
        if state_sha != row["public_state_sha256"] or len(timeline) != 720:
            raise RuntimeError(f"public-state sidecar hash/frame mismatch: {key}")
        family_history = declared["family"]["shop_histories"][str(row["rank"])]
        for checkpoint in range(72, 649, 72):
            shops = list(timeline[checkpoint]["states"][seat].get("town", {}).get("unlocked_shops", []))
            if shops != family_history[str(checkpoint)]:
                raise RuntimeError(f"visible-shop history mismatch for {key} at {checkpoint}")

        if str(route_path.resolve()) != str(Path(descriptor["route_path"]).resolve()):
            raise RuntimeError(f"route path provenance mismatch: {key}")
        if str(replay_path.resolve()) != str(Path(descriptor["replay_path"]).resolve()):
            raise RuntimeError(f"replay path provenance mismatch: {key}")
        verified = {
            "rank": int(row["rank"]), "team_id": row.get("team_id"),
            "submission_id": row.get("submission_id"), "episode_id": int(row["episode_id"]),
            "source_seat": seat, "engine_version": row["engine_version"],
            "frames": 720, "action_sha256": action_hash,
            "replay_archive_sha256": replay_archive_sha, "replay_sha256": replay_sha,
            "public_state_index_archive_sha256": index_archive_sha,
            "public_state_index_content_sha256": index_sha,
            "public_state_index_sha256_from_source_summary": row["public_state_index_sha256"],
            "public_state_archive_sha256": state_archive_sha,
            "public_state_sha256": state_sha,
            "route_path": str(route_path.resolve()), "replay_path": str(replay_path.resolve()),
            "public_state_index_path": str(index_path.resolve()),
            "public_state_path": str(state_path.resolve()),
        }
        verified_sources[key] = verified
        return verified

    validated = []
    for declared in analysis["selected_candidates"]:
        path = Path(declared["candidate_path"])
        raw = path.read_bytes()
        actual_hash = sha(raw)
        if actual_hash != declared["candidate_sha256"]:
            raise RuntimeError(f"candidate source hash mismatch: {path.name}")
        tree = ast.parse(raw.decode("utf-8"), filename=str(path))
        compile(tree, str(path), "exec")
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        if not imports <= ALLOWED_IMPORTS:
            raise RuntimeError(f"unexpected candidate imports in {path.name}: {imports - ALLOWED_IMPORTS}")
        for required in ("agent", "_physical", "_prefix_matches", "_shops_match_only_through_now"):
            if not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == required
                       for node in tree.body):
                raise RuntimeError(f"missing router function {required!r} in {path.name}")

        spec = importlib.util.spec_from_file_location(f"fresh_candidate_{declared['candidate_id']}", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not load candidate module {path.name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        base = module._TAPES[int(module._BASE_RANK)]
        rank_key = (int(declared["base_rank"]), int(declared["base_episode_id"]))
        source = source_by_key.get(rank_key)
        if source is None:
            raise RuntimeError(f"base tape not in frozen source at {path.name}")
        if source["action_sha256"] != sha(json.dumps(base["actions"], sort_keys=True,
                                                       separators=(",", ":"), ensure_ascii=False).encode("utf-8")):
            raise RuntimeError(f"base action hash mismatch at {path.name}")
        if len(base["actions"]) != 719:
            raise RuntimeError(f"base route is not a complete tape at {path.name}")
        first_action = module.agent({"step": 0, "town": {"unlocked_shops": []}}, None)
        if first_action != base["actions"][0]:
            raise RuntimeError(f"step-0 policy action mismatch at {path.name}")

        declared_tapes = {int(tape["rank"]): tape for tape in declared["embedded_tapes"]}
        if set(module._TAPES) != set(declared_tapes):
            raise RuntimeError(f"embedded rank set mismatch at {path.name}")
        embedded = []
        for tape in module._TAPES.values():
            descriptor = declared_tapes[int(tape["rank"])]
            route_source = source_by_key.get((int(tape["rank"]), int(descriptor["episode_id"])))
            if route_source is None:
                raise RuntimeError(f"source row missing for embedded rank {tape['rank']}")
            verified_source = verify_input_source(route_source, descriptor, declared)
            action_hash = sha(json.dumps(tape["actions"], sort_keys=True,
                                         separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
            if route_source is None or route_source["action_sha256"] != action_hash \
                    or descriptor["action_sha256"] != action_hash:
                raise RuntimeError(f"embedded tape/source mismatch at {path.name}: rank {tape.get('rank')}")
            if len(tape["actions"]) != 719:
                raise RuntimeError(f"incomplete embedded route at {path.name}")
            if set(tape) != {"rank", "shop_history", "actions"}:
                raise RuntimeError(f"candidate policy embeds identity or unapproved fields at {path.name}")
            embedded.append({**verified_source, "candidate_action_sha256": action_hash})

        validated.append({
            "candidate_id": declared["candidate_id"],
            "path": str(path.resolve()),
            "sha256": actual_hash,
            "ast_parse": True,
            "compile": True,
            "imports": sorted(imports),
            "embedded_complete_tapes": len(embedded),
            "embedded_tapes": embedded,
            "base_tape_id": f"{int(module._BASE_RANK)}:{int(declared['base_episode_id'])}",
            "base_rank": declared["base_rank"],
            "base_team": declared["base_team"],
            "first_action_matches_source_route": True,
            "first_action_sha256": sha(json.dumps(first_action, sort_keys=True,
                                                   separators=(",", ":"), ensure_ascii=False).encode("utf-8")),
        })

    result = {
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "plan_sha256": frozen_plan_sha,
        "source_summary_sha256": source_sha,
        "candidate_results": validated,
        "checks": {
            "source_rows": len(source_rows),
            "selected_route_replay_sidecar_provenance_verified": len(verified_sources),
            "candidate_count": len(validated),
            "outcome_fields_used": False,
            "reserved_episode_2_or_3_read": False,
            "network_calls": 0,
            "game_runs": 0,
            "simulator_imported": False,
            "first_action_calls_per_candidate": 1,
        },
    }
    receipt_path = HERE / "candidate_validation.json"
    receipt_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"validation_receipt": str(receipt_path.resolve()),
                      "plan_sha256": frozen_plan_sha,
                      "source_summary_sha256": source_sha,
                      "candidate_results": [{"candidate_id": row["candidate_id"], "path": row["path"],
                                             "sha256": row["sha256"],
                                             "first_action_matches_source_route": row["first_action_matches_source_route"],
                                             "tapes": row["embedded_complete_tapes"]}
                                            for row in validated],
                      "checks": result["checks"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
