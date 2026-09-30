"""Reconstruct exact executed-cash ledger on preselected close live games."""

from __future__ import annotations

from collections import Counter
import concurrent.futures
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from trace_paired_game_events import run  # noqa: E402

SUBMITTED = ROOT / "main_before_top10_goal_20260926_04b0bdc3.py"
# Eight smallest near-mirror live losses, plus three close near-mirror wins.
EPISODES = (
    113363691, 113386304, 113342041, 113397194,
    113356930, 113394363, 113297174, 113326562,
    113321656, 113361461, 113381219,
)


def ledger(data: dict, seat: int) -> dict:
    net_by_item: Counter[str] = Counter()
    sale_cash: Counter[str] = Counter()
    buy_cost: Counter[str] = Counter()
    sale_units: Counter[str] = Counter()
    atomic_cash: Counter[str] = Counter()
    market_total = 0.0
    for event in data["events"]:
        if event.get("player") != seat or not event.get("success"):
            continue
        phase = event.get("phase")
        op = str(event.get("operation", ""))
        if phase == "market_unit":
            item = str(event.get("item", ""))
            delta = float(event.get("cash_delta", 0))
            net_by_item[item] += delta
            market_total += delta
            if op == "SELL":
                sale_cash[item] += delta
                sale_units[item] += 1
            elif delta < 0:
                buy_cost[f"{op}:{item}"] += -delta
        elif phase == "market_atomic":
            delta = float(event.get("cash_after", 0)) - float(event.get("cash_before", 0))
            atomic_cash[op] += delta
            market_total += delta
    final = float(data["candidate_reward"] if seat == data["candidate_seat"]
                  else data["opponent_reward"])
    return {
        "final": final,
        "net_market_by_item": dict(net_by_item),
        "sale_cash": dict(sale_cash),
        "buy_cost": dict(buy_cost),
        "sale_units": dict(sale_units),
        "atomic_cash": dict(atomic_cash),
        "market_total": market_total,
        "other_cash": final - 3000.0 - market_total,
    }


def play(job: tuple[dict, dict]) -> dict:
    source, live = job
    episode = int(source["episode_id"])
    seat = int(live["our_seat"])
    assert int(source["seed"]) == int(live["seed"])
    data = run(
        candidate=str(SUBMITTED), opponent=f"rawroute:{source['path']}",
        seed=int(source["seed"]), candidate_seat=seat,
    )
    assert data["candidate_status"] == data["opponent_status"] == "DONE"
    assert (data["candidate_reward"], data["opponent_reward"]) == (
        live["our_cash"], live["rival_cash"]
    ), episode
    ours = ledger(data, seat)
    rival = ledger(data, 1 - seat)
    items = sorted(set(ours["net_market_by_item"]) | set(rival["net_market_by_item"]))
    return {
        "episode_id": episode, "opponent": live["opponent"],
        "seed": live["seed"], "our_seat": seat, "live_margin": live["margin"],
        "exact_action_matches": live["exact_action_matches"],
        "ours": ours, "rival": rival,
        "net_item_differences": {
            item: ours["net_market_by_item"].get(item, 0)
            - rival["net_market_by_item"].get(item, 0) for item in items
        },
        "atomic_cash_difference": sum(ours["atomic_cash"].values())
        - sum(rival["atomic_cash"].values()),
        "other_cash_difference": ours["other_cash"] - rival["other_cash"],
    }


def main() -> None:
    episodes = tuple(int(raw) for raw in sys.argv[1:]) or EPISODES
    assert set(episodes) <= set(EPISODES)
    sources = {int(r["episode_id"]): r for r in json.loads(
        (HERE / "summary.json").read_text(encoding="utf-8"))}
    lives = {int(r["episode_id"]): r for r in json.loads(
        (HERE / "audit_latest_40.json").read_text(encoding="utf-8"))["episodes"]}
    jobs = [(sources[episode], lives[episode]) for episode in episodes]
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(play, jobs))
    assert len(rows) == len(episodes)
    for row in rows:
        total = (sum(row["net_item_differences"].values())
                 + row["atomic_cash_difference"] + row["other_cash_difference"])
        assert abs(total - row["live_margin"]) < 1e-6, row["episode_id"]
        print(row["episode_id"], row["live_margin"],
              "net market", round(sum(row["net_item_differences"].values())
                                  + row["atomic_cash_difference"]),
              "other", round(row["other_cash_difference"]),
              "worst items", sorted(row["net_item_differences"].items(),
                                    key=lambda kv: kv[1])[:3])
    output = HERE / ("cash_ledger_close.json" if episodes == EPISODES
                     else "cash_ledger_pilot.json")
    output.write_text(json.dumps({"episodes": episodes, "rows": rows},
                                 indent=2, ensure_ascii=False), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
