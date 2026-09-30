"""Development-only opportunity audit using past public worker positions."""
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module

ITEMS = {"CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"}


def signature(farm):
    return (tuple(farm["farmer"]), tuple(tuple(p) for p in farm["hands"]))


def main():
    routes = json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/routes/summary.json").read_text(encoding="utf8"))
    models = []
    for row in routes:
        replay = json.loads(Path(row["replay_path"]).read_text(encoding="utf8"))
        seat = row["source_seat"]
        positions = [signature(frame[seat]["observation"]["farms"][seat]) for frame in replay["steps"][:719]]
        actions = [frame[seat]["action"] for frame in replay["steps"][1:]]
        models.append({"team": row["team"], "positions": positions, "actions": actions})
    candidate = _load_module(ROOT / "exp_shunki_shop_optimized_20260927.py", "race_diagnostic")
    ledgers = json.loads((HERE / "ledger.json").read_text(encoding="utf8"))
    results = []
    for row in ledgers:
        with gzip.open(row["trace"], "rt", encoding="utf8") as f:
            trace = json.load(f)
        records = trace["traces"][row["seat"]]
        past = []
        opportunities, matched_turns, correct_items, predictions = [], 0, 0, 0
        for rec in records:
            step, obs, action = rec["step"], rec["observation"], rec["action"]
            past.append(signature(obs["farms"][1 - row["seat"]]))
            if step < 144 or len(set(past[-8:])) < 3:
                continue
            matches = [m for m in models if m["positions"][step-7:step+1] == past[-8:]]
            if not matches:
                continue
            matched_turns += 1
            # Predict only sale quantities on which all physically matching
            # source models agree. No identity, seed, future position or result.
            sales = []
            for model in matches:
                counts = {}
                for order in model["actions"][step].get("market", []):
                    if len(order) >= 3 and order[0] == "SELL" and order[1] in ITEMS:
                        counts[order[1]] = counts.get(order[1], 0) + int(order[2])
                sales.append(counts)
            predicted = {item: min(s.get(item, 0) for s in sales) for item in ITEMS}
            real = {}
            for order in trace["traces"][1-row["seat"]][step]["action"].get("market", []):
                if len(order) >= 3 and order[0] == "SELL":
                    real[order[1]] = real.get(order[1], 0) + int(order[2])
            for item, qty in predicted.items():
                if qty > 0:
                    predictions += 1
                    correct_items += qty <= real.get(item, 0)
                available = obs["private"]["shed"].get(item, 0)
                if qty <= 0 or available <= 0 or any(o[:2] == ["SELL", item] for o in action.get("market", [])):
                    continue
                scheduled = []
                for future in range(step+1, min(step+4, 718)+1):
                    if future // 72 != step // 72:
                        break
                    planned = candidate.agent({"step": future, "town": obs["town"]})
                    for order in planned.get("market", []):
                        if order[:2] == ["SELL", item] and len(order) >= 3:
                            scheduled.append([future, order[2]])
                if scheduled:
                    opportunities.append({"step": step, "item": item, "stock": available,
                                          "predicted_rival_sale": qty, "actual_sale": real.get(item, 0),
                                          "scheduled_own": scheduled, "source_matches": len(matches)})
        results.append({"team": row["team"], "seat": row["seat"], "matched_turns": matched_turns,
                        "sale_item_predictions": predictions, "correct_lower_bounds": correct_items,
                        "opportunities": opportunities})
        print(row["team"], row["seat"], "matches", matched_turns, "sale opportunities", len(opportunities), flush=True)
    (HERE / "sale_race_audit.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf8")


if __name__ == "__main__":
    main()
