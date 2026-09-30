"""Read-only summary of already captured native 4ee replay traces.

Opponent inputs are recorded action routes. No opponent source is loaded.
This produces mechanism evidence, not an independent strength estimate.
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def period(step):
    day = int(step) // 24
    return "d00_09" if day < 10 else "d10_19" if day < 20 else "d20_29"


def summarize_player(trace, player):
    sales = defaultdict(float)
    buys = defaultdict(float)
    sale_units = Counter()
    buy_units = Counter()
    failures = Counter()
    actions = Counter()
    productive = Counter()
    period_cash = defaultdict(float)
    period_sales = defaultdict(float)
    cash_atomic = defaultdict(float)
    atomic_success = Counter()
    first_last = {}
    for event in trace["events"]:
        if event.get("player") != player:
            continue
        phase = event["phase"]
        step = event["step"]
        if phase == "market_unit":
            op, item = event["operation"], event["item"]
            if event["success"]:
                amount = float(event["cash_delta"])
                period_cash[period(step)] += amount
                if op == "SELL":
                    sales[item] += amount
                    sale_units[item] += 1
                    period_sales[period(step)] += amount
                else:
                    buys[op + ":" + item] += amount
                    buy_units[op + ":" + item] += 1
                    first_last.setdefault(op + ":" + item, [step, step])[1] = step
            else:
                failures[op + ":" + item + ":" + str(event["failure_reason"])] += 1
        elif phase == "market_atomic":
            op = event["operation"]
            if event["success"]:
                amount = float(event["cash_after"] - event["cash_before"])
                cash_atomic[op] += amount
                atomic_success[op] += 1
                period_cash[period(step)] += amount
                first_last.setdefault(op, [step, step])[1] = step
            else:
                failures[op] += 1
        elif phase == "unit_action":
            action = event.get("action") or ["EMPTY"]
            op = str(action[0])
            if op != "PASS":
                actions[op] += 1
                if event["changed"]:
                    productive[op] += 1
    records = trace["traces"][player]
    milestones = {}
    for step in (0, 72, 144, 216, 288, 360, 432, 504, 576, 648, 718):
        rec = records[step]
        obs = rec["observation"]
        farm = obs["farms"][player]
        tiles = Counter()
        for row in farm["tiles"]:
            for tile in row:
                if isinstance(tile, dict):
                    kind = tile.get("crop") or tile.get("animal")
                    if kind:
                        tiles[kind] += 1
        milestones[str(step)] = {
            "cash_before": farm["money"],
            "hands": len(farm["hands"]),
            "land": len(farm["unlocked_quadrants"]),
            "tiles": dict(tiles),
            "shed": {k: v for k, v in (obs.get("private", {}).get("shed") or {}).items() if v},
            "shops": obs["town"]["unlocked_shops"],
        }
    return {
        "sales_cash": dict(sorted(sales.items())), "sales_units": dict(sorted(sale_units.items())),
        "buys_cash": dict(sorted(buys.items())), "buy_units": dict(sorted(buy_units.items())),
        "atomic_cash": dict(cash_atomic), "atomic_success": dict(atomic_success),
        "failures": dict(failures), "worker_commands": dict(actions),
        "worker_changed": dict(productive), "period_cash_market": dict(period_cash),
        "period_sales_cash": dict(period_sales), "first_last_investment": first_last,
        "milestones": milestones,
    }


def main():
    panels = json.loads((ROOT / "diagnostics/shunki_purchase_iterated_20260927/panels.json").read_text(encoding="utf-8"))
    expected = {(r["panel"], r["team"], r["candidate_seat"]): r for r in panels["games"]}
    top20 = json.loads((ROOT / "diagnostics/current_top20_20260927_163500/assessment.json").read_text(encoding="utf-8"))
    expected.update({("top20", r["team"], r["candidate_seat"]): r for r in top20["games"]})
    rows = []
    for path in sorted(HERE.glob("trace_*.json.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            trace = json.load(fh)
        stem = path.stem.removesuffix(".json")
        _, panel, team, seat_string = stem.split("_", 3)
        team = {"Majkel": "Majkel1337", "WeWanna": "We wanna be tomatos",
                "Vadim": "Vadim Vasilenko"}.get(team, team)
        seat = int(seat_string[1:])
        key = ({"current": "current100", "original": "original50", "top20": "top20"}[panel], team, seat)
        baseline = expected[key]
        assert trace["margin"] == baseline["margin"], (key, trace["margin"], baseline["margin"])
        assert trace["candidate_reward"] == baseline["candidate_reward"]
        assert trace["opponent_reward"] == baseline["opponent_reward"]
        assert trace["candidate_status"] == trace["opponent_status"] == "DONE"
        assert len(trace["turns"]) == 720
        rows.append({
            "panel": key[0], "team": team, "rank": baseline["rank"],
            "episode_id": baseline["episode_id"], "seed": baseline["seed"],
            "seat": seat, "margin": trace["margin"],
            "cash": [trace["candidate_reward"], trace["opponent_reward"]],
            "trace": str(path),
            "candidate": summarize_player(trace, seat),
            "opponent": summarize_player(trace, 1 - seat),
        })
    output = {"created_at_utc": datetime.now(timezone.utc).isoformat(),
              "candidate_sha256": panels["candidate_sha256"],
              "interpretation": "Saved-action native replays; causal diagnosis only, not independent policy validation.",
              "rows": rows}
    (HERE / "ledger.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    for row in rows:
        a, b = row["candidate"], row["opponent"]
        print(row["panel"], row["team"], row["seat"], "margin", row["margin"],
              "cash", row["cash"], "sales", round(sum(a["sales_cash"].values())),
              round(sum(b["sales_cash"].values())), "failed", a["failures"])


if __name__ == "__main__":
    main()
