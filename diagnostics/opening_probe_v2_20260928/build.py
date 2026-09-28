"""Build opening arms with incumbent market/cash parity through turn three."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCES = {
    "4ee": ("main.py", "4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed"),
    "v43": ("main_v43_current.py", "69f06a802b62aa08f28705dab5728eb924bb6a7c23ffe0164f65b104cc3dadf3"),
}
LAYER = '''

import copy as _probe_copy
_PROBE_PARENT = agent
_PROBE_ARM = ARM_VALUE
_PROBE_TELEMETRY = {"probe_arm": _PROBE_ARM, "probe_turns": 0}

def _probe_parent_observation(observation):
    step = int(observation["step"])
    if _PROBE_ARM != "4ee" or step not in (1, 2):
        return observation
    virtual = _probe_copy.deepcopy(observation)
    farm = virtual["farms"][int(virtual["player"])]
    private = virtual["private"]
    if step == 1:
        farm["money"] -= 2390
        private["shed"]["COW"] += 2
        private["shed"]["SHEEP"] += 3
        private["seeds"]["STRAWBERRY"] += 1
        private["seeds"]["WHEAT"] -= 1
    else:
        private["shed"]["COW"] -= 1
        private["inventories"][0]["COW"] = private["inventories"][0].get("COW", 0) + 1
        private["seeds"]["WHEAT"] += 1
        x, y = farm["farmer"]
        assert farm["tiles"][y][x].get("crop") == "WHEAT"
        farm["tiles"][y][x] = None
    return virtual

def agent(observation, configuration=None):
    step = int(observation["step"])
    result = _PROBE_PARENT(_probe_parent_observation(observation), configuration)
    if step == 0:
        _PROBE_TELEMETRY["probe_turns"] = 0
        result = {"farmer": ["PASS"], "hands": [], "market": [
            ["BUY_PRODUCT", "WHEAT", 28], ["SELL", "WHEAT", 24],
            ["BUY_PRODUCT", "WHEAT", 2], ["NOOP"], ["NOOP"],
            ["BUY_SEED", "WHEAT", 1], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"]]}
    elif step == 1:
        result = _probe_copy.deepcopy(result)
        if _PROBE_ARM == "4ee":
            result["farmer"] = ["PLANT", "WHEAT"]
            consumed = False
            for index, order in enumerate(result["market"]):
                if order[:2] == ["BUY_SEED", "WHEAT"] and not consumed:
                    assert order[2] == 1
                    result["market"][index] = ["NOOP"]
                    consumed = True
            assert consumed
            result["market"] += [["BUY_ANIMAL", "COW", 2], ["BUY_ANIMAL", "SHEEP", 3],
                                  ["BUY_SEED", "STRAWBERRY", 1]]
            assert len(result["market"]) <= 10
        else:
            result["farmer"] = ["PICKUP", "WHEAT", 4]
            result["market"] = [["BUY_SEED", "MELON", 7], ["BUY_SEED", "WHEAT", 4],
                                ["BUY_ANIMAL", "SHEEP", 4]]
    elif step == 2:
        result = _probe_copy.deepcopy(result)
        if _PROBE_ARM == "4ee":
            result["farmer"] = ["PICKUP", "COW", 1]
        else:
            result["farmer"] = ["PICKUP", "SHEEP", 4]
            result["market"] = [["BUY_PRODUCT", "WHEAT", 2]]
    if step <= 2:
        _PROBE_TELEMETRY["probe_turns"] += 1
    agent.telemetry.update(_PROBE_TELEMETRY)
    return result

agent.telemetry = _PROBE_TELEMETRY

def kaggle_observable_opening_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''


def main():
    records = []
    for name, (source_name, expected) in SOURCES.items():
        original = (ROOT / source_name).read_bytes()
        assert hashlib.sha256(original).hexdigest() == expected
        output = HERE / ("candidate_" + name + ".py")
        blob = original + LAYER.replace("ARM_VALUE", repr(name)).encode()
        compile(blob, str(output), "exec")
        output.write_bytes(blob)
        records.append({"arm": name, "source": source_name, "source_sha256": expected,
                        "path": str(output), "sha256": hashlib.sha256(blob).hexdigest()})
    (HERE / "candidates.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    previous = ROOT / "diagnostics/opening_probe_20260928"
    for filename in ("screen_arms.py", "select_rule.py", "build_selector.py"):
        target = HERE / filename
        if not target.exists():
            target.write_bytes((previous / filename).read_bytes())
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
