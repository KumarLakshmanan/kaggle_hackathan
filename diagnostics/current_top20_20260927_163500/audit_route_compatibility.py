"""Passive compatibility screen of the frozen incumbent's embedded routes."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "candidate_frozen.py"


def physical(action):
    return action["farmer"], action["hands"]


if __name__ == "__main__":
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest().startswith("4eeac9c3")
    spec = importlib.util.spec_from_file_location("frozen_routes", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = json.loads((HERE / "fresh_loss_structure.json").read_text(encoding="utf8"))
    result = {}
    for team, row in data.items():
        shops = row["players"]["ours"]["states"]["455"]["shops"]
        route_id = str(module._DATA["route_map"]["|".join(shops[:2])])
        incumbent = module._DATA["routes"][route_id]
        matches = [rid for rid, route in module._DATA["routes"].items()
                   if all(physical(route[i]) == physical(incumbent[i]) for i in range(144, 432))]
        suffix_hashes = {rid: hashlib.sha256(json.dumps(module._DATA["routes"][rid][432:],
                                                   sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                         for rid in matches}
        result[team] = {"first_two_shops": shops[:2], "incumbent_route_id": route_id,
                        "physical_day6_to_day17_compatible_route_ids": matches,
                        "distinct_day18_to_end_suffixes": len(set(suffix_hashes.values())),
                        "suffix_sha256_by_route": suffix_hashes}
    (HERE / "route_compatibility.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print(json.dumps(result, indent=2))
