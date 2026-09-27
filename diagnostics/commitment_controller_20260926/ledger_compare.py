"""Compare exact engine cash events for the frozen sheep experiment.

Usage: python -B -X utf8 diagnostics/commitment_controller_20260926/ledger_compare.py
"""

from __future__ import annotations

import gzip
import json
from collections import Counter
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "live_refresh_56530281_20260926"))
from cash_ledger_close import ledger  # noqa: E402

FILES = {
    "A_native": "trace_A_2612002_s0.json.gz",
    "B_native": "trace_B_native_2612002_s0.json.gz",
    "B_matched_shops": "trace_B_matched_2612002_s0.json.gz",
}


def numeric_delta(left: dict, right: dict) -> dict:
    return {key: right.get(key, 0) - left.get(key, 0)
            for key in sorted(left.keys() | right.keys())
            if right.get(key, 0) != left.get(key, 0)}


def summarize(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as source:
        data = json.load(source)
    assert data["candidate_status"] == data["opponent_status"] == "DONE"
    assert data["candidate_seat"] == 0
    rows = data["traces"][0]
    shops = []
    previous = ()
    for row in rows:
        current = tuple(row["observation"]["town"]["unlocked_shops"])
        if current != previous:
            shops.append({"step": row["step"], "shops": current})
            previous = current
    ledgers = [ledger(data, seat) for seat in (0, 1)]
    return {
        "source": path.name,
        "candidate_cash": data["candidate_reward"],
        "rival_cash": data["opponent_reward"],
        "margin": data["margin"],
        "shops": shops,
        "ledgers": ledgers,
        "candidate_timing": data["candidate_timing"],
        "failed_orders": dict(Counter(
            f"{event.get('operation')}:{event.get('failure_reason')}"
            for event in data["events"] if event.get("player") == 0
            and event.get("phase") in ("market_unit", "market_atomic")
            and not event.get("success"))),
    }


def main() -> None:
    results = {name: summarize(HERE / filename)
               for name, filename in FILES.items()}
    base = results["A_native"]
    for name, treatment in results.items():
        comparison = {
            "against": "A_native",
            "arm": name,
            "own_cash_delta": treatment["candidate_cash"] - base["candidate_cash"],
            "rival_cash_delta": treatment["rival_cash"] - base["rival_cash"],
            "margin_delta": treatment["margin"] - base["margin"],
            "seat_ledgers": [],
        }
        for seat in (0, 1):
            before, after = base["ledgers"][seat], treatment["ledgers"][seat]
            comparison["seat_ledgers"].append({
                "seat": seat,
                "sale_cash_delta": numeric_delta(before["sale_cash"], after["sale_cash"]),
                "sale_units_delta": numeric_delta(before["sale_units"], after["sale_units"]),
                "buy_cost_delta": numeric_delta(before["buy_cost"], after["buy_cost"]),
                "atomic_cash_delta": numeric_delta(before["atomic_cash"], after["atomic_cash"]),
                "other_cash_delta": after["other_cash"] - before["other_cash"],
            })
            assert abs(before["final"] - after["final"] - (
                before["market_total"] - after["market_total"]
                + before["other_cash"] - after["other_cash"])) < 1e-6
        results[name]["against_A"] = comparison
    output = HERE / "ledger_2612002_s0.json"
    output.write_text(json.dumps(results, indent=2, default=list), encoding="utf-8")
    for name, row in results.items():
        print(name, "cash", row["candidate_cash"], row["rival_cash"],
              "margin", row["margin"], "shops", row["shops"])
        if name != "A_native":
            print(json.dumps(row["against_A"], indent=2))
    print(output)


if __name__ == "__main__":
    main()
