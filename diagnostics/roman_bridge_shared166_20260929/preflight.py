"""Reproducible static-only preflight; never imports or calls an agent/engine."""
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
FILES = {
    "parent_7b": ROOT / "diagnostics/a44_ghost_kwa_combo_20260929/candidate_v4.py",
    "donor_shared166": ROOT / "diagnostics/donor_opening_agents_20260928/candidate_shared166.py",
    "panel_208": ROOT / "diagnostics/a44_source_bridge_goose_4leaf_20260929/feature_rows.json",
    "obligation_audit": ROOT / "diagnostics/donor_opening_agents_20260928/INITIAL_OBLIGATIONS.md",
    "trace_pool": ROOT / "diagnostics/adaptive_donor_pair_repair_20260928/pool.json",
    "adapter_layer": HERE / "adapter_layer.py",
    "donor_trace_seat0": ROOT / "diagnostics/donor_opening_agents_20260928/full_shared166_live-114270587_seat0.jsonl.gz",
    "donor_trace_seat1": ROOT / "diagnostics/donor_opening_agents_20260928/full_shared166_live-114270587_seat1.jsonl.gz",
}
EXPECTED_SHA256 = {
    "parent_7b": "7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2",
    "donor_shared166": "fc403d05e29b1b317985f7ec77d1a3fa490c0264af8d639c3bfea899fcf1a849",
    "panel_208": "bfd178472afd40c6b457e794dbde6d5d045440fd3b2c6cb40e658c9f7a26d795",
    "obligation_audit": "e8a30db9e26e77a81ac01720cb23eca58d234a9229a08aca23b62ea4ec0717f5",
    "donor_trace_seat0": "6eb2952e5c931b201fe72e457f8eac2c5ecbf21454f43fc18ad20881e7360e9d",
    "donor_trace_seat1": "1885ab9d8ab0435dc9f26fc334208950bc799cf16f5cb7107a0ce7f69063cd1f",
    "target_trace_seat0": "7505703872cc3ce80799e08f50e4c3a9649f20d32cc518cbe12329b8f8c3d2ac",
    "target_trace_seat1": "f7afeedbfc2dcc11818ab8553ca2ef65518202363c6954f9f24eacb77a6f27ea",
    "donor_trace_seat0": "6eb2952e5c931b201fe72e457f8eac2c5ecbf21454f43fc18ad20881e7360e9d",
    "donor_trace_seat1": "1885ab9d8ab0435dc9f26fc334208950bc799cf16f5cb7107a0ce7f69063cd1f",
}


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trace_path_from_row(row: dict) -> pathlib.Path:
    raw = pathlib.Path(row["trace_path"])
    if raw.exists():
        return raw
    text = str(row["trace_path"]).replace("/", "\\")
    marker = "diagnostics\\"
    if marker not in text:
        raise FileNotFoundError(row["trace_path"])
    return ROOT / "diagnostics" / text.split(marker, 1)[1]


def trace_records(path: pathlib.Path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            yield json.loads(line)


def first_observation_at(path: pathlib.Path, wanted_step: int) -> dict:
    for record in trace_records(path):
        if int(record["step"]) == wanted_step:
            return record["observation"]
    raise AssertionError(f"step {wanted_step} missing from {path}")


def donor_routes(path: pathlib.Path) -> dict:
    """Decode only the donor's literal data blob; do not execute candidate code."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    decode_call = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "b85decode"
    )
    packed = ast.literal_eval(decode_call.args[0])
    data = json.loads(zlib.decompress(base64.b85decode(packed)))
    constants = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in {"_DONOR_DEFAULT", "_DONOR_MAP"}:
                constants[target.id] = ast.literal_eval(node.value)
    return {"routes": data, "constants": constants}


def main() -> None:
    hashes = {name: sha256(path) for name, path in FILES.items()}
    for name, expected in EXPECTED_SHA256.items():
        if name in hashes and hashes[name] != expected:
            raise AssertionError(f"frozen {name} hash changed: {hashes.get(name)}")

    # Parsing source files is static inspection only.  No candidate module is
    # imported and no callable from either submission is run.
    ast.parse(FILES["parent_7b"].read_text(encoding="utf-8"))
    ast.parse(FILES["donor_shared166"].read_text(encoding="utf-8"))
    ast.parse(FILES["adapter_layer"].read_text(encoding="utf-8"))

    panel_bytes = FILES["panel_208"].read_bytes()
    panel = json.loads(panel_bytes)
    if panel.get("source_a44_sha256") != "a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f":
        raise AssertionError("historical feature-panel producer changed")
    rows = panel["rows"]
    if len(rows) != 208:
        raise AssertionError(f"expected 208 rows, got {len(rows)}")

    census = []
    checked_trace_hashes = {}
    for row in rows:
        path = trace_path_from_row(row)
        trace_hash = sha256(path)
        if trace_hash != row["trace_sha256"]:
            raise AssertionError(f"row trace hash mismatch: {path}")
        key = f"{row['fixture_id']}|seat{row['seat']}"
        checked_trace_hashes[key] = trace_hash
        obs = first_observation_at(path, 1)
        player = int(obs["player"])
        if player != int(row["seat"]):
            raise AssertionError(f"player/seat mismatch for {key}")
        rival = obs["farms"][1 - player]
        own = obs["farms"][player]
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
            "trace_sha256": trace_hash,
        })

    triggered = [
        row for row in census
        if row["rival_hand_count"] == 3 and row["rival_farmer"] == [4, 3]
    ]
    near_three_stationary = [
        row for row in census
        if row["rival_hand_count"] == 3 and row["rival_farmer"] == [4, 4]
    ]
    near_four_other_move = [
        row for row in census
        if row["rival_hand_count"] == 4 and row["rival_farmer"] == [3, 4]
    ]
    expected_target = {"live-114270587|seat0", "live-114270587|seat1"}
    actual_target = {f"{r['fixture_id']}|seat{r['seat']}" for r in triggered}
    if actual_target != expected_target:
        raise AssertionError(f"trigger changed: {sorted(actual_target)}")
    if len(near_three_stationary) != 6 or len(near_four_other_move) != 4:
        raise AssertionError("near-miss census changed")

    histogram = Counter(
        (row["rival_hand_count"], tuple(row["rival_farmer"])) for row in census
    )
    trigger_trace_hashes = {
        f"target_trace_seat{row['seat']}": row["trace_sha256"] for row in triggered
    }
    for name, expected in EXPECTED_SHA256.items():
        if name.startswith("target_trace_") and trigger_trace_hashes.get(name) != expected:
            raise AssertionError(f"frozen {name} changed")

    # Confirm the donor's raw route data and segment boundary without running
    # _donor_schedule, _donor_action, transformations, or any game transition.
    decoded = donor_routes(FILES["donor_shared166"])
    routes = decoded["routes"]
    if set(routes) != {"route0", "route1"}:
        raise AssertionError(f"unexpected donor route keys: {sorted(routes)}")
    route0, route1 = routes["route0"], routes["route1"]
    if len(route0) != 719 or len(route1) != 719:
        raise AssertionError("donor route length changed")
    common_prefix = next((i for i, pair in enumerate(zip(route0, route1)) if pair[0] != pair[1]), 719)
    constants = decoded["constants"]
    if common_prefix != 166 or constants.get("_DONOR_DEFAULT") != "route0":
        raise AssertionError("donor segment/default route changed")
    if constants.get("_DONOR_MAP") != {
        "PET_CAFE|FARMERS_MARKET": "route0",
        "ICE_CREAM_SHOP|PET_CAFE": "route1",
    }:
        raise AssertionError("donor observed-shop map changed")
    expected_step2 = {
        "farmer": ["SOUTH"],
        "hands": [["PICKUP", "COW", 1], ["PASS"], ["NORTH"], ["NORTH"], ["PICKUP", "COW", 1]],
        "market": [],
    }
    if route0[2] != expected_step2 or route1[2] != expected_step2:
        raise AssertionError("donor action 2 changed")
    actual_order_donor_slots = [1, 2, 3, 0, 4]
    mapped_step2_hands = [route0[2]["hands"][i] for i in actual_order_donor_slots]
    if mapped_step2_hands != [["PASS"], ["NORTH"], ["NORTH"], ["PICKUP", "COW", 1], ["PICKUP", "COW", 1]]:
        raise AssertionError("static donor hand remap changed")

    target_source = next(
        trace_path_from_row(row) for row in rows
        if row["fixture_id"] == "live-114270587" and row["seat"] == 0
    )
    target_donor = ROOT / "diagnostics/donor_opening_agents_20260928/full_shared166_live-114270587_seat0.jsonl.gz"
    source_obs1 = first_observation_at(target_source, 1)
    donor_obs2 = first_observation_at(target_donor, 2)
    source_own = source_obs1["farms"][source_obs1["player"]]
    source_private = source_obs1["private"]
    donor_own = donor_obs2["farms"][donor_obs2["player"]]
    donor_private = donor_obs2["private"]
    if source_own["hands"] != [[5, 4], [4, 5], [5, 5], [4, 4]]:
        raise AssertionError("recorded target parent state changed")
    if source_private["shed"].get("COW") != 2 or source_private["shed"].get("SHEEP") != 2 or source_private["shed"].get("WHEAT") != 6:
        raise AssertionError("recorded target parent obligations changed")
    if donor_own["hands"] != [[4, 4], [5, 4], [4, 5], [5, 5], [4, 4]]:
        raise AssertionError("recorded donor worker order changed")

    # The pair is public at 144.  An unmapped pair chooses the default route.
    source_obs144 = first_observation_at(target_source, 144)
    shops144 = source_obs144.get("town", {}).get("unlocked_shops", [])[:2]
    shop_key = "|".join(shops144)
    if shop_key != "PET_CAFE|PET_CAFE" or shop_key in constants["_DONOR_MAP"]:
        raise AssertionError(f"saved Roman shop pair changed: {shop_key}")

    payload = {
        "passed": True,
        "static_only": True,
        "agent_calls": 0,
        "engine_transitions": 0,
        "games_run": 0,
        "source_hashes": hashes,
        "panel_trace_producer_sha256": panel["source_a44_sha256"],
        "frozen_target_and_donor_trace_hashes": {
            name: EXPECTED_SHA256[name]
            for name in EXPECTED_SHA256
            if name.startswith("target_trace_") or name.startswith("donor_trace_")
        },
        "panel_rows": len(rows),
        "unique_traces": len(checked_trace_hashes),
        "trigger": {
            "predicate": "step==1 and rival hands==3 and rival farmer==[4,3]",
            "rows": triggered,
            "count": len(triggered),
        },
        "near_misses": {
            "three_hands_farmer_4_4": near_three_stationary,
            "three_hands_farmer_4_4_count": len(near_three_stationary),
            "four_hands_farmer_3_4": near_four_other_move,
            "four_hands_farmer_3_4_count": len(near_four_other_move),
        },
        "full_rival_opening_histogram": [
            {"hand_count": count, "farmer": list(position), "rows": n}
            for (count, position), n in sorted(histogram.items())
        ],
        "donor_static_route_audit": {
            "route_keys": sorted(routes),
            "route_length": len(route0),
            "common_action_indices": [0, common_prefix - 1],
            "first_divergence_index": common_prefix,
            "default_route": constants["_DONOR_DEFAULT"],
            "target_step144_shop_key": shop_key,
            "target_uses_default_route": True,
            "raw_action_step2": route0[2],
            "mapped_action_step2_hands": mapped_step2_hands,
            "donor_to_actual_hand_slots_1_based": [4, 1, 2, 3, 5],
            "actual_order_donor_slots_1_based": [2, 3, 4, 1, 5],
        },
        "merge_state": {
            "status": "PENDING_SHARED_SIMULATOR_OCCUPIED",
            "source_observation_step1": {
                "farmer": source_own["farmer"],
                "hands": source_own["hands"],
                "cash": source_own["money"],
                "hires_today": source_own["hires_today"],
                "shed": source_private["shed"],
            },
            "custom_step1_action": {
                "farmer": ["NORTH"],
                "hands": [["PASS"]] * len(source_own["hands"]),
                "market": [["HIRE"]],
            },
            "static_hire_cost": 5,
            "static_expected_step2_cash": float(source_own["money"]) - 5.0,
            "static_expected_worker_positions_after_step1": [
                [5, 4], [4, 5], [5, 5], [4, 4], [4, 4]
            ],
            "recorded_donor_step2_cash": donor_own["money"],
            "recorded_donor_step2_wheat": donor_private["shed"].get("WHEAT", 0),
            "recorded_source_step1_wheat": source_private["shed"].get("WHEAT", 0),
            "not_verified_by_transition": True,
        },
        "decision": "STAGE_ONLY_DO_NOT_PROMOTE",
    }
    out = HERE / "preflight.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "passed": payload["passed"],
        "static_only": payload["static_only"],
        "rows": payload["panel_rows"],
        "trigger_rows": payload["trigger"]["count"],
        "near_misses": [payload["near_misses"]["three_hands_farmer_4_4_count"], payload["near_misses"]["four_hands_farmer_3_4_count"]],
        "donor_common_prefix": common_prefix,
        "merge_state": payload["merge_state"]["status"],
        "preflight": str(out),
    }, indent=2))


if __name__ == "__main__":
    main()
