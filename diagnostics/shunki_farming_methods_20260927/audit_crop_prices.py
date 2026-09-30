"""Observe first carrot-investment state without changing the base policy."""
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_agent, make


def audit(row):
    own, _ = _load_agent(str(ROOT / "exp_shunki_land_retry_20260927.py"), "farm_price_own")
    other, _ = _load_agent("rawroute:" + row["path"], "farm_price_other")
    captures = []

    def agent(obs, cfg):
        action = own(obs, cfg)
        relevant = any(len(o) > 1 and o[:2] == ["BUY_SEED", "CARROT"] for o in action.get("market", []))
        if relevant and len(captures) < 4:
            captures.append({"step": obs["step"], "prices": dict(obs["market"]["prices"]),
                             "inventory": dict(obs["market"]["inventory"]),
                             "shops": list(obs["town"]["unlocked_shops"]),
                             "shed": dict(obs["private"]["shed"]),
                             "money": obs["farms"][0]["money"], "market": action.get("market", [])})
        return action

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": row["seed"]}, debug=False)
    env.run([agent, other])
    result = {"team": row["team"], "seed": row["seed"], "captures": captures,
              "rewards": [s.reward for s in env.state], "statuses": [s.status for s in env.state]}
    for timed in (own, other):
        if timed.module_name:
            sys.modules.pop(timed.module_name, None)
    return result


if __name__ == "__main__":
    rows = json.loads((ROOT / "diagnostics/shunki_sale_advance_20260927/development_routes.json").read_text(encoding="utf8"))
    results = []
    with ProcessPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(audit, row) for row in rows]):
            r = future.result()
            results.append(r)
            print(r["team"], [(c["step"], c["prices"]["WHEAT"], c["prices"]["CARROT"]) for c in r["captures"]], flush=True)
    (HERE / "crop_price_audit.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf8")
