"""Read-only same-turn receipt bound for swapping two adjacent active SELLs.

This replays only premium-product market execution on observed public games.
It knows the rival's recorded current action and is an *oracle diagnostic*,
never a valid agent policy or terminal-score prediction.
"""

from collections import Counter, defaultdict
import json
from pathlib import Path
from sys import path as sys_path

HERE = Path(__file__).resolve().parent
sys_path.insert(0, str(HERE.parents[1]))
import main as incumbent  # noqa: E402
from market_swap_exposure import PREMIUM  # noqa: E402
sys_path.insert(0, str(HERE.parent / "live_clone_margin_20260925"))
from analyze_live_clone_margin import market_price  # noqa: E402


def simulate_item(item: str, market: dict, orders: list[list], stocks: list[int]) -> tuple[list[int], list[int], int]:
    """Mirror per-unit lockstep for one premium product (SELL-only market)."""
    inventory = int(market["inventory"][item])
    receipts = [0, 0]
    filled = [0, 0]
    available = stocks[:]
    for slot in range(max(map(len, orders))):
        remaining = []
        for queue in orders:
            order = queue[slot] if slot < len(queue) else []
            remaining.append(
                max(0, int(order[2]))
                if isinstance(order, list) and len(order) >= 3
                and order[0] == "SELL" and order[1] == item else 0
            )
        while any(remaining[seat] and available[seat] for seat in (0, 1)):
            quote = market_price(item, inventory, market)
            for seat in (0, 1):
                if remaining[seat] and available[seat]:
                    remaining[seat] -= 1
                    available[seat] -= 1
                    receipts[seat] += quote
                    filled[seat] += 1
                    if quote > 1:
                        inventory += 1
    return receipts, filled, inventory


def main() -> None:
    audit = json.loads((HERE / "audit_latest_24.json").read_text(encoding="utf-8"))
    episode_rows = []
    for entry in audit["episodes"]:
        replay_path = HERE / f"episode-{entry['episode_id']}-replay.json"
        replay = json.loads(replay_path.read_text(encoding="utf-8"))
        ours = int(entry["our_seat"])
        records = []
        for i in range(1, len(replay["steps"])):
            before = [replay["steps"][i - 1][seat].get("observation") for seat in (0, 1)]
            after = [replay["steps"][i][seat].get("observation") for seat in (0, 1)]
            actions = [replay["steps"][i][seat].get("action") or {} for seat in (0, 1)]
            if not all(before) or not all(after) or int(before[ours]["day"]) != int(after[ours]["day"]):
                continue
            queue = actions[ours].get("market") or []
            if len(queue) < 2:
                continue
            if any(
                isinstance(order, list) and len(order) > 1
                and order[0] in ("BUY_PRODUCT", "SELL") and order[1] in ("WHEAT", "FERTILIZER")
                for order in queue
            ):
                continue
            stocks = [
                incumbent.projected_shed(actions[seat], incumbent.FarmView(before[seat]))
                for seat in (0, 1)
            ]
            all_orders = [actions[seat].get("market") or [] for seat in (0, 1)]
            for slot in range(1, len(queue)):
                earlier, later = queue[slot - 1], queue[slot]
                if not all(isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] in PREMIUM and int(o[2]) > 0 for o in (earlier, later)):
                    continue
                if earlier[1] == later[1]:
                    continue
                items = (earlier[1], later[1])
                if any(sum(isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] == item for o in queue) != 1 for item in items):
                    continue
                if any(float(before[ours]["market"]["prices"].get(item, 0)) <= 1 for item in items):
                    continue
                baseline = {}
                trusted = True
                for item in items:
                    receipts, filled, inventory = simulate_item(
                        item, before[ours]["market"], all_orders,
                        [int(stocks[seat].get(item, 0)) for seat in (0, 1)],
                    )
                    observed_inventory = int(after[ours]["market"]["inventory"][item])
                    if inventory != observed_inventory:
                        trusted = False
                    for seat in (0, 1):
                        if int(stocks[seat].get(item, 0)) - filled[seat] != int(after[seat]["private"]["shed"].get(item, 0)):
                            trusted = False
                    baseline[item] = receipts
                if not trusted:
                    records.append({"step": i, "slot": slot, "trusted": False})
                    continue
                swapped = [list(o) if isinstance(o, list) else o for o in queue]
                swapped[slot - 1], swapped[slot] = swapped[slot], swapped[slot - 1]
                alternative_orders = list(all_orders)
                alternative_orders[ours] = swapped
                deltas = [0, 0]
                for item in items:
                    receipts, filled, inventory = simulate_item(
                        item, before[ours]["market"], alternative_orders,
                        [int(stocks[seat].get(item, 0)) for seat in (0, 1)],
                    )
                    for seat in (0, 1):
                        deltas[seat] += receipts[seat] - baseline[item][seat]
                records.append({
                    "step": i, "slot": slot, "trusted": True,
                    "items": items, "requested": (int(earlier[2]), int(later[2])),
                    "own_receipt_delta": deltas[ours],
                    "rival_receipt_delta": deltas[1 - ours],
                })
        episode_rows.append((entry, records))
    totals = Counter()
    for entry, records in episode_rows:
        trusted = [row for row in records if row["trusted"]]
        better = [row for row in trusted if row["own_receipt_delta"] > 0]
        total_gain = sum(row["own_receipt_delta"] for row in better)
        totals["trusted"] += len(trusted)
        totals["untrusted"] += len(records) - len(trusted)
        totals["positive"] += len(better)
        totals["oracle_gain"] += total_gain
        if trusted:
            print(
                entry["episode_id"], entry["outcome"], f"margin={entry['margin']:+.0f}",
                f"trusted={len(trusted)} positive={len(better)} oracle_gain={total_gain}",
                "best=", sorted(better, key=lambda row: -row["own_receipt_delta"])[:2],
            )
    print("TOTAL", dict(totals))


if __name__ == "__main__":
    main()
