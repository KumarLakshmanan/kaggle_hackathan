"""Apply and audit one complete public schedule replacement."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "exp_shunki_later_lookup_20260927.py"
DEST = ROOT / "exp_shunki_ice_schedule_20260927.py"
OLD, NEW = 113445495, 113383763


def main():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "68aad0908c38884aba856373088f1a6ba4a0423df2ee00edbec4c796f8e45fac"
    folder = ROOT / "diagnostics/shunki_portfolio_20260927"
    mapping = json.loads((folder / "later_shop_analysis.json").read_text(encoding="utf8"))["route_map"]
    manifest = json.loads((folder / "route_manifest.json").read_text(encoding="utf8"))
    tapes = {}
    for row in manifest["rows"]:
        if row["episode_id"] in set(mapping.values()):
            with gzip.open(row["route_path"], "rt", encoding="utf8") as handle:
                tapes[row["episode_id"]] = json.load(handle)["actions"]
    assert tapes[OLD][:241] == tapes[NEW][:241]
    changed = [key for key, value in mapping.items() if value == OLD]
    assert len(changed) == 7
    new_map = {key: NEW if value == OLD else value for key, value in mapping.items()}
    unrelated = []
    affected = []
    for key, value in new_map.items():
        parts = key.split("|")
        if len(parts) < 2:
            continue
        parent_key = "|".join(parts[:-1])
        parent = new_map[parent_key]
        step = len(parts) * 72
        compatible = tapes[value][:step] == tapes[parent][:step]
        if key in changed or parent_key in changed:
            assert compatible, (key, parent, value, step)
            affected.append({"key": key, "parent": parent, "route": value, "step": step})
        elif not compatible:
            unrelated.append({"key": key, "parent": parent, "route": value, "step": step})
    addition = '''

# Complete ICE/BRUNCH schedule replacement. The routes share all actions
# through turn 240; every affected map transition was checked at build time.
for _ice_schedule_key, _ice_schedule_source in list(_DATA["route_map"].items()):
    if _ice_schedule_source == 113445495:
        _DATA["route_map"][_ice_schedule_key] = 113383763
del _ice_schedule_key, _ice_schedule_source

def kaggle_shunki_ice_schedule_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
    DEST.write_bytes(raw + addition.encode("utf8"))
    digest = hashlib.sha256(DEST.read_bytes()).hexdigest()
    payload = {"candidate_sha256": digest, "old_source": OLD, "new_source": NEW,
               "changed_keys": changed, "affected_transitions": affected,
               "unrelated_preexisting_mismatches": unrelated}
    (HERE / "build_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf8")
    panel = json.loads((ROOT / "diagnostics/shunki_later_lookup_20260927/top100_analysis.json").read_text(encoding="utf8"))
    selected = [r for r in panel["rows"] if r["shops_by_seat"]["0"]["candidate"] == ["ICE_CREAM_SHOP", "BRUNCH_SPOT"]]
    (HERE / "development_routes.json").write_text(json.dumps(selected, indent=2), encoding="utf8")
    # Small prefix-only data for outcome-blind shop scans, byte-equivalent
    # to the original selector through action 143 for every first shop.
    first = {key: tapes[value][:144] for key, value in mapping.items() if "|" not in key}
    assert all(tape[:72] == next(iter(first.values()))[:72] for tape in first.values())
    (HERE / "scan_prefixes.json").write_text(json.dumps(first, separators=(",", ":")), encoding="utf8")
    print("built", digest, "affected transitions", len(affected), "development routes", len(selected))
    print("pre-existing unrelated mismatches", len(unrelated))


if __name__ == "__main__":
    main()
