"""Static action-prefix census; does not read reserved episode_2/episode_3."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import zlib

HERE = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load_actions(row: dict) -> list:
    payload = json.loads(gzip.decompress(Path(row["path"]).read_bytes()))
    return payload["actions"]


def first_shop(row: dict) -> tuple[str, ...]:
    timeline = json.loads(gzip.decompress(Path(row["public_state_path"]).read_bytes()))
    state = timeline[72]["states"][int(row["source_seat"])]
    return tuple(sorted(state.get("town", {}).get("unlocked_shops", [])))


def extract_cb76_data() -> dict:
    """Decode only the literal _DATA payload; do not import/run the agent."""
    source = HERE.parents[0] / "upload_minimal_repair_20260929_cb76fbc4" / "main.py"
    source_raw = source.read_bytes()
    tree = ast.parse(source_raw.decode("utf-8"))
    encoded = next(node for node in ast.walk(tree)
                   if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Attribute)
                   and node.func.attr == "b85decode")
    blob = encoded.args[0].value
    data = json.loads(zlib.decompress(base64.b85decode(blob)).decode("utf-8"))
    return data, source, hashlib.sha256(source_raw).hexdigest()


def physical_projection(action: dict, *, investments: bool) -> dict:
    result = {"farmer": action.get("farmer", []), "hands": action.get("hands", [])}
    if investments:
        retained = {"HIRE", "BUY_LAND", "BUY_SEED", "BUY_SEEDS", "BUY_ANIMAL"}
        result["investment_orders"] = [order for order in action.get("market", [])
                                       if order and order[0] in retained]
    return result


def actual_route_prefix(data: dict, shops: tuple[str, ...]) -> tuple[list, int | None]:
    route_map = dict(data["route_map"])
    # Reproduce the two static route-map edits present in the uploaded cb76 file.
    for key, value in list(route_map.items()):
        if value == 113445495:
            route_map[key] = 113383763
    pair_routes = {
        "BRUNCH_SPOT|BRUNCH_SPOT": 113373693,
        "BRUNCH_SPOT|SMOOTHIE_SHOP": 113557748,
        "ICE_CREAM_SHOP|PET_CAFE": 113336042,
    }
    for pair, route_id in pair_routes.items():
        for key in list(route_map):
            if key == pair or key.startswith(pair + "|"):
                route_map[key] = route_id
        route_map[pair] = route_id

    # For action indices 72..143, the deployed selector has observed only its
    # first shop and selects the one-shop route-map entry.
    route_id = route_map.get(shops[0]) if shops else None
    if route_id is None:
        route_id = next(iter(data["routes"]))
    return data["routes"][str(route_id)], int(route_id)


def main() -> None:
    latest_path = HERE / "routes" / "development_latest" / "summary.json"
    own_path = HERE / "routes" / "current_submission_56680167" / "summary.json"
    latest_rows = json.loads(latest_path.read_text(encoding="utf-8"))
    own_rows = json.loads(own_path.read_text(encoding="utf-8"))
    if len(latest_rows) != 100 or len(own_rows) != 27:
        raise RuntimeError(f"unexpected route counts: latest={len(latest_rows)} own={len(own_rows)}")

    own_reference = []
    reference_72 = set()
    reference_72_and_shop = set()
    reference_144_and_shop = set()
    for row in own_rows:
        actions = load_actions(row)
        shop = first_shop(row)
        h72, h144 = digest(actions[:72]), digest(actions[:144])
        own_reference.append({"episode_id": row["episode_id"], "team": row["opponent_team"],
                              "source_seat": row["source_seat"], "shop_at_step72": list(shop),
                              "actions72_sha256": h72, "actions144_sha256": h144})
        reference_72.add(h72)
        reference_72_and_shop.add((h72, shop))
        reference_144_and_shop.add((h144, shop))

    census = []
    counts72 = defaultdict(list)
    for row in latest_rows:
        actions = load_actions(row)
        shop = first_shop(row)
        h72, h144 = digest(actions[:72]), digest(actions[:144])
        counts72[h72].append(int(row["rank"]))
        census.append({
            "rank": int(row["rank"]), "team": row["team"], "team_id": row.get("team_id"),
            "episode_id": row["episode_id"], "submission_id": row.get("submission_id"),
            "seed": row["seed"], "source_seat": row["source_seat"],
            "shop_at_step72": list(shop),
            "actions72_sha256": h72, "actions144_sha256": h144,
            "matches_any_uploaded_56680167_actual_72_prefix": h72 in reference_72,
            "matches_uploaded_56680167_72_prefix_and_same_first_shop": (h72, shop) in reference_72_and_shop,
            "matches_uploaded_56680167_144_prefix_and_same_first_shop": (h144, shop) in reference_144_and_shop,
        })

    largest_size = max(len(ranks) for ranks in counts72.values())
    largest_clusters = []
    for h, ranks in sorted(counts72.items()):
        if len(ranks) == largest_size:
            largest_clusters.append({"actions72_sha256": h, "count": len(ranks),
                                     "ranks": sorted(ranks), "top20_count": sum(r <= 20 for r in ranks)})

    own_clusters = defaultdict(list)
    for ref in own_reference:
        own_clusters[ref["actions72_sha256"]].append(ref)
    common_openings = [
        {"actions72_sha256": h, "count_in_27_uploaded_public_episodes": len(refs),
         "episodes": [r["episode_id"] for r in refs],
         "first_shops_at_step72": sorted({tuple(r["shop_at_step72"]) for r in refs})}
        for h, refs in sorted(own_clusters.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ]

    cb76_data, cb76_source, cb76_source_sha = extract_cb76_data()
    opening = cb76_data["opening"]
    if len(opening) != 72:
        raise RuntimeError(f"cb76 embedded opening has {len(opening)} actions, expected 72")
    own_schedule_calibration = {"worker_only": {"prefix_72": 0, "prefix_144": 0},
                                "worker_plus_investments": {"prefix_72": 0, "prefix_144": 0}}
    for row in own_rows:
        actual = load_actions(row)
        shops_ordered = json.loads(gzip.decompress(Path(row["public_state_path"]).read_bytes()))[72]["states"][int(row["source_seat"])].get("town", {}).get("unlocked_shops", [])
        selected_route, route_id = actual_route_prefix(cb76_data, tuple(shops_ordered))
        expected_144 = opening[:72] + selected_route[72:144]
        for label, keep_investments in (("worker_only", False), ("worker_plus_investments", True)):
            project = lambda seq: [physical_projection(a, investments=keep_investments) for a in seq]
            own_schedule_calibration[label]["prefix_72"] += int(project(actual[:72]) == project(opening[:72]))
            own_schedule_calibration[label]["prefix_144"] += int(project(actual[:144]) == project(expected_144))
    physical_results = {"worker_only": {"prefix_72": [], "prefix_144": []},
                        "worker_plus_investments": {"prefix_72": [], "prefix_144": []}}
    physical_rows = []
    for row in latest_rows:
        actual = load_actions(row)
        shops_ordered = json.loads(gzip.decompress(Path(row["public_state_path"]).read_bytes()))[72]["states"][int(row["source_seat"])].get("town", {}).get("unlocked_shops", [])
        shops_tuple = tuple(shops_ordered)
        selected_route, route_id = actual_route_prefix(cb76_data, shops_tuple)
        if len(selected_route) < 144:
            raise RuntimeError(f"cb76 route {route_id} is too short")
        expected_72 = opening[:72]
        expected_144 = expected_72 + selected_route[72:144]
        matches = {}
        for label, keep_investments in (("worker_only", False), ("worker_plus_investments", True)):
            expected72_projected = [physical_projection(a, investments=keep_investments) for a in expected_72]
            expected144_projected = [physical_projection(a, investments=keep_investments) for a in expected_144]
            actual72_projected = [physical_projection(a, investments=keep_investments) for a in actual[:72]]
            actual144_projected = [physical_projection(a, investments=keep_investments) for a in actual[:144]]
            match72 = actual72_projected == expected72_projected
            match144 = actual144_projected == expected144_projected
            matches[label] = {"prefix_72": match72, "prefix_144": match144}
            physical_results[label]["prefix_72"].append(match72)
            physical_results[label]["prefix_144"].append(match144)
        physical_rows.append({
            "rank": int(row["rank"]), "team": row["team"], "episode_id": row["episode_id"],
            "source_seat": row["source_seat"], "first_shop_at_step72": shops_ordered[0] if shops_ordered else None,
            "cb76_first_shop_route_id": route_id,
            "worker_only_matches": matches["worker_only"],
            "worker_plus_investments_matches": matches["worker_plus_investments"],
        })

    result = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Static hash and raw-prefix comparison only. Reads development_latest and the uploaded submission's 27 own public replays; does not read episode_2/episode_3, inspect outcomes, or run games.",
        "source_routes": {
            "development_latest_summary": str(latest_path.resolve()),
            "development_latest_summary_sha256": hashlib.sha256(latest_path.read_bytes()).hexdigest(),
            "uploaded_submission_summary": str(own_path.resolve()),
            "uploaded_submission_summary_sha256": hashlib.sha256(own_path.read_bytes()).hexdigest(),
            "uploaded_submission_id": 56680167,
            "development_count": len(latest_rows), "uploaded_public_replay_count": len(own_rows),
        },
        "comparison_method": "actions come from runner route payloads. Hashes use SHA-256 over sorted-key compact UTF-8 JSON, ensure_ascii=False. First-shop class is the sorted unlocked_shops list at public-state frame 72 for the same tape's source_seat.",
        "cb76_embedded_data": {
            "source_path": str(cb76_source.resolve()),
            "source_sha256": cb76_source_sha,
            "opening_length": len(opening),
            "route_count": len(cb76_data["routes"]),
            "normalization": "worker-only keeps each action's farmer and hands verbatim. Worker-plus-investments also retains only HIRE, BUY_LAND, BUY_SEED(S), and BUY_ANIMAL market orders in original relative order; SELL/BUY_PRODUCT and their interleaving with retained orders are ignored.",
            "144-prefix_reference": "opening[0:72] plus the selected deployed first-shop raw route actions[72:144], using the uploaded route_map edits and the source selector's first-shop lookup at steps 72-143.",
        },
        "physical_schedule_match_summary": {
            label: {prefix: {"matches": sum(values), "of": len(values),
                              "top20_matches": sum(ok for ok, row in zip(values, latest_rows) if int(row["rank"]) <= 20)}
                   for prefix, values in prefixes.items()}
            for label, prefixes in physical_results.items()
        },
        "uploaded_public_tape_calibration": {
            "actual_cb76_56680167_tapes_matching_embedded_projected_schedule": own_schedule_calibration,
            "of": len(own_rows),
        },
        "uploaded_actual_opening_templates": common_openings,
        "uploaded_actual_opening_template_count": len(common_openings),
        "development_prefix_summary": {
            "prefix_72_unique_hashes": len(counts72),
            "largest_identical_prefix_72_count": largest_size,
            "largest_identical_prefix_72_clusters": largest_clusters,
            "matches_any_of_27_uploaded_actual_actions_0_71": sum(x["matches_any_uploaded_56680167_actual_72_prefix"] for x in census),
            "matches_uploaded_actions_0_71_and_same_first_shop": sum(x["matches_uploaded_56680167_72_prefix_and_same_first_shop"] for x in census),
            "matches_uploaded_actions_0_143_and_same_first_shop": sum(x["matches_uploaded_56680167_144_prefix_and_same_first_shop"] for x in census),
            "top20_matches_any_uploaded_actual_actions_0_71": sum(x["rank"] <= 20 and x["matches_any_uploaded_56680167_actual_72_prefix"] for x in census),
            "top20_matches_uploaded_actions_0_143_and_same_first_shop": sum(x["rank"] <= 20 and x["matches_uploaded_56680167_144_prefix_and_same_first_shop"] for x in census),
            "top20_distinct_prefix_72_hashes": len({x["actions72_sha256"] for x in census if x["rank"] <= 20}),
        },
        "development_rows": census,
        "physical_schedule_rows": physical_rows,
    }
    out = HERE / "static_prefix_census.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out.resolve()),
                      "summary": result["development_prefix_summary"],
                      "physical_schedule_matches": result["physical_schedule_match_summary"],
                      "cb76_source_sha256": cb76_source_sha,
                      "uploaded_actual_opening_templates": common_openings}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
