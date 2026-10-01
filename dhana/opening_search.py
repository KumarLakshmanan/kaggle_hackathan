"""Screen same-inventory opening order schedules against the fixed control."""
import copy
import json
from strength_lab import Struct, SimpleNamespace, engine, load


def search():
    defaults = {k: v.get("default") if isinstance(v, dict) else v
                for k, v in engine.specification["configuration"].items()}
    defaults["seed"] = 42
    env = SimpleNamespace(configuration=Struct(**defaults), info={}, done=False)
    initial = [Struct(observation=Struct(step=0), action={}, reward=0, status="ACTIVE") for _ in range(2)]
    engine.interpreter(initial, env)
    action = load("main.py")(copy.deepcopy(initial[0].observation), env.configuration)
    print("CONTROL", json.dumps(action), flush=True)
    baseline = copy.deepcopy(initial)
    for s in baseline:
        s.action = copy.deepcopy(action)
    engine.interpreter(baseline, env)
    target = baseline[0].observation.private["shed"]["WHEAT"]
    rows = []
    for qty in range(target, 101):
        trial = copy.deepcopy(initial)
        market = [["BUY_PRODUCT", "WHEAT", qty]]
        if qty > target:
            market.append(["SELL", "WHEAT", qty-target])
        market += action["market"][2:]
        trial[0].action = dict(action, market=market)
        trial[1].action = copy.deepcopy(action)
        engine.interpreter(trial, env)
        if trial[0].observation.private["shed"]["WHEAT"] != target:
            continue
        money = [s.observation.farms[i]["money"] for i, s in enumerate(trial)]
        rows.append({"quantity": qty, "margin": money[0]-money[1], "money": money, "market": market})
    for row in sorted(rows, key=lambda r: -r["margin"])[:15]:
        print(json.dumps(row), flush=True)


if __name__ == "__main__":
    search()
