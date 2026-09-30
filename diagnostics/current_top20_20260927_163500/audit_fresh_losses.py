"""Native sales, investment and worker execution for fresh DECEM/Majkel tapes."""

from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = {
    "DECEM": "decem_current_seat0_events.json.gz",
    "Majkel1337": "majkel_current_seat0_events.json.gz",
}
CUTS = {"before_day6": 144, "through_day18": 456, "terminal": 720}


def counts(farm):
    by_kind, by_crop, by_animal = Counter(), Counter(), Counter()
    for row in farm["tiles"]:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind"):
                by_kind[tile["kind"]] += 1
            if tile.get("crop"):
                by_crop[tile["crop"]] += 1
            if tile.get("animal"):
                by_animal[tile["animal"]] += 1
    return {"tile_kinds": dict(by_kind), "crops": dict(by_crop), "animals": dict(by_animal)}


def position(data, step, player):
    if step < 719:
        record = data["traces"][player][step]
        farm = record["observation"]["farms"][player]
        private = record["observation"]["private"]
        shops = record["observation"]["town"]["unlocked_shops"]
    else:
        record = data["traces"][player][-1]
        farm = record["observation"]["farms"][player]
        private = record["observation"]["private"]
        shops = record["observation"]["town"]["unlocked_shops"]
    return {"cash": farm["money"], "hands": len(farm["hands"]),
            "land": list(farm["unlocked_quadrants"]), "shops": shops,
            "shed": {k:v for k,v in private["shed"].items() if v},
            "seeds": {k:v for k,v in private["seeds"].items() if v},
            **counts(farm)}


def summarize(data, cutoff, player):
    market = [e for e in data["events"] if e["phase"] == "market_unit"
              and e["player"] == player and e["step"] < cutoff]
    successful = [e for e in market if e["success"]]
    sales = defaultdict(lambda: {"units": 0, "coins": 0})
    costs = defaultdict(lambda: {"units": 0, "coins": 0})
    for e in successful:
        target = sales if e["operation"] == "SELL" else costs
        target[e["item"]]["units"] += 1
        target[e["item"]]["coins"] += abs(int(e["cash_delta"]))
    atomic = Counter(e["operation"] for e in data["events"] if e["phase"] == "market_atomic"
                     and e["player"] == player and e["step"] < cutoff and e["success"])
    atomic_cost = Counter()
    for e in data["events"]:
        if e["phase"] == "market_atomic" and e["player"] == player and e["step"] < cutoff and e["success"]:
            atomic_cost[e["operation"]] += int(e["cash_before"] - e["cash_after"])
    workers = [e for e in data["events"] if e["phase"] == "unit_action"
               and e["player"] == player and e["actor"] >= 1 and e["step"] < cutoff]
    nonpass = [e for e in workers if e["action"] and e["action"][0] != "PASS"]
    worker_types = Counter(e["action"][0] for e in nonpass if e["changed"])
    failures = Counter(e["failure_reason"] for e in market if not e["success"])
    return {"sales": dict(sales), "sale_coins": sum(v["coins"] for v in sales.values()),
            "purchases": dict(costs), "purchase_coins": sum(v["coins"] for v in costs.values()),
            "atomic_successes": dict(atomic), "atomic_costs": dict(atomic_cost),
            "worker_actions": len(workers), "worker_nonpass": len(nonpass),
            "worker_changed_nonpass": sum(e["changed"] for e in nonpass),
            "worker_nochange_nonpass": sum(not e["changed"] for e in nonpass),
            "worker_changed_types": dict(worker_types),
            "market_failures": dict(failures)}


if __name__ == "__main__":
    out = {}
    for team, name in INPUTS.items():
        data = json.loads(gzip.decompress((HERE / name).read_bytes()))
        assert data["candidate_seat"] == 0
        assert data["candidate_status"] == data["opponent_status"] == "DONE"
        row = {"seed": data["seed"], "margin": data["margin"],
               "candidate_reward": data["candidate_reward"],
               "opponent_reward": data["opponent_reward"], "players": {}}
        for player, label in ((0, "ours"), (1, "rival")):
            row["players"][label] = {
                "states": {str(step): position(data, step, player) for step in (143, 287, 431, 455, 575, 718)},
                "before_day6": summarize(data, 144, player),
                "through_day18": summarize(data, 456, player),
                "terminal": summarize(data, 720, player),
            }
        out[team] = row
    (HERE / "fresh_loss_structure.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf8")
    for team, row in out.items():
        print(team, "final", row["candidate_reward"], row["opponent_reward"])
        for label in ("ours", "rival"):
            p = row["players"][label]
            print(label, "d18 last-hour cash/hands/land", *(p["states"]["455"][k] for k in ("cash", "hands", "land")))
            for phase in ("through_day18", "terminal"):
                s = p[phase]
                top = sorted(s["sales"].items(), key=lambda x: -x[1]["coins"])
                print(" ", phase, "sales", s["sale_coins"], top, "purchase", s["purchase_coins"], "atomic", s["atomic_successes"],
                      "workers", s["worker_changed_nonpass"], "/", s["worker_nonpass"])
