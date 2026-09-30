"""Enumerate opening-compatible alternatives without reading new outcomes."""
from collections import defaultdict
import base64
import gzip
import hashlib
import json
from pathlib import Path
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module


def canonical(action):
    orders, kept, index = action.get("market", []), [], 0
    while index < len(orders):
        if (index + 1 < len(orders) and len(orders[index]) >= 3
                and len(orders[index + 1]) >= 3
                and orders[index][0] == "BUY_PRODUCT"
                and orders[index + 1][0] == "SELL"
                and orders[index][1:] == orders[index + 1][1:]):
            index += 2
            continue
        kept.append(orders[index])
        index += 1
    return {"farmer": action.get("farmer"), "hands": action.get("hands"), "market": kept}


def source_for(module, shops):
    route = None
    for count in (1, 2):
        route = module._DATA["route_map"].get("|".join(shops[:count]), route)
    return int(route)


def main():
    source = ROOT / "main_uploaded_shunki_schedule_20260927_3cc0f69f.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == "3cc0f69fcb9f6a8bee17bf6789f0f321a17f0d47324c462def1e783d6921a603"
    module = _load_module(source, "route_search_prepare")
    folder = ROOT / "diagnostics/shunki_portfolio_20260927"
    manifest = json.loads((folder / "route_manifest.json").read_text(encoding="utf8"))
    tapes = {}
    for row in manifest["rows"]:
        with gzip.open(row["route_path"], "rt", encoding="utf8") as handle:
            tapes[row["episode_id"]] = json.load(handle)["actions"]
    signatures = {episode: [canonical(a) for a in tape[:144]] for episode, tape in tapes.items()}
    comparison = json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/comparison.json").read_text(encoding="utf8"))
    grouped = defaultdict(list)
    for row in comparison["rows"]:
        grouped[tuple(row["candidate_shops"][0][:2])].append(row)
    targets = []
    for shops, cases in sorted(grouped.items()):
        if all(row["candidate_sweep"] for row in cases):
            continue
        parent = source_for(module, shops)
        eligible = [eid for eid in tapes if eid != 113445495 and signatures[eid] == signatures[parent]]
        assert parent in eligible
        targets.append({"shops": list(shops), "parent": parent, "eligible": eligible,
                        "cases": [{"team": row["team"], "seed": row["seed"],
                                   "route_path": row["route_path"],
                                   "baseline_seat0_margin": row["candidate_seat_margins"][0],
                                   "baseline_sweep": row["candidate_sweep"]} for row in cases]})
    required = {eid for group in targets for eid in group["eligible"]}
    missing = {str(eid): tapes[eid] for eid in required if str(eid) not in module._DATA["routes"]}
    packed = base64.b85encode(zlib.compress(json.dumps(missing, separators=(",", ":")).encode(), 9)).decode()
    layer = f'''

_DATA["routes"].update(json.loads(zlib.decompress(base64.b85decode({packed!r})).decode("utf8")))
_PORT_PARENT = agent
_PORT_PAIR = []
_PORT_EPISODE = None
_PORT_STATS = {{"portfolio_turns": 0}}

def agent(observation, configuration=None):
    step = int(observation["step"])
    if step == 0:
        _PORT_STATS["portfolio_turns"] = 0
    shops = observation["town"]["unlocked_shops"]
    if _PORT_EPISODE is not None and step >= 144 and list(shops[:2]) == list(_PORT_PAIR):
        _PORT_STATS["portfolio_turns"] += 1
        return copy.deepcopy(_DATA["routes"][str(_PORT_EPISODE)][min(step, 718)])
    return _PORT_PARENT(observation, configuration)

agent.telemetry = _PORT_STATS

def kaggle_portfolio_search_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
    candidate = ROOT / "exp_shunki_route_search_20260927.py"
    raw = source.read_bytes() + layer.encode("utf8")
    compile(raw, str(candidate), "exec")
    candidate.write_bytes(raw)
    plan = {"candidate_sha256": hashlib.sha256(raw).hexdigest(), "candidate": str(candidate),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest(),
            "targets": targets, "added_routes": len(missing),
            "jobs": sum(len(t["eligible"]) * len(t["cases"]) for t in targets)}
    (HERE / "search_manifest.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf8")
    print("candidate", plan["candidate_sha256"], "added routes", len(missing), "jobs", plan["jobs"], flush=True)
    for row in targets:
        print(row["shops"], "alternatives", len(row["eligible"]), "cases", len(row["cases"]), flush=True)


if __name__ == "__main__":
    main()
