"""Compile exact-prefix-compatible public-route shop history selector."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE_DIR = HERE.parent / "shunki_portfolio_20260927"
ANALYSIS = SOURCE_DIR / "later_shop_analysis.json"
MANIFEST = SOURCE_DIR / "route_manifest.json"
OUTPUT = ROOT / "exp_shunki_later_lookup_20260927.py"


def main() -> None:
    analysis_bytes = ANALYSIS.read_bytes()
    analysis = json.loads(analysis_bytes)
    manifest = json.loads(MANIFEST.read_text(encoding="utf8"))
    route_map = analysis["route_map"]
    selected = set(route_map.values())
    routes = {}
    for row in manifest["rows"]:
        episode = row["episode_id"]
        if episode not in selected:
            continue
        with gzip.open(row["route_path"], "rt", encoding="utf8") as handle:
            actions = json.load(handle)["actions"]
        assert len(actions) == 719
        routes[str(episode)] = actions
    assert len(routes) == 145 and len(route_map) == 1241
    first_episode = manifest["rows"][0]["episode_id"]
    opening = routes[str(first_episode)][:72]
    assert all(actions[:72] == opening for actions in routes.values())
    payload = json.dumps({"opening": opening, "route_map": route_map,
                          "routes": routes}, sort_keys=True,
                         separators=(",", ":"), ensure_ascii=False).encode("utf8")
    packed = base64.b85encode(zlib.compress(payload, 9)).decode("ascii")
    code = f'''"""Experimental observed-shop route selector. No Kaggle upload."""
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
    route = None
    for count in range(1, min(len(shops), 8) + 1):
        if step < 72 * count:
            break
        candidate = _DATA["route_map"].get("|".join(shops[:count]))
        if candidate is not None:
            route = candidate
    if route is None:
        route = next(iter(_DATA["routes"]))
    return copy.deepcopy(_DATA["routes"][str(route)][step])

def kaggle_shunki_later_lookup_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
    OUTPUT.write_text(code, encoding="utf8")
    result = {"analysis_sha256": hashlib.sha256(analysis_bytes).hexdigest(),
              "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
              "selected_routes": len(routes), "mapped_shop_prefixes": len(route_map),
              "candidate_bytes": OUTPUT.stat().st_size}
    (HERE / "build_manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print(result)


if __name__ == "__main__":
    main()
