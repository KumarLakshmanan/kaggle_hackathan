"""Observation-only multi-product sale-race opportunities from 100 live replays."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_submission_56572390_20260926"
AUDIT = LIVE / "audit_latest_100.json"
DEVELOPMENT = LIVE / "mirror_dev_routes" / "summary.json"
OUTPUT = HERE / "opportunities.json"
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER")
ANIMAL_PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}


def sale_items(action: dict | None) -> set[str]:
    return {str(order[1]) for order in ((action or {}).get("market") or [])
            if isinstance(order, list) and len(order) >= 3
            and order[0] == "SELL" and order[1] in PRODUCTS
            and int(order[2] or 0) > 0}


def next_sale_arrays(steps: list, seat: int) -> dict[str, list[int | None]]:
    size = len(steps)
    arrays = {item: [None] * size for item in PRODUCTS}
    current = {item: None for item in PRODUCTS}
    for step in range(size - 1, -1, -1):
        sold = sale_items(steps[step][seat].get("action"))
        for item in sold:
            current[item] = step
        for item in PRODUCTS:
            arrays[item][step] = current[item]
    return arrays


def counts(farm: dict) -> dict[str, int]:
    out = Counter()
    for line in farm.get("tiles") or []:
        for tile in line:
            if isinstance(tile, dict):
                item = tile.get("crop") or ANIMAL_PRODUCT.get(tile.get("animal"))
                if item:
                    out[item] += 1
    return dict(out)


def legal_slot(action: dict, item: str) -> bool:
    market = action.get("market") or []
    if len(market) >= 10:
        return False
    if any(isinstance(order, list) and len(order) > 1 and order[1] == item
           and order[0] in ("SELL", "BUY_PRODUCT") for order in market):
        return False
    commands = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
    if any(isinstance(command, list) and len(command) > 1
           and command[:2] == ["PICKUP", item] for command in commands):
        return False
    return True


def physical_fraction(farms: list[dict]) -> float:
    if len(farms) != 2:
        return 0.0
    left, right = farms
    matches = total = 0
    for a, b in zip(left.get("tiles") or [], right.get("tiles") or []):
        for x, y in zip(a, b):
            total += 1
            matches += x == y
    return matches / total if total else 0.0


def extract(entry: dict, development_ids: set[int]) -> list[dict]:
    episode = int(entry["episode_id"])
    replay = json.loads((LIVE / f"episode-{episode}-replay.json").read_text(encoding="utf8"))
    steps = replay["steps"]
    seat = int(entry["our_seat"])
    own_next = next_sale_arrays(steps, seat)
    rival_next = next_sale_arrays(steps, 1 - seat)
    armed = {item: True for item in PRODUCTS}
    last_own_sale = {item: -1000 for item in PRODUCTS}
    quote_history = {item: [] for item in PRODUCTS}
    inventory_history = {item: [] for item in PRODUCTS}
    own_money_history = []
    rival_money_history = []
    output = []
    for step in range(min(718, len(steps))):
        frame = steps[step][seat]
        obs = frame["observation"]
        action = frame.get("action") or {}
        farms = obs.get("farms") or []
        if len(farms) != 2:
            continue
        own_farm, rival_farm = farms[seat], farms[1 - seat]
        market = obs.get("market") or {}
        prices = market.get("prices") or {}
        inventory = market.get("inventory") or {}
        shed = (obs.get("private") or {}).get("shed") or {}
        sold = sale_items(action)
        own_counts, rival_counts = counts(own_farm), counts(rival_farm)
        physical = physical_fraction(farms)
        own_money_history.append(float(own_farm.get("money", 0) or 0))
        rival_money_history.append(float(rival_farm.get("money", 0) or 0))
        for item in PRODUCTS:
            quote = int(prices.get(item, 0) or 0)
            level = int(inventory.get(item, 0) or 0)
            quote_history[item].append(quote)
            inventory_history[item].append(level)
            stock = int(shed.get(item, 0) or 0)
            if stock < 3 or item in sold:
                armed[item] = True
            future_own = own_next[item][step]
            if (armed[item] and 144 <= step < 718 and stock >= 3
                    and item not in sold and legal_slot(action, item)
                    and future_own is not None and 1 <= future_own - step <= 24):
                future_rival = rival_next[item][step]
                positive = (future_rival is not None and
                            1 <= future_rival - step <= 12 and future_rival < future_own)
                features = {
                    "item": item, "step": step, "hour": step % 24,
                    "stock": stock, "quote": quote, "market_inventory": level,
                    "quote_delta_1": quote - quote_history[item][max(0, step - 1)],
                    "quote_delta_4": quote - quote_history[item][max(0, step - 4)],
                    "inventory_delta_1": level - inventory_history[item][max(0, step - 1)],
                    "inventory_delta_4": level - inventory_history[item][max(0, step - 4)],
                    "since_own_sale": min(120, step - last_own_sale[item]),
                    "own_producers": own_counts.get(item, 0),
                    "rival_producers": rival_counts.get(item, 0),
                    "own_money_delta_4": own_money_history[-1] - own_money_history[max(0, len(own_money_history) - 5)],
                    "rival_money_delta_4": rival_money_history[-1] - rival_money_history[max(0, len(rival_money_history) - 5)],
                    "physical_match_fraction": physical,
                    "market_order_count": len(action.get("market") or []),
                }
                output.append({"episode_id": episode, "step": step,
                               "train": episode in development_ids,
                               "features": features, "rival_before_own": int(positive),
                               "next_own_sale": future_own,
                               "next_rival_sale": future_rival})
                armed[item] = False
            if item in sold:
                last_own_sale[item] = step
    return output


def main() -> None:
    audit = json.loads(AUDIT.read_text(encoding="utf8"))["episodes"]
    development = json.loads(DEVELOPMENT.read_text(encoding="utf8"))
    development_ids = {int(row["episode_id"]) for row in development}
    assert len(audit) == 100 and len(development_ids) == 39
    assert len({int(row["episode_id"]) for row in audit}) == 100
    rows = []
    for index, entry in enumerate(audit, 1):
        rows.extend(extract(entry, development_ids))
        if index % 10 == 0:
            print("episodes", index, "opportunities", len(rows), flush=True)
    labels = Counter(("train" if row["train"] else "holdout", row["rival_before_own"])
                     for row in rows)
    positives = Counter(("train" if row["train"] else "holdout", row["features"]["item"])
                        for row in rows if row["rival_before_own"])
    positive_episodes = {row["episode_id"] for row in rows
                         if not row["train"] and row["rival_before_own"]}
    summary = {
        "labels": {f"{split}_{label}": n for (split, label), n in sorted(labels.items())},
        "positive_items": {f"{split}_{item}": n for (split, item), n in sorted(positives.items())},
        "holdout_positive_episodes": len(positive_episodes),
        "data_gate": (labels[("holdout", 1)] >= 20
                      and len(positive_episodes) >= 10
                      and sum(n >= 5 for (split, item), n in positives.items()
                              if split == "holdout") >= 2),
    }
    payload = {"audit_sha256": hashlib.sha256(AUDIT.read_bytes()).hexdigest(),
               "development_sha256": hashlib.sha256(DEVELOPMENT.read_bytes()).hexdigest(),
               "episodes": len(audit), "development_episodes": len(development_ids),
               "summary": summary, "rows": rows}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
