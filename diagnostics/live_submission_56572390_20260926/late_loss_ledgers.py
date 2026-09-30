"""Exact native cash attribution for late reversals in frozen public losses."""

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from trace_paired_game_events import run  # noqa: E402


SOURCE = ROOT / "main.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
CACHE = HERE / "late_loss_ledgers_cache"
OUTPUT = HERE / "late_loss_ledgers_29.json"


def play(job):
    live, route = job
    seat = int(live["our_seat"])
    data = run(str(SOURCE), f"rawroute:{route['path']}", int(live["seed"]), seat)
    assert data["candidate_status"] == data["opponent_status"] == "DONE"
    assert (data["candidate_reward"], data["opponent_reward"]) == (live["our_cash"], live["rival_cash"]), live["episode_id"]
    day19_turn = next(turn for turn in data["turns"] if int(turn["step"]) == 479)
    day19_own = float(day19_turn["players_after"][seat]["cash"])
    day19_rival = float(day19_turn["players_after"][1 - seat]["cash"])
    bins = {
        (player, period): {"net_item": Counter(), "sale_cash": Counter(), "sale_units": Counter(), "atomic": Counter()}
        for player in (0, 1) for period in ("early", "late")
    }
    for event in data["events"]:
        if not event.get("success") or event.get("player") not in (0, 1):
            continue
        period = "late" if int(event["step"]) >= 480 else "early"
        bucket = bins[(int(event["player"]), period)]
        if event["phase"] == "market_unit":
            item = str(event["item"])
            amount = float(event["cash_delta"])
            bucket["net_item"][item] += amount
            if event["operation"] == "SELL":
                bucket["sale_cash"][item] += amount
                bucket["sale_units"][item] += 1
        elif event["phase"] == "market_atomic":
            bucket["atomic"][str(event["operation"])] += float(event["cash_after"]) - float(event["cash_before"])
    result = {
        "episode_id": live["episode_id"], "opponent": live["opponent"],
        "seed": live["seed"], "our_seat": seat, "margin": live["margin"],
        "day19_margin": day19_own - day19_rival,
        "late_margin_change": live["margin"] - (day19_own - day19_rival),
        "periods": {},
    }
    for period in ("early", "late"):
        own = bins[(seat, period)]
        rival = bins[(1 - seat, period)]
        own_cash_change = ((day19_own - 3000) if period == "early" else (live["our_cash"] - day19_own))
        rival_cash_change = ((day19_rival - 3000) if period == "early" else (live["rival_cash"] - day19_rival))
        market_own = sum(own["net_item"].values()) + sum(own["atomic"].values())
        market_rival = sum(rival["net_item"].values()) + sum(rival["atomic"].values())
        items = sorted(set(own["net_item"]) | set(rival["net_item"]))
        result["periods"][period] = {
            "cash_change_margin": own_cash_change - rival_cash_change,
            "net_item_difference": {item: own["net_item"][item] - rival["net_item"][item] for item in items},
            "sale_cash_difference": {item: own["sale_cash"][item] - rival["sale_cash"][item] for item in items},
            "sale_unit_difference": {item: own["sale_units"][item] - rival["sale_units"][item] for item in items},
            "atomic_difference": {name: own["atomic"][name] - rival["atomic"][name]
                                  for name in sorted(set(own["atomic"]) | set(rival["atomic"]))},
            "market_cash_difference": market_own - market_rival,
            "other_cash_difference": (own_cash_change - market_own) - (rival_cash_change - market_rival),
        }
        accounted = sum(result["periods"][period]["net_item_difference"].values())
        accounted += sum(own["atomic"].values()) - sum(rival["atomic"].values())
        accounted += result["periods"][period]["other_cash_difference"]
        assert abs(accounted - result["periods"][period]["cash_change_margin"]) < 1e-6
    assert abs(result["periods"]["early"]["cash_change_margin"] + result["periods"]["late"]["cash_change_margin"] - live["margin"]) < 1e-6
    (CACHE / f"{live['episode_id']}.json").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    lives = [row for row in json.loads((HERE / "audit_latest_100.json").read_text(encoding="utf-8"))["episodes"] if row["outcome"] == "loss"]
    routes = {row["episode_id"]: row for row in json.loads((HERE / "mirror_dev_routes" / "summary.json").read_text(encoding="utf-8"))}
    assert len(lives) == 29 and all(row["episode_id"] in routes for row in lives)
    CACHE.mkdir(exist_ok=True)
    missing = [row for row in lives if not (CACHE / f"{row['episode_id']}.json").exists()]
    with ProcessPoolExecutor(max_workers=3) as pool:
        list(pool.map(play, [(row, routes[row["episode_id"]]) for row in missing]))
    rows = [json.loads((CACHE / f"{row['episode_id']}.json").read_text(encoding="utf-8")) for row in lives]
    late_net = Counter()
    late_sales = Counter()
    late_units = Counter()
    for row in rows:
        late_net.update(row["periods"]["late"]["net_item_difference"])
        late_sales.update(row["periods"]["late"]["sale_cash_difference"])
        late_units.update(row["periods"]["late"]["sale_unit_difference"])
    summary = {"losses": len(rows), "late_margin_change": sum(row["late_margin_change"] for row in rows),
               "day19_leaders": sum(row["day19_margin"] > 0 for row in rows),
               "late_net_item_difference": dict(late_net),
               "late_sale_cash_difference": dict(late_sales),
               "late_sale_unit_difference": dict(late_units),
               "late_market_cash_difference": sum(row["periods"]["late"]["market_cash_difference"] for row in rows),
               "late_other_cash_difference": sum(row["periods"]["late"]["other_cash_difference"] for row in rows)}
    assert abs(summary["late_market_cash_difference"] + summary["late_other_cash_difference"] - summary["late_margin_change"]) < 1e-6
    OUTPUT.write_text(json.dumps({"source_sha256": EXPECTED, "summary": summary, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(OUTPUT)


if __name__ == "__main__":
    main()
