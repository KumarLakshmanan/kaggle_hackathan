"""Static-only audit for the separately staged exact-8f Roman adapter.

This module reads and hashes frozen files, parses Python with ``ast``, and
decodes literal gzip/JSON/route data. It never imports or calls an agent,
simulator, transition, Kaggle client, or game runner.
"""
from __future__ import annotations

import ast
import base64
import gzip
import hashlib
import json
import pathlib
import zlib
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
P = lambda value: ROOT / pathlib.Path(value)

FILES = {
    "candidate_8f": P("diagnostics/a44_ghost_kwa_piice_combo_20260929/candidate.py"),
    "candidate_parent_8f_copy": P("diagnostics/a44_ghost_kwa_piice_combo_20260929/candidate_parent.py"),
    "candidate_base_7b": P("diagnostics/a44_ghost_kwa_combo_20260929/candidate_v4.py"),
    "parent_source_a44": P("diagnostics/a44_source_bridge_goose_4leaf_20260929/source_a44.py"),
    "feature_panel_208": P("diagnostics/a44_source_bridge_goose_4leaf_20260929/feature_rows.json"),
    "candidate_8f_panel": P("diagnostics/a44_ghost_kwa_piice_combo_20260929/panel.json"),
    "candidate_8f_manifest": P("diagnostics/a44_ghost_kwa_piice_combo_20260929/frozen_manifest.json"),
    "candidate_8f_outcome_receipt": P("diagnostics/a44_ghost_kwa_piice_combo_20260929/outcome_receipt.json"),
    "candidate_8f_parent_receipts": P("diagnostics/a44_ghost_kwa_piice_combo_20260929/parent_receipts.json"),
    "candidate_8f_static_preflight": P("diagnostics/a44_ghost_kwa_piice_combo_20260929/static_preflight.json"),
    "candidate_8f_outcomes": P("diagnostics/a44_ghost_kwa_piice_combo_20260929/outcomes.jsonl"),
    "donor_shared166": P("diagnostics/donor_opening_agents_20260928/candidate_shared166.py"),
    "donor_shared151": P("diagnostics/donor_opening_agents_20260928/candidate_shared151.py"),
    "donor_obligations": P("diagnostics/donor_opening_agents_20260928/INITIAL_OBLIGATIONS.md"),
    "donor_pool": P("diagnostics/adaptive_donor_pair_repair_20260928/pool.json"),
    "donor_full_pool": P("diagnostics/adaptive_donor_pair_repair_20260928/full_pool.json"),
    "raw_replay": P("diagnostics/new_live_56609430_20260927/raw/episode-114270587-replay.json.gz"),
    "raw_replay_receipt": P("diagnostics/new_live_56609430_20260927/raw/episode-114270587-receipt.json"),
    "matched_opponent_tape": P("diagnostics/loss_class_20260927/routes/episode-114270587-seat1.json.gz"),
    "loss_events": P("diagnostics/loss_class_20260927/traces/episode-114270587-seat1-events.json.gz"),
    "target_parent_trace_seat0": P("diagnostics/adaptive_donor_pair_repair_20260928/full_live-114270587_seat0.jsonl.gz"),
    "target_parent_trace_seat1": P("diagnostics/adaptive_donor_pair_repair_20260928/full_live-114270587_seat1.jsonl.gz"),
    "target_residual_trace_seat0": P("diagnostics/residual_execution_20260928/live-114270587_seat0.jsonl.gz"),
    "target_residual_receipt_seat0": P("diagnostics/residual_execution_20260928/live-114270587_seat0.jsonl.gz.receipt.json"),
    "target_residual_trace_seat1": P("diagnostics/residual_execution_20260928/live-114270587_seat1.jsonl.gz"),
    "target_residual_receipt_seat1": P("diagnostics/residual_execution_20260928/live-114270587_seat1.jsonl.gz.receipt.json"),
    "donor166_trace_seat0": P("diagnostics/donor_opening_agents_20260928/full_shared166_live-114270587_seat0.jsonl.gz"),
    "donor166_trace_seat1": P("diagnostics/donor_opening_agents_20260928/full_shared166_live-114270587_seat1.jsonl.gz"),
    "donor151_trace_seat0": P("diagnostics/donor_opening_agents_20260928/full_shared151_live-114270587_seat0.jsonl.gz"),
    "donor151_trace_seat1": P("diagnostics/donor_opening_agents_20260928/full_shared151_live-114270587_seat1.jsonl.gz"),
    "adapter_layer": HERE / "adapter_layer.py",
}

EXPECTED_SHA256 = {
    "candidate_8f": "8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62",
    "candidate_parent_8f_copy": "7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2",
    "candidate_base_7b": "7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2",
    "parent_source_a44": "a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f",
    "feature_panel_208": "bfd178472afd40c6b457e794dbde6d5d045440fd3b2c6cb40e658c9f7a26d795",
    "candidate_8f_panel": "ecf09fbde109bc13922f16851257939923ada9f158dc4e33c2e5e6b1a0f4b247",
    "candidate_8f_outcome_receipt": "7d9e9ae29f420e361aec8c3d060089eb8dd969416bf2b65cb2fd23812fada14e",
    "candidate_8f_parent_receipts": "27ea7f63a0b922dee521d323536f75d4f3650bc9e48a89f0da57ab3e04ea211d",
    "candidate_8f_static_preflight": "d6940502e6c2c0c4e8892f76e47fac848ecf3dcaac30479969b7735408cfc9df",
    "candidate_8f_outcomes": "459065b14277c58c08f8ab577cc15bf592e8cb26f11f88b5af07a46504ab5ea7",
    "donor_shared166": "fc403d05e29b1b317985f7ec77d1a3fa490c0264af8d639c3bfea899fcf1a849",
    "donor_shared151": "2635662c20d1d2c70079fb9ba063831d8863ec1e5f670c37c7bdac4b89f5ca2a",
    "donor_obligations": "e8a30db9e26e77a81ac01720cb23eca58d234a9229a08aca23b62ea4ec0717f5",
    "donor_pool": "8dbb99617d72585b75ee9f2b19d6254f51e30d59bdedc4ea75612919595bdaf2",
    "donor_full_pool": "4d0a74d3c897891d182d80948a1d8b79d761855147098ad4a6b7d763e068af5d",
    "raw_replay": "3b93e403b761ebf6aac26884ec86fbb7abd151730a6c3201401f8c2ff5aa68e5",
    "raw_replay_receipt": "a43ef6128d0dbecd0e1822566d5664fb18674289fd923b6bdf0810b9ccf18382",
    "matched_opponent_tape": "18ba3ec92eec0ec7bab95498119eebae88e7ce0ca4571eba42ffbaeb9ddda4b1",
    "loss_events": "5cb58667b3093864397de39e70c8f9e9527711692adf420b3af6f84e2f058ee9",
    "target_parent_trace_seat0": "7505703872cc3ce80799e08f50e4c3a9649f20d32cc518cbe12329b8f8c3d2ac",
    "target_parent_trace_seat1": "f7afeedbfc2dcc11818ab8553ca2ef65518202363c6954f9f24eacb77a6f27ea",
    "target_residual_trace_seat0": "ed291f63f3edb8892844b76433fa8e21cfcf5290e791ad33020a069fedd3fc3d",
    "target_residual_receipt_seat0": "02b0d527c91f3b59ef288ae55af18c7be974fa789ed738a917ec71ab67c04dc2",
    "target_residual_trace_seat1": "90ecce3f214621aea4f9a963d09e634f784acf863c7b891c7cbaea6dedf1feb9",
    "target_residual_receipt_seat1": "efa5579bcd7a8c0cb80eff29d9f93d54a2f76646379eed8dd9f31eca3b14462e",
    "donor166_trace_seat0": "6eb2952e5c931b201fe72e457f8eac2c5ecbf21454f43fc18ad20881e7360e9d",
    "donor166_trace_seat1": "1885ab9d8ab0435dc9f26fc334208950bc799cf16f5cb7107a0ce7f69063cd1f",
    "donor151_trace_seat0": "0a02fe23eabb3cb6028f5b41bdea8f1ceb107a2272599ca50ed4e782ed1a886f",
    "donor151_trace_seat1": "1cf84dacd42317f6f2b51575af2ecbc47bf25f26de8f32e4b554bfc55d0a0948",
}

TARGET_TRACE_EXPECTED = {
    0: EXPECTED_SHA256["target_parent_trace_seat0"],
    1: EXPECTED_SHA256["target_parent_trace_seat1"],
}
ADAPTER_STEP1_ACTION = {
    "farmer": ["NORTH"],
    "hands": [["PASS"], ["PASS"], ["PASS"], ["PASS"]],
    "market": [["HIRE"]],
}
OPPONENT_ACTION_TAPE_SHA256 = EXPECTED_SHA256["matched_opponent_tape"]
OPPONENT_ACTION_INDEX = 1
OPPONENT_ACTION_SHA256 = "48e7b680c2f75b6a1d838749d1289420710bd6fb05c27275c9f2c38ac26769ff"
ADAPTER_ACTION_SHA256 = "22ab294d18251d7ce475cd29261d151a7301c3c6ff9eb32315832ed7aba9cb15"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value) -> str:
    blob = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def trace_path_from_row(row: dict) -> pathlib.Path:
    raw = pathlib.Path(row["trace_path"])
    if raw.exists():
        return raw
    normalized = str(row["trace_path"]).replace("/", "\\")
    marker = "diagnostics\\"
    if marker.casefold() not in normalized.casefold():
        raise FileNotFoundError(row["trace_path"])
    split_at = normalized.casefold().index(marker.casefold())
    return ROOT / "diagnostics" / normalized[split_at + len(marker):]


def trace_records(path: pathlib.Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def record_at(records: list[dict], step: int) -> dict:
    found = [record for record in records if int(record["step"]) == step]
    if len(found) != 1:
        raise AssertionError(f"expected one record at step {step}, found {len(found)}")
    return found[0]


def decode_donor_routes(path: pathlib.Path) -> tuple[dict, dict]:
    """Decode only a literal route blob; no candidate function is executed."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    decode_call = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "b85decode"
    )
    packed = ast.literal_eval(decode_call.args[0])
    routes = json.loads(zlib.decompress(base64.b85decode(packed)))
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"_DONOR_DEFAULT", "_DONOR_MAP"}:
                    constants[target.id] = ast.literal_eval(node.value)
    return routes, constants


def main() -> None:
    hashes = {name: sha256(path) for name, path in FILES.items()}
    for name, expected in EXPECTED_SHA256.items():
        if hashes.get(name) != expected:
            raise AssertionError(f"frozen {name} hash mismatch: {hashes.get(name)} != {expected}")

    # These checks parse source only; they do not import it or call any agent.
    for name in ("candidate_8f", "candidate_parent_8f_copy", "candidate_base_7b", "donor_shared166", "donor_shared151", "adapter_layer"):
        ast.parse(FILES[name].read_text(encoding="utf-8"), filename=str(FILES[name]))
    parent_7b_bytes = FILES["candidate_base_7b"].read_bytes()
    if FILES["candidate_parent_8f_copy"].read_bytes() != parent_7b_bytes:
        raise AssertionError("8f parent source copy is no longer byte-identical to frozen 7b")
    candidate_8f_bytes = FILES["candidate_8f"].read_bytes()
    if not candidate_8f_bytes.startswith(parent_7b_bytes):
        raise AssertionError("8f source no longer preserves the exact 7b source prefix")

    manifest = json.loads(FILES["candidate_8f_manifest"].read_text(encoding="utf-8"))
    if manifest.get("candidate_sha256") != EXPECTED_SHA256["candidate_8f"]:
        raise AssertionError("8f manifest candidate binding changed")
    if manifest.get("parent_candidate_sha256") != EXPECTED_SHA256["candidate_base_7b"]:
        raise AssertionError("8f manifest parent binding changed")
    if manifest.get("reactive_validation") is not False or manifest.get("promotion") is not False:
        raise AssertionError("8f outcome manifest no longer describes diagnostic-only evidence")
    outcome_receipt = json.loads(FILES["candidate_8f_outcome_receipt"].read_text(encoding="utf-8"))
    if outcome_receipt.get("candidate_sha256") != EXPECTED_SHA256["candidate_8f"]:
        raise AssertionError("8f outcome receipt candidate binding changed")
    if outcome_receipt.get("parent_candidate_sha256") != EXPECTED_SHA256["candidate_base_7b"]:
        raise AssertionError("8f outcome receipt parent binding changed")
    if outcome_receipt.get("panel_sha256") != EXPECTED_SHA256["candidate_8f_panel"]:
        raise AssertionError("8f outcome receipt panel binding changed")
    outcome_rows = [json.loads(line) for line in FILES["candidate_8f_outcomes"].read_text(encoding="utf-8").splitlines() if line.strip()]
    outcome_fixtures = sorted({row["fixture_id"] for row in outcome_rows})
    if any(row.get("candidate_sha256") != EXPECTED_SHA256["candidate_8f"] for row in outcome_rows):
        raise AssertionError("8f outcome row candidate binding changed")
    if "live-114270587" in outcome_fixtures:
        raise AssertionError("8f test panel unexpectedly claims a Roman target trace")

    panel = json.loads(FILES["feature_panel_208"].read_text(encoding="utf-8"))
    if panel.get("source_a44_sha256") != EXPECTED_SHA256["parent_source_a44"]:
        raise AssertionError("208-row panel historical source binding changed")
    rows = panel.get("rows", [])
    if len(rows) != 208:
        raise AssertionError(f"expected 208 rows, found {len(rows)}")

    census = []
    trace_hashes = {}
    trace_paths = {}
    for row in rows:
        path = trace_path_from_row(row)
        actual_sha = sha256(path)
        if actual_sha != row["trace_sha256"]:
            raise AssertionError(f"panel trace hash changed for {row['fixture_id']} seat {row['seat']}")
        key = f"{row['fixture_id']}|seat{int(row['seat'])}"
        trace_hashes[key] = actual_sha
        trace_paths[key] = path
        obs = record_at(trace_records(path), 1)["observation"]
        player = int(obs["player"])
        if player != int(row["seat"]):
            raise AssertionError(f"panel seat mismatch in {key}: obs player {player}")
        own, rival = obs["farms"][player], obs["farms"][1 - player]
        census.append({
            "fixture_id": row["fixture_id"],
            "panel": row["panel"],
            "seat": int(row["seat"]),
            "rival_hand_count": len(rival.get("hands", [])),
            "rival_farmer": rival.get("farmer"),
            "own_farmer": own.get("farmer"),
            "own_hand_count": len(own.get("hands", [])),
            "own_hires_today": own.get("hires_today"),
            "own_cash": own.get("money"),
            "trace_sha256": actual_sha,
        })

    triggered = [row for row in census if row["rival_hand_count"] == 3 and row["rival_farmer"] == [4, 3]]
    near_three_stationary = [row for row in census if row["rival_hand_count"] == 3 and row["rival_farmer"] == [4, 4]]
    near_four_other_move = [row for row in census if row["rival_hand_count"] == 4 and row["rival_farmer"] == [3, 4]]
    expected_trigger = {"live-114270587|seat0", "live-114270587|seat1"}
    actual_trigger = {f"{row['fixture_id']}|seat{row['seat']}" for row in triggered}
    if actual_trigger != expected_trigger or len(near_three_stationary) != 6 or len(near_four_other_move) != 4:
        raise AssertionError("208-row trigger/near-miss census changed")
    for seat, expected in TARGET_TRACE_EXPECTED.items():
        if trace_hashes.get(f"live-114270587|seat{seat}") != expected:
            raise AssertionError(f"target source trace seat {seat} hash changed")

    raw_replay = json.load(gzip.open(FILES["raw_replay"], "rt", encoding="utf-8"))
    action_tape = json.load(gzip.open(FILES["matched_opponent_tape"], "rt", encoding="utf-8"))
    tape_actions = action_tape["actions"]
    if len(tape_actions) <= OPPONENT_ACTION_INDEX:
        raise AssertionError("matched opponent tape too short")
    if tape_actions[0] != raw_replay["steps"][1][0]["action"]:
        raise AssertionError("tape action 0 no longer matches raw replay step 1 player 0")
    if tape_actions[OPPONENT_ACTION_INDEX] != raw_replay["steps"][2][0]["action"]:
        raise AssertionError("tape action 1 no longer matches raw replay step 2 player 0")
    action_hash = canonical_sha256(tape_actions[OPPONENT_ACTION_INDEX])
    if action_hash != OPPONENT_ACTION_SHA256:
        raise AssertionError(f"matched opponent action hash changed: {action_hash}")

    # Rebind every available historical Roman parent trace to the saved public
    # replay. These are a44 traces; their step-2 snapshots are controls only.
    historical_snapshots = []
    for seat in (0, 1):
        path = FILES[f"target_parent_trace_seat{seat}"]
        records = trace_records(path)
        step1 = record_at(records, 1)
        step2 = record_at(records, 2)
        obs1, obs2 = step1["observation"], step2["observation"]
        player = int(obs2["player"])
        historical_rival1 = obs1["farms"][1 - int(obs1["player"])]
        historical_rival2 = obs2["farms"][1 - player]
        raw_step1 = raw_replay["steps"][1][1]["observation"]
        raw_step2 = raw_replay["steps"][2][1]["observation"]
        if historical_rival1 != raw_step1["farms"][1 - int(raw_step1["player"])]:
            raise AssertionError(f"historical step-1 rival farm no longer matches raw public control, seat {seat}")
        if historical_rival2 != raw_step2["farms"][1 - int(raw_step2["player"])]:
            raise AssertionError(f"historical step-2 rival farm no longer matches raw public control, seat {seat}")
        if obs1["market"] != raw_step1["market"] or obs2["market"] != raw_step2["market"]:
            raise AssertionError(f"historical market no longer matches raw public control, seat {seat}")
        source_action = step1["action"]
        if source_action == ADAPTER_STEP1_ACTION or len(source_action.get("market", [])) != 6:
            raise AssertionError(f"historical parent step-1 action changed, seat {seat}")
        historical_snapshots.append({
            "seat": seat,
            "trace_sha256": sha256(path),
            "source_step1_action_sha256": canonical_sha256(source_action),
            "source_step1_market_order_count": len(source_action.get("market", [])),
            "source_step1_action_is_adapter_hire": False,
            "step1_rival_farm": historical_rival1,
            "step1_market": obs1["market"],
            "step2_rival_farm": historical_rival2,
            "step2_market": obs2["market"],
            "matches_raw_replay_p1_public_control_steps_1_2": True,
            "valid_for_adapter": False,
            "invalid_reason": "source took six market orders; adapter takes only HIRE, so the step-2 market and rival response can differ",
        })

    # Bind the residual native target traces to their receipts; these arose
    # from the earlier 8dde candidate and are not exact 8f traces.
    residual_receipts = {}
    for seat in (0, 1):
        trace_key = f"target_residual_trace_seat{seat}"
        receipt_key = f"target_residual_receipt_seat{seat}"
        receipt = json.loads(FILES[receipt_key].read_text(encoding="utf-8"))
        game = receipt.get("game", {})
        if game.get("candidate_sha256") != "8dde995de6430dcdb7c3dae57bc7a42885ea1b230583c9b0eaf062d1361d3432":
            raise AssertionError(f"residual seat {seat} receipt candidate changed")
        if game.get("trace_sha256") != hashes[trace_key]:
            raise AssertionError(f"residual seat {seat} receipt trace binding changed")
        residual_receipts[str(seat)] = {
            "candidate_sha256": game["candidate_sha256"],
            "result": game.get("result"),
            "margin": game.get("margin"),
            "trace_sha256": game["trace_sha256"],
            "receipt_sha256": hashes[receipt_key],
            "exact_8f_trace": False,
        }

    # Decode donor literal schedules without importing or running their agents.
    routes, route_constants = decode_donor_routes(FILES["donor_shared166"])
    if set(routes) != {"route0", "route1"} or len(routes["route0"]) != 719 or len(routes["route1"]) != 719:
        raise AssertionError("shared166 route tables changed")
    common_prefix = next((i for i, pair in enumerate(zip(routes["route0"], routes["route1"])) if pair[0] != pair[1]), 719)
    if common_prefix != 166 or route_constants.get("_DONOR_DEFAULT") != "route0":
        raise AssertionError("shared166 route prefix/default changed")
    if routes["route0"][2] != routes["route1"][2]:
        raise AssertionError("donor step-2 action ceased to be shared")
    if route_constants.get("_DONOR_MAP") != {
        "PET_CAFE|FARMERS_MARKET": "route0",
        "ICE_CREAM_SHOP|PET_CAFE": "route1",
    }:
        raise AssertionError("donor observed-shop routing changed")

    # Static expected state is deliberately not promoted to verified state.
    # The adapter snapshot is None because no native run was allowed here.
    adapter_text = FILES["adapter_layer"].read_text(encoding="utf-8")
    if "expected_step2_public=None" not in adapter_text or "_has_bound_step2_public_snapshot(expected_step2_public)" not in adapter_text:
        raise AssertionError("adapter no longer defaults closed or validates before step 1")
    if ADAPTER_ACTION_SHA256 not in adapter_text:
        raise AssertionError("adapter step-1 action provenance hash is absent")
    if canonical_sha256(ADAPTER_STEP1_ACTION) != ADAPTER_ACTION_SHA256:
        raise AssertionError("adapter step-1 action canonical hash changed")

    histogram = Counter((row["rival_hand_count"], tuple(row["rival_farmer"])) for row in census)
    payload = {
        "passed": True,
        "static_only": True,
        "agent_calls": 0,
        "engine_transitions": 0,
        "games_run": 0,
        "kaggle_access": False,
        "main_py_or_agent_md_edited": False,
        "package": str(HERE.relative_to(ROOT)).replace("\\", "/"),
        "frozen_source_hashes": hashes,
        "source_lineage": {
            "candidate_8f_sha256": hashes["candidate_8f"],
            "candidate_8f_parent_prefix_sha256": hashlib.sha256(parent_7b_bytes).hexdigest(),
            "candidate_8f_starts_with_exact_7b_parent": True,
            "exact_parent_prefix_bytes": len(parent_7b_bytes),
            "8f_appended_bytes": len(candidate_8f_bytes) - len(parent_7b_bytes),
            "parent_copy_byte_identical_to_7b": True,
            "candidate_8f_test_fixtures": outcome_fixtures,
            "candidate_8f_test_rows": len(outcome_rows),
            "candidate_8f_outcome_fixtures": outcome_fixtures,
            "candidate_8f_has_roman_target_trace": False,
            "historical_panel_producer_sha256": panel["source_a44_sha256"],
        },
        "panel_208": {
            "row_count": len(rows),
            "unique_trace_count": len(trace_hashes),
            "all_trace_hashes_verified": True,
            "trace_hashes_by_fixture_and_seat": trace_hashes,
            "trigger_predicate": "step==1 and rival hands==3 and rival farmer==[4,3]",
            "trigger_rows": triggered,
            "trigger_count": len(triggered),
            "near_miss_three_hands_farmer_4_4_count": len(near_three_stationary),
            "near_miss_four_hands_farmer_3_4_count": len(near_four_other_move),
            "rival_opening_histogram": [
                {"hands": count, "farmer": list(position), "rows": count_rows}
                for (count, position), count_rows in sorted(histogram.items())
            ],
        },
        "matched_opponent_action": {
            "tape_file_sha256": hashes["matched_opponent_tape"],
            "action_index": OPPONENT_ACTION_INDEX,
            "canonical_action_sha256": action_hash,
            "action0_matches_raw_replay_step1_player0": True,
            "action1_matches_raw_replay_step2_player0": True,
        },
        "available_target_evidence": {
            "historical_a44_parent_traces": historical_snapshots,
            "residual_execution_traces": residual_receipts,
            "donor_shared166_trace_sha256_by_seat": {
                "0": hashes["donor166_trace_seat0"], "1": hashes["donor166_trace_seat1"]
            },
            "donor_shared151_trace_sha256_by_seat": {
                "0": hashes["donor151_trace_seat0"], "1": hashes["donor151_trace_seat1"]
            },
            "exact_8f_roman_per_turn_trace_available": False,
            "exact_8f_roman_step0_step1_step2_state_verified": False,
        },
        "donor_static_route_audit": {
            "routes": sorted(routes),
            "route_length": 719,
            "first_divergence_action_index": common_prefix,
            "common_action_indices": [0, common_prefix - 1],
            "default_route": route_constants["_DONOR_DEFAULT"],
            "step2_action": routes["route0"][2],
            "hand_remap_donor_slots_1_based_to_actual_slots_1_based": [4, 1, 2, 3, 5],
        },
        "adapter_step2_public_guard": {
            "required": ["full rival_farm", "full shared market", "matched opponent tape SHA", "matched opponent action index/hash", "adapter step/hash"],
            "rival_farm_keys": ["farmer", "hands", "hires_today", "money", "tiles", "unlocked_quadrants"],
            "market_keys": ["inventory", "prices"],
            "opponent_tape_sha256": OPPONENT_ACTION_TAPE_SHA256,
            "opponent_action_index": OPPONENT_ACTION_INDEX,
            "opponent_action_sha256": OPPONENT_ACTION_SHA256,
            "adapter_step": 1,
            "adapter_action_sha256": ADAPTER_ACTION_SHA256,
            "expected_adapter_step2_public_snapshot": None,
            "status": "FAIL_CLOSED_DISABLED_UNTIL_NATIVE_MATCHED_STEP1_SNAPSHOT",
            "step1_hire_spend_allowed_now": False,
        },
        "pending": [
            "exact 8f Roman step-0/step-1/step-2 trace and state parity",
            "post-adapter-HIRE full rival farm and shared-market snapshot after matched opponent action index 1",
            "native two-seat merge-state and donor-schedule verification",
            "paired Roman controls and reactive qualification after native opening validation",
        ],
        "decision": "STAGE_ONLY_DO_NOT_PROMOTE",
    }
    out = HERE / "preflight.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "passed": payload["passed"],
        "static_only": payload["static_only"],
        "candidate_8f_sha256": hashes["candidate_8f"],
        "candidate_parent_prefix_exact": payload["source_lineage"]["candidate_8f_starts_with_exact_7b_parent"],
        "panel_rows": len(rows),
        "trigger_rows": len(triggered),
        "near_misses": [len(near_three_stationary), len(near_four_other_move)],
        "exact_8f_roman_trace": payload["available_target_evidence"]["exact_8f_roman_per_turn_trace_available"],
        "adapter_snapshot": payload["adapter_step2_public_guard"]["status"],
        "preflight": str(out),
    }, indent=2))


if __name__ == "__main__":
    main()
