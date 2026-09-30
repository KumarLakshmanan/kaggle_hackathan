"""Executed-cash reconciliation for both activated whole-route control seeds."""

from __future__ import annotations

import gzip
import json
from collections import Counter
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "live_refresh_56530281_20260926"))
from cash_ledger_close import ledger  # noqa: E402


def read(name: str) -> dict:
    with gzip.open(HERE / name, "rt", encoding="utf-8") as source:
        return json.load(source)


def diff(a: dict, b: dict) -> dict:
    return {key: b.get(key, 0) - a.get(key, 0)
            for key in sorted(a.keys() | b.keys())
            if b.get(key, 0) != a.get(key, 0)}


def noops(data: dict, player: int) -> dict:
    events = data["events"]
    physical = sum(event.get("phase") == "unit_action"
                   and event.get("player") == player
                   and event.get("action", ["PASS"])[0] != "PASS"
                   and not event.get("changed") for event in events)
    failed_market = Counter(
        str(event.get("operation")) + ":" + str(event.get("failure_reason"))
        for event in events if event.get("player") == player
        and event.get("phase") in ("market_unit", "market_atomic")
        and not event.get("success"))
    return {"physical_nonpass_nochange": physical,
            "failed_market_event_counts": dict(failed_market)}


def compare(seed: int) -> dict:
    baseline = read(f"route_trace_A_{seed}_s0.json.gz")
    forced = read(f"route_trace_C_{seed}_s0.json.gz")
    assert baseline["candidate_status"] == baseline["opponent_status"] == "DONE"
    assert forced["candidate_status"] == forced["opponent_status"] == "DONE"
    assert baseline["candidate_seat"] == forced["candidate_seat"] == 0
    own0, own1 = ledger(baseline, 0), ledger(forced, 0)
    rival0, rival1 = ledger(baseline, 1), ledger(forced, 1)
    own_delta = own1["final"] - own0["final"]
    rival_delta = rival1["final"] - rival0["final"]
    assert own_delta - rival_delta == forced["margin"] - baseline["margin"]
    assert all(abs(row["other_cash"]) < 1e-6
               for row in (own0, own1, rival0, rival1))
    return {
        "seed": seed,
        "baseline_cash": [baseline["candidate_reward"], baseline["opponent_reward"]],
        "forced_cash": [forced["candidate_reward"], forced["opponent_reward"]],
        "delta_own": own_delta,
        "delta_rival": rival_delta,
        "delta_margin": own_delta - rival_delta,
        "own_sale_cash_delta": diff(own0["sale_cash"], own1["sale_cash"]),
        "own_sale_units_delta": diff(own0["sale_units"], own1["sale_units"]),
        "own_buy_cost_delta": diff(own0["buy_cost"], own1["buy_cost"]),
        "own_atomic_cash_delta": diff(own0["atomic_cash"], own1["atomic_cash"]),
        "rival_sale_cash_delta": diff(rival0["sale_cash"], rival1["sale_cash"]),
        "rival_sale_units_delta": diff(rival0["sale_units"], rival1["sale_units"]),
        "rival_buy_cost_delta": diff(rival0["buy_cost"], rival1["buy_cost"]),
        "rival_atomic_cash_delta": diff(rival0["atomic_cash"], rival1["atomic_cash"]),
        "own_noops_A": noops(baseline, 0),
        "own_noops_C": noops(forced, 0),
        "rival_noops_A": noops(baseline, 1),
        "rival_noops_C": noops(forced, 1),
        "shop_sequence_A": [(r["step"], r["observation"]["town"]["unlocked_shops"])
                            for r in baseline["traces"][0]
                            if r["step"] > 0 and r["step"] % 72 == 0],
        "shop_sequence_C": [(r["step"], r["observation"]["town"]["unlocked_shops"])
                            for r in forced["traces"][0]
                            if r["step"] > 0 and r["step"] % 72 == 0],
    }


def main() -> None:
    results = [compare(seed) for seed in (2613002, 2613015)]
    output = HERE / "route_ledger_activated_s0.json"
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    for result in results:
        print(json.dumps(result, indent=2))
    print(output)


if __name__ == "__main__":
    main()
