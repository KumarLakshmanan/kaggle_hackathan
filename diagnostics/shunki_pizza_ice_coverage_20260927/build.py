import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import base64
import zlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
source = ROOT/"exp_shunki_market_queue_20260927.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == "a2d2869c1d53bcfcedc8514d004f73bbab27ec6ef22b34d23241e718e4c1bf47"
row = next(r for r in json.loads((ROOT/"diagnostics/shunki_source_refresh_20260927_0213/manifest.json").read_text(encoding="utf8"))["rows"] if r["episode_id"] == 113940892)
with gzip.open(row["route_path"], "rt", encoding="utf8") as handle:
    route = json.load(handle)["actions"]
spec = importlib.util.spec_from_file_location("parent_for_coverage", source)
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
key = "PIZZA_SHOP|ICE_CREAM_SHOP"
assert not any(k.startswith(key) for k in parent._DATA["route_map"])
prefix = parent._DATA["opening"][:72]+parent._DATA["routes"][str(parent._DATA["route_map"]["PIZZA_SHOP"])][72:144]
assert all(a["farmer"] == b["farmer"] and a["hands"] == b["hands"] for a,b in zip(prefix,route[:144]))
diff = [i for i,(a,b) in enumerate(zip(prefix,route[:144])) if a["market"] != b["market"]]
assert diff == [79], diff
assert route[79]["market"] == [["BUY_PRODUCT","WHEAT",15],["SELL","WHEAT",15]]
packed = base64.b85encode(zlib.compress(json.dumps(route,separators=(",",":")).encode())).decode()
suffix = '\n\n# Newly observed missing two-shop branch; parent opening retained.\n_DATA["routes"]["113940892"] = json.loads(zlib.decompress(base64.b85decode('+repr(packed)+')))\n_DATA["route_map"]["PIZZA_SHOP|ICE_CREAM_SHOP"] = 113940892\n\ndef kaggle_pizza_ice_coverage_entrypoint(observation, configuration=None):\n    return agent(observation, configuration)\n'
raw = source.read_bytes()+suffix.encode()
target = ROOT/"exp_shunki_pizza_ice_coverage_20260927.py"
compile(raw,str(target),"exec")
target.write_bytes(raw)
digest = hashlib.sha256(raw).hexdigest()
backup = ROOT/("main_candidate_pizza_ice_coverage_20260927_"+digest[:8]+".py")
backup.write_bytes(raw)
manifest = {"candidate_sha256":digest,"parent_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "plan_sha256":hashlib.sha256((HERE/"PLAN.md").read_bytes()).hexdigest(),"backup":str(backup),
            "new_route":row,"opening_retained_through":143,"only_prefix_difference":diff}
(HERE/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf8")
panel = json.loads((ROOT/"diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))
(HERE/"development_routes.json").write_text(json.dumps([r for r in panel if r["team"] in ("ymg_aq","Breaking1800","Arda Ceylan")],indent=2),encoding="utf8")
print(json.dumps({"candidate_sha256":digest,"backup":str(backup)}))
