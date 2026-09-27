"""Passive native execution ledger for the five remaining training matchups."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from trace_paired_game_events import run


def main():
    candidate = ROOT / "exp_shunki_shop_optimized_20260927.py"
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == "94f0602f0a6a2d4c1af84f8caf93ee802335582485dd2f796a8c7e5a09846604"
    decision = json.loads((ROOT / "diagnostics/shunki_route_search_20260927/top50_decision.json").read_text(encoding="utf8"))
    routes = json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))
    rows = []
    for case in decision["rows"]:
        if case["new_sweep"]:
            continue
        route = next(r for r in routes if r["team"] == case["team"])
        for seat in ((0, 1) if case["team"] == "ymg_aq" else (0,)):
            path = HERE / f"episode-{route['episode_id']}-seat{seat}.json.gz"
            if path.exists():
                with gzip.open(path, "rt", encoding="utf8") as handle:
                    trace = json.load(handle)
            else:
                trace = run(str(candidate), "rawroute:" + route["path"], route["seed"], seat)
                with gzip.open(path, "wt", encoding="utf8") as handle:
                    json.dump(trace, handle, separators=(",", ":"))
            assert trace["margin"] == case["new_margins"][seat]
            ledgers = []
            for player in (seat, 1 - seat):
                cash, quantities, failures, nochange = defaultdict(float), Counter(), Counter(), Counter()
                for event in trace["events"]:
                    if event["player"] != player:
                        continue
                    if event["phase"] == "market_unit":
                        key = event["operation"] + ":" + event["item"]
                        if event["success"]:
                            cash[key] += event["cash_delta"]
                            quantities[key] += 1
                        else:
                            failures[key + ":" + str(event["failure_reason"])] += 1
                    elif event["phase"] == "market_atomic":
                        cash[event["operation"]] += event["cash_after"] - event["cash_before"]
                        if not event["success"]:
                            failures[event["operation"]] += 1
                    elif event["phase"] == "unit_action" and not event["changed"]:
                        command = event["action"] or ["EMPTY"]
                        nochange[command[0]] += 1
                ledgers.append({"player": player, "cash_by_operation": dict(cash),
                                "units_by_operation": dict(quantities), "market_failures": dict(failures),
                                "unchanged_unit_commands": dict(nochange)})
            row = {"team": case["team"], "seed": route["seed"], "seat": seat, "margin": trace["margin"],
                   "statuses": [trace["candidate_status"], trace["opponent_status"]],
                   "trace": str(path), "ledgers": ledgers}
            rows.append(row)
            (HERE / "ledger.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf8")
            print(case["team"], seat, trace["margin"], "ledger saved", flush=True)


if __name__ == "__main__":
    main()
