"""Exact native event cash ledgers for the 17 new public routes."""

from __future__ import annotations

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

MAIN = ROOT / "main.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
ROUTES = HERE / "routes" / "summary.json"
OUTPUT = HERE / "cash_ledgers_17.json"


def trace(route: dict) -> dict:
    seat = int(route["our_seat"])
    data = run(str(MAIN), f"rawroute:{route['path']}", int(route["seed"]), seat)
    assert data["candidate_status"] == data["opponent_status"] == "DONE"
    assert (data["candidate_reward"], data["opponent_reward"]) == (
        route["our_live_cash"], route["rival_live_cash"]), route["episode_id"]
    checkpoint = next(t for t in data["turns"] if int(t["step"]) == 479)
    day19 = (float(checkpoint["players_after"][seat]["cash"]),
             float(checkpoint["players_after"][1-seat]["cash"]))
    bins = {(player, period): {"net": Counter(), "sale_cash": Counter(),
                               "sale_units": Counter(), "atomic": Counter()}
            for player in (0, 1) for period in ("early", "late")}
    for event in data["events"]:
        if not event.get("success") or event.get("player") not in (0, 1):
            continue
        period = "late" if int(event["step"]) >= 480 else "early"
        bucket = bins[(int(event["player"]), period)]
        if event["phase"] == "market_unit":
            item = str(event["item"])
            amount = float(event["cash_delta"])
            bucket["net"][item] += amount
            if event["operation"] == "SELL":
                bucket["sale_cash"][item] += amount
                bucket["sale_units"][item] += 1
        elif event["phase"] == "market_atomic":
            bucket["atomic"][str(event["operation"])] += (
                float(event["cash_after"]) - float(event["cash_before"]))
    periods = {}
    for period in ("early", "late"):
        own, rival = bins[(seat, period)], bins[(1-seat, period)]
        own_change = (day19[0]-3000) if period == "early" else (route["our_live_cash"]-day19[0])
        rival_change = (day19[1]-3000) if period == "early" else (route["rival_live_cash"]-day19[1])
        cash_diff = own_change-rival_change
        net_items = {item: own["net"][item]-rival["net"][item]
                     for item in sorted(set(own["net"]) | set(rival["net"]))}
        sales = {item: own["sale_cash"][item]-rival["sale_cash"][item]
                 for item in sorted(set(own["sale_cash"]) | set(rival["sale_cash"]))}
        units = {item: own["sale_units"][item]-rival["sale_units"][item]
                 for item in sorted(set(own["sale_units"]) | set(rival["sale_units"]))}
        atomics = {item: own["atomic"][item]-rival["atomic"][item]
                   for item in sorted(set(own["atomic"]) | set(rival["atomic"]))}
        market_diff = sum(net_items.values())+sum(atomics.values())
        other = cash_diff-market_diff
        periods[period] = {"cash_margin_change": cash_diff,
                           "net_item_difference": net_items,
                           "sale_cash_difference": sales,
                           "sale_unit_difference": units,
                           "atomic_cash_difference": atomics,
                           "other_cash_difference": other}
        assert abs(cash_diff - (market_diff+other)) < 1e-6
    assert abs(sum(p["cash_margin_change"] for p in periods.values())-route["live_margin"]) < 1e-6
    return {"episode_id": route["episode_id"], "team": route["team"],
            "seed": route["seed"], "our_seat": seat,
            "outcome": route["outcome"], "margin": route["live_margin"],
            "day19_margin": day19[0]-day19[1],
            "periods": periods}


def main() -> None:
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == EXPECTED
    routes = json.loads(ROUTES.read_text(encoding="utf8"))
    assert len(routes) == 17 and len({r["action_sha256"] for r in routes}) == 17
    with ProcessPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(trace, routes))
    losses = [row for row in rows if row["outcome"] == "loss"]
    late_items = Counter()
    total_items = Counter()
    for row in losses:
        for period in ("early", "late"):
            total_items.update(row["periods"][period]["net_item_difference"])
        late_items.update(row["periods"]["late"]["net_item_difference"])
    summary = {"games": len(rows), "wins": len(rows)-len(losses), "losses": len(losses),
               "all_exact_cash_parity": True,
               "loss_total_margin": sum(row["margin"] for row in losses),
               "losses_day19_ahead": sum(row["day19_margin"] > 0 for row in losses),
               "loss_net_item_difference": dict(total_items),
               "loss_late_net_item_difference": dict(late_items)}
    OUTPUT.write_text(json.dumps({"main_sha256": EXPECTED,
                                  "route_manifest_sha256": hashlib.sha256(ROUTES.read_bytes()).hexdigest(),
                                  "summary": summary, "rows": rows},
                                 indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps(summary, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
