"""Exact native cash/sales ledgers for two large ICE/BRUNCH losses."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from trace_paired_game_events import run  # noqa: E402

MAIN = ROOT / "main.py"
CANDIDATE = ROOT / "exp_shunki_later_lookup_20260927.py"
TEAMS = ("Dipam Chakraborty", "mtmr_s1")


def summarize(job: tuple[dict, str]) -> dict:
    target, arm = job
    path = MAIN if arm == "main" else CANDIDATE
    data = run(str(path), f"rawroute:{target['opponent_path']}",
               int(target["seed"]), 0)
    expected = target["seat_margins"]["0"]["main" if arm == "main" else "candidate"]
    assert data["candidate_status"] == data["opponent_status"] == "DONE"
    assert float(data["margin"]) == float(expected)
    periods = [{"net": [Counter(), Counter()],
                "sale_cash": [Counter(), Counter()],
                "sale_units": [Counter(), Counter()],
                "atomic": [Counter(), Counter()]}
               for _ in range(3)]
    for event in data["events"]:
        if not event.get("success") or event.get("player") not in (0, 1):
            continue
        step = int(event["step"])
        period = min(2, step // 240)
        player = int(event["player"])
        bucket = periods[period]
        if event["phase"] == "market_unit":
            item = str(event["item"])
            amount = float(event["cash_delta"])
            bucket["net"][player][item] += amount
            if event["operation"] == "SELL":
                bucket["sale_cash"][player][item] += amount
                bucket["sale_units"][player][item] += 1
        elif event["phase"] == "market_atomic":
            bucket["atomic"][player][str(event["operation"])] += (
                float(event["cash_after"]) - float(event["cash_before"]))
    period_rows = []
    for index, bucket in enumerate(periods):
        ending = data["turns"][min(719, 240 * (index + 1) - 1)]
        period_rows.append({"ending_cash": [float(x["cash"])
                                             for x in ending["players_after"]],
                            **{key: [dict(counter) for counter in bucket[key]]
                               for key in ("net", "sale_cash", "sale_units", "atomic")}})
    shops = [data["traces"][0][t]["observation"]["town"]["unlocked_shops"]
             for t in (72, 144, 216, 288, 360, 432, 504, 576)]
    return {"team": target["team"], "rank": target["rank"], "seed": target["seed"],
            "arm": arm, "cash": [data["candidate_reward"], data["opponent_reward"]],
            "margin": data["margin"], "shops_at_reveals": shops,
            "periods": period_rows}


def main() -> None:
    analysis = json.loads((HERE / "top100_analysis.json").read_text(encoding="utf8"))
    targets = [row for row in analysis["largest_candidate_losses"]
               if row["team"] in TEAMS]
    assert len(targets) == len(TEAMS)
    jobs = [(target, arm) for target in targets for arm in ("main", "candidate")]
    with ProcessPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(summarize, jobs))
    by = {(row["team"], row["arm"]): row for row in rows}
    deltas = []
    for target in targets:
        base = by[(target["team"], "main")]
        trial = by[(target["team"], "candidate")]
        period_deltas = []
        for old_period, new_period in zip(base["periods"], trial["periods"]):
            amounts = {}
            for field in ("net", "sale_cash", "sale_units", "atomic"):
                amounts[field] = []
                for player in (0, 1):
                    keys = set(old_period[field][player]) | set(new_period[field][player])
                    amounts[field].append({key: new_period[field][player].get(key, 0)
                                           - old_period[field][player].get(key, 0)
                                           for key in sorted(keys)})
            period_deltas.append({"ending_cash_delta": [
                new_period["ending_cash"][player] - old_period["ending_cash"][player]
                for player in (0, 1)], **amounts})
        deltas.append({"team": target["team"], "rank": target["rank"],
                       "seed": target["seed"], "main_margin": base["margin"],
                       "candidate_margin": trial["margin"],
                       "candidate_shops": trial["shops_at_reveals"],
                       "period_deltas": period_deltas})
    result = {"rows": rows, "deltas": deltas}
    (HERE / "ice_brunch_cash_ledgers.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    for row in deltas:
        print(row["team"], "margins", row["main_margin"], row["candidate_margin"])
        print("shops", row["candidate_shops"])
        for index, period in enumerate(row["period_deltas"]):
            print("period", index, "cash_delta", period["ending_cash_delta"],
                  "own_net", period["net"][0], "rival_net", period["net"][1])


if __name__ == "__main__":
    main()
