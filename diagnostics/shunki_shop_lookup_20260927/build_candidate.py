"""Compile an outcome-blind first-shop/pair lookup from public routes."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "shunki_portfolio_20260927" / "route_manifest.json"
OUTPUT = ROOT / "exp_shunki_shop_lookup_20260927.py"


def main() -> None:
    manifest_bytes = SOURCE.read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest["total"] == 203 and manifest["distinct_shop_pairs"] == 61
    first = {}
    pair = {}
    by_id = {}
    for row in manifest["rows"]:
        episode = int(row["episode_id"])
        shop_a, shop_b = row["shops_day6"]
        first.setdefault(shop_a, episode)
        pair.setdefault(f"{shop_a}|{shop_b}", episode)
    selected = set(first.values()) | set(pair.values())
    for row in manifest["rows"]:
        episode = int(row["episode_id"])
        if episode not in selected:
            continue
        with gzip.open(row["route_path"], "rt", encoding="utf8") as handle:
            actions = json.load(handle)["actions"]
        assert len(actions) == 719
        by_id[str(episode)] = actions
    assert len(first) == 8 and len(pair) == 61
    opening = by_id[str(manifest["rows"][0]["episode_id"])][:72]
    assert all(actions[:72] == opening for actions in by_id.values())
    data = {"opening": opening, "first": first, "pair": pair,
            "routes": by_id}
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf8")
    packed = base64.b85encode(zlib.compress(payload, 9)).decode("ascii")
    code = f'''"""Experimental public-route shop lookup. No Kaggle upload."""
import base64
import copy
import json
import zlib

_DATA = json.loads(zlib.decompress(base64.b85decode({packed!r})).decode("utf8"))
_CALLS = 0

def _value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)

def agent(observation, configuration=None):
    del configuration
    global _CALLS
    raw_step = _value(observation, "step", None)
    try:
        step = int(raw_step) if raw_step is not None else _CALLS
    except (TypeError, ValueError):
        step = _CALLS
    _CALLS += 1
    step = max(0, min(step, 718))
    if step < 72:
        return copy.deepcopy(_DATA["opening"][step])
    town = _value(observation, "town", {{}})
    shops = _value(town, "unlocked_shops", []) or []
    if not shops:
        return copy.deepcopy(_DATA["opening"][min(step, 71)])
    source = _DATA["first"].get(shops[0])
    if step >= 144 and len(shops) >= 2:
        source = _DATA["pair"].get(shops[0] + "|" + shops[1], source)
    if source is None:
        source = next(iter(_DATA["routes"]))
    return copy.deepcopy(_DATA["routes"][str(source)][step])

def kaggle_shunki_shop_lookup_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
    OUTPUT.write_text(code, encoding="utf8")
    result = {"manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
              "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
              "selected_routes": len(by_id), "first_shop_episodes": first,
              "shop_pair_episodes": pair, "candidate_bytes": OUTPUT.stat().st_size}
    (HERE / "build_manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print(result["candidate_sha256"], "routes", len(by_id), "bytes", OUTPUT.stat().st_size)


if __name__ == "__main__":
    main()
