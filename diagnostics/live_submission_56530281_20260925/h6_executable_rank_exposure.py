"""Read-only scan: would stock-clipped H6 sale scores reorder submitted queues?"""

from collections import Counter
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import main as incumbent  # noqa: E402


def proposed_queue(observation: dict, action: dict) -> tuple[list, int]:
    market = action.get("market") or []
    stock = incumbent.projected_shed(action, incumbent.FarmView(observation))
    slots = []
    rows = []
    overrequested = 0
    for index, order in enumerate(market):
        if not isinstance(order, list) or len(order) < 3 or order[0] != "SELL":
            continue
        if order[1] not in incumbent._H6_MARKET_PARAMS:
            continue
        requested = max(0, int(order[2]))
        effective = min(requested, max(0, int(stock.get(order[1], 0))))
        overrequested += int(requested > effective)
        stock[order[1]] = max(0, int(stock.get(order[1], 0)) - effective)
        scored = list(order)
        scored[2] = effective
        score, _ = incumbent._h6_order_score(observation, None, scored)
        slots.append(index)
        rows.append((score, -index, order))
    rows.sort(reverse=True)
    result = [list(order) if isinstance(order, list) else order for order in market]
    for index, row in zip(slots, rows):
        result[index] = row[2]
    return result, overrequested


def main() -> None:
    audit = json.loads((HERE / "audit_latest_24.json").read_text(encoding="utf-8"))
    total = Counter()
    for entry in audit["episodes"]:
        path = HERE / f"episode-{entry['episode_id']}-replay.json"
        replay = json.loads(path.read_text(encoding="utf-8"))
        ours = int(entry["our_seat"])
        changed = 0
        over = 0
        exposed = 0
        examples = []
        for index in range(1, len(replay["steps"])):
            observation = replay["steps"][index - 1][ours].get("observation") or {}
            action = replay["steps"][index][ours].get("action") or {}
            market = action.get("market") or []
            if not observation or not market:
                continue
            revised, excess = proposed_queue(observation, action)
            over += excess
            exposed += int(excess > 0)
            if revised != market:
                changed += 1
                if len(examples) < 2:
                    examples.append({"step": index - 1, "original": market, "revised": revised})
        total["changed_turns"] += changed
        total["overrequested_orders"] += over
        total["overrequested_turns"] += exposed
        total["episodes_with_change"] += int(changed > 0)
        print(entry["episode_id"], entry["outcome"], f"margin={entry['margin']:+.0f}",
              f"changed={changed}", f"overrequested_orders={over}", "examples=", examples)
    print("TOTAL", dict(total))


if __name__ == "__main__":
    main()
