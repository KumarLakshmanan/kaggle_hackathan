"""Package the frozen observable selector and both exact opening arms."""
from pathlib import Path
import base64
import hashlib
import json
import zlib

HERE = Path(__file__).resolve().parent


def main():
    selection = json.loads((HERE / "selection.json").read_text(encoding="utf-8"))
    selected = selection["best_preserving_incumbent_wins"]
    assert selected is not None and selected["sweeps"] > 17
    records = json.loads((HERE / "candidates.json").read_text())
    sources = {}
    for record in records:
        blob = Path(record["path"]).read_bytes()
        assert hashlib.sha256(blob).hexdigest() == record["sha256"]
        sources[record["arm"]] = blob.decode("utf-8")
    packed = base64.b85encode(zlib.compress(json.dumps(sources).encode(), 9)).decode()
    source = '''"""Experimental observable opening selector; local qualification only."""
import base64
import json
import types
import zlib

_OPENING_SOURCES = json.loads(zlib.decompress(base64.b85decode(__PAYLOAD_VALUE__)))
_OPENING_MODULES = {}
for _opening_name, _opening_source in _OPENING_SOURCES.items():
    _opening_module = types.ModuleType("opening_arm_" + _opening_name)
    _opening_module.__file__ = "<bundled opening " + _opening_name + ">"
    exec(compile(_opening_source, _opening_module.__file__, "exec"), _opening_module.__dict__)
    _OPENING_MODULES[_opening_name] = _opening_module

_OPENING_RULE = __RULE_VALUE__
_OPENING_SELECTED = None
_OPENING_STATS = {"selected_arm": "", "rival_hands": 0, "rival_cash": 0.0,
                  "rival_wheat_net_buy": 0, "selector_errors": 0}

def _opening_choose(rule, features):
    if "arm" in rule:
        return rule["arm"]
    condition = rule["condition"]
    branch = "yes" if features[condition["feature"]] <= condition["threshold"] else "no"
    return _opening_choose(rule[branch], features)

def agent(observation, configuration=None):
    global _OPENING_SELECTED
    step = int(observation["step"])
    if step == 0:
        _OPENING_SELECTED = None
        _OPENING_STATS.update(selected_arm="", rival_hands=0, rival_cash=0.0,
                              rival_wheat_net_buy=0, selector_errors=0)
        initial = {name: module.agent(observation, configuration)
                   for name, module in _OPENING_MODULES.items()}
        if initial["4ee"] != initial["v43"]:
            raise RuntimeError("Opening arms no longer share their first action")
        return initial["4ee"]
    if _OPENING_SELECTED is None:
        seat = int(observation["player"])
        rival = observation["farms"][1-seat]
        features = {"rival_hands": len(rival["hands"]), "rival_cash": float(rival["money"]),
                    "rival_wheat_net_buy": 10000 - int(observation["market"]["inventory"]["WHEAT"]) - 6}
        _OPENING_SELECTED = _opening_choose(_OPENING_RULE, features)
        _OPENING_STATS.update(features)
        _OPENING_STATS["selected_arm"] = _OPENING_SELECTED
    return _OPENING_MODULES[_OPENING_SELECTED].agent(observation, configuration)

agent.telemetry = _OPENING_STATS

def kaggle_observable_portfolio_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''.replace("__RULE_VALUE__", repr(selected["rule"])).replace("__PAYLOAD_VALUE__", repr(packed))
    output = HERE / "candidate_selector.py"
    compile(source, str(output), "exec")
    output.write_text(source, encoding="utf-8")
    manifest = {"candidate": str(output), "candidate_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "selection_sha256": hashlib.sha256((HERE / "selection.json").read_bytes()).hexdigest(),
                "rule": selected["rule"], "arm_sources": records,
                "development_sweeps": selected["sweeps"], "development_lost_incumbent_win_seats": 0}
    (HERE / "selector_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
