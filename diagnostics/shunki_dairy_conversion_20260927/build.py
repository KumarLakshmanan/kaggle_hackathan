import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module


if __name__ == "__main__":
    source = ROOT / "exp_shunki_shop_optimized_20260927.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == "94f0602f0a6a2d4c1af84f8caf93ee802335582485dd2f796a8c7e5a09846604"
    module = _load_module(source, "dairy_preflight")
    tape = module._DATA["routes"]["113537968"]
    assert module._OPT_TABLE["PIZZA_SHOP|ICE_CREAM_SHOP"] == 113537968
    for step, action in enumerate(tape):
        commands = [action["farmer"], *action["hands"]]
        assert all(cmd[:2] == ["PLACE", "EGG"] for cmd in commands if "EGG" in cmd), (step, commands)
        if step < 144:
            assert not any("GOOSE" in cmd or "BUILD_COOP" in cmd for cmd in commands + action["market"]), (step, action)
    layer = '''

_DAIRY_PARENT = agent
_DAIRY_STATS = {"animal_orders": 0, "animal_commands": 0, "structures": 0, "sale_orders": 0, "product_commands": 0}

def agent(observation, configuration=None):
    step = int(observation["step"])
    if step == 0:
        for key in _DAIRY_STATS:
            _DAIRY_STATS[key] = 0
    action = _DAIRY_PARENT(observation, configuration)
    if step < 144 or observation["town"]["unlocked_shops"][:2] != ["PIZZA_SHOP", "ICE_CREAM_SHOP"]:
        return action
    for command in [action.get("farmer", []), *action.get("hands", [])]:
        if command and command[0] == "BUILD_COOP":
            command[0] = "BUILD_PASTURE"
            _DAIRY_STATS["structures"] += 1
        elif len(command) > 1 and command[0] in ("PICKUP", "PLACE") and command[1] == "GOOSE":
            command[1] = "COW"
            _DAIRY_STATS["animal_commands"] += 1
        elif len(command) > 1 and command[:2] == ["PLACE", "EGG"]:
            command[1] = "MILK"
            _DAIRY_STATS["product_commands"] += 1
    for order in action.get("market", []):
        if len(order) > 1 and order[:2] == ["BUY_ANIMAL", "GOOSE"]:
            order[1] = "COW"
            _DAIRY_STATS["animal_orders"] += 1
        elif len(order) > 1 and order[:2] == ["SELL", "EGG"]:
            order[1] = "MILK"
            _DAIRY_STATS["sale_orders"] += 1
    return action

agent.telemetry = _DAIRY_STATS

def kaggle_coherent_dairy_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
    target = ROOT / "exp_shunki_dairy_conversion_20260927.py"
    raw = source.read_bytes() + layer.encode("utf8")
    compile(raw, str(target), "exec")
    target.write_bytes(raw)
    manifest = {"candidate": str(target), "candidate_sha256": hashlib.sha256(raw).hexdigest(),
                "parent": str(source), "parent_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest(),
                "preflight": "No goose/coop before 144; all EGG unit commands are three PLACE shed drops, converted coherently"}
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    print(manifest["candidate_sha256"])
