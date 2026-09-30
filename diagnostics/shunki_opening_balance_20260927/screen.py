"""Opening-only financial screen; no terminal rewards used for selection."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS, CROPS, MARKET_PARAMS


def liquid(obs, seat):
    private = obs[seat].observation.private
    value = obs[0].observation.farms[seat]["money"]
    value += sum(CROPS[k]["seed"]*n for k, n in private["seeds"].items())
    for stock in [private["shed"], *private["inventories"]]:
        for item, n in stock.items():
            value += n*(ANIMALS[item]["cost"] if item in ANIMALS else MARKET_PARAMS[item]["base"])
    return value


def physical(states, seat):
    obs = states[seat].observation
    farm = copy.deepcopy(obs.farms[seat])
    farm.pop("money")
    return {"farm": farm, "private": copy.deepcopy(obs.private)}


def run(q, opponent, seat, opening):
    env = make("kaggriculture", configuration={"seed": 2655999}, debug=False)
    env.reset(2)
    own = copy.deepcopy(opening)
    assert own[0]["market"][:3] == [["BUY_PRODUCT", "WHEAT", 28], ["SELL", "WHEAT", 24], ["BUY_PRODUCT", "WHEAT", 2]]
    own[0]["market"][0][2] = q
    own[0]["market"][1][2] = q-4
    states = []
    values = []
    for step in range(2):
        actions = [opponent[step], opponent[step]]
        actions[seat] = own[step]
        env.step(actions)
        states.append(physical(env.state, seat))
        values.append(liquid(env.state, seat)-liquid(env.state, 1-seat))
    return states, values


if __name__ == "__main__":
    source = ROOT/"main_uploaded_shunki_schedule_20260927_3cc0f69f.py"
    spec = importlib.util.spec_from_file_location("opening_source", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    opening = module._DATA["opening"][:2]
    routes = json.loads((ROOT/"diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))
    quantities = (4, 8, 12, 20, 28, 40, 55, 70, 80)
    rows = []
    for route in routes:
        with gzip.open(route["path"], "rt", encoding="utf8") as h:
            opponent = json.load(h)["actions"][:2]
        for seat in (0, 1):
            baseline, values0 = run(28, opponent, seat, opening)
            for q in quantities:
                state, values = (baseline, values0) if q == 28 else run(q, opponent, seat, opening)
                rows.append({"team": route["team"], "seat": seat, "quantity": q,
                             "physical_equal": state == baseline,
                             "liquid_delta": values[-1]-values0[-1], "liquid_by_turn": values})
        print(route["team"], "screened", flush=True)
    summary = []
    for q in quantities:
        group = [r for r in rows if r["quantity"] == q]
        summary.append({"quantity": q, "games": len(group), "eligible": all(r["physical_equal"] for r in group),
                        "physical_mismatches": sum(not r["physical_equal"] for r in group),
                        "mean_liquid_delta": statistics.mean(r["liquid_delta"] for r in group),
                        "minimum_liquid_delta": min(r["liquid_delta"] for r in group)})
    eligible = [r for r in summary if r["eligible"]]
    selected = max(eligible, key=lambda r: (r["mean_liquid_delta"], -abs(r["quantity"]-28)))
    result = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "plan_sha256": hashlib.sha256((HERE/"PLAN.md").read_bytes()).hexdigest(),
              "rows": rows, "summary": summary, "selected": selected}
    (HERE/"screen.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps({"summary": summary, "selected": selected}), flush=True)
