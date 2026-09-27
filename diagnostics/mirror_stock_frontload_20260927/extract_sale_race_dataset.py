"""Extract observation-only sale-race features from 100 live public replays."""

from collections import Counter
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_submission_56572390_20260926"
AUDIT = LIVE / "audit_latest_100.json"
DEVELOPMENT = LIVE / "mirror_dev_routes" / "summary.json"
OUTPUT = HERE / "sale_race_dataset.json"
FEATURES = (
    "step", "hour", "stock", "quote", "quote_delta_1", "quote_delta_4",
    "quote_delta_12", "inventory_delta_1", "inventory_delta_4",
    "since_own_strawberry_sale", "since_public_inventory_spike",
    "own_strawberry_plants", "rival_strawberry_plants", "hands_count",
    "strawberry_shop_count", "market_order_count",
)
STRAWBERRY_SHOPS = {"BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET"}


def strawberry_sell(action):
    return any(isinstance(order, list) and len(order) > 2
               and order[0] == "SELL" and order[1] == "STRAWBERRY"
               and int(order[2] or 0) > 0
               for order in ((action or {}).get("market") or []))


def next_sales(steps, seat):
    upcoming = [None] * len(steps)
    next_step = None
    for step in range(len(steps) - 1, -1, -1):
        frame = steps[step][seat]
        if strawberry_sell(frame.get("action")):
            next_step = step
        upcoming[step] = next_step
    return upcoming


def strawberry_plants(farm):
    return sum(isinstance(tile, dict) and tile.get("crop") == "STRAWBERRY"
               for board_row in (farm.get("tiles") or []) for tile in board_row)


def action_eligible(action):
    if not isinstance(action, dict):
        return False
    market = action.get("market") or []
    if not isinstance(market, list) or len(market) >= 10:
        return False
    if any(isinstance(order, list) and order and
           (order[0] == "BUY_PRODUCT" or
            (len(order) > 1 and order[0] == "SELL" and order[1] == "STRAWBERRY"))
           for order in market):
        return False
    commands = [action.get("farmer") or ["PASS"], *(action.get("hands") or [])]
    if any(isinstance(command, list) and len(command) > 1 and
           command[0] == "PICKUP" and command[1] == "STRAWBERRY"
           for command in commands):
        return False
    return True


def opportunity_rows(entry, development_ids):
    episode = int(entry["episode_id"])
    replay_path = LIVE / f"episode-{episode}-replay.json"
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    steps = replay["steps"]
    seat = int(entry["our_seat"])
    own_next = next_sales(steps, seat)
    rival_next = next_sales(steps, 1 - seat)
    quotes = []
    inventories = []
    streak = 0
    latched = False
    armed = True
    last_own_sale = -1000
    last_spike = -1000
    rows = []
    for step in range(min(718, len(steps))):
        frame = steps[step][seat]
        observation = frame["observation"]
        action = frame.get("action") or {}
        farms = observation.get("farms") or []
        market = observation.get("market") or {}
        quote = int((market.get("prices") or {}).get("STRAWBERRY", 0) or 0)
        inventory = int((market.get("inventory") or {}).get("STRAWBERRY", 0) or 0)
        if inventories and inventory - inventories[-1] >= 4:
            last_spike = step
        quotes.append(quote)
        inventories.append(inventory)
        shed = (observation.get("private") or {}).get("shed") or {}
        stock = int(shed.get("STRAWBERRY", 0) or 0)
        sold_now = strawberry_sell(action)
        if stock < 4 or sold_now:
            armed = True
        if 144 <= step < 718 and len(farms) == 2:
            same = (farms[0]["tiles"] == farms[1]["tiles"]
                    and farms[0]["farmer"] == farms[1]["farmer"]
                    and farms[0]["hands"] == farms[1]["hands"])
            streak = streak + 1 if same else 0
            latched = latched or streak >= 24
            aligned = (farms[0]["farmer"] == farms[1]["farmer"]
                       and farms[0]["hands"] == farms[1]["hands"])
        else:
            same = aligned = False
        if (armed and 480 <= step < 718 and latched and not same and aligned
                and stock >= 4 and quote >= 60 and action_eligible(action)):
            own_farm = farms[seat]
            rival_farm = farms[1 - seat]
            own_sale = own_next[step]
            rival_sale = rival_next[step]
            label = (rival_sale is not None and rival_sale - step <= 24
                     and (own_sale is None or rival_sale < own_sale))
            feature_map = {
                "step": step,
                "hour": step % 24,
                "stock": stock,
                "quote": quote,
                "quote_delta_1": quote - quotes[max(0, step - 1)],
                "quote_delta_4": quote - quotes[max(0, step - 4)],
                "quote_delta_12": quote - quotes[max(0, step - 12)],
                "inventory_delta_1": inventory - inventories[max(0, step - 1)],
                "inventory_delta_4": inventory - inventories[max(0, step - 4)],
                "since_own_strawberry_sale": min(120, step - last_own_sale),
                "since_public_inventory_spike": min(120, step - last_spike),
                "own_strawberry_plants": strawberry_plants(own_farm),
                "rival_strawberry_plants": strawberry_plants(rival_farm),
                "hands_count": len(own_farm.get("hands") or []),
                "strawberry_shop_count": sum(shop in STRAWBERRY_SHOPS
                                              for shop in (observation.get("town") or {}).get("unlocked_shops", [])),
                "market_order_count": len(action.get("market") or []),
            }
            assert tuple(feature_map) == FEATURES
            rows.append({"episode_id": episode, "step": step,
                         "train": episode in development_ids,
                         "features": feature_map, "rival_before_own": int(label),
                         "next_own_sale": own_sale, "next_rival_sale": rival_sale})
            armed = False
        if sold_now:
            last_own_sale = step
    return rows


def main():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))["episodes"]
    development = json.loads(DEVELOPMENT.read_text(encoding="utf-8"))
    development_ids = {int(row["episode_id"]) for row in development}
    assert len(audit) == 100 and len(development_ids) == 39
    assert len({int(row["episode_id"]) for row in audit}) == 100
    all_rows = []
    for index, entry in enumerate(audit, 1):
        rows = opportunity_rows(entry, development_ids)
        all_rows.extend(rows)
        if index % 10 == 0:
            print("episodes", index, "opportunities", len(all_rows), flush=True)
    by_split = Counter(("train" if row["train"] else "test", row["rival_before_own"])
                       for row in all_rows)
    payload = {
        "audit_sha256": hashlib.sha256(AUDIT.read_bytes()).hexdigest(),
        "development_sha256": hashlib.sha256(DEVELOPMENT.read_bytes()).hexdigest(),
        "feature_names": FEATURES,
        "episodes": len(audit), "development_episodes": len(development_ids),
        "summary": {f"{split}_label_{label}": count
                    for (split, label), count in sorted(by_split.items())},
        "rows": all_rows,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(OUTPUT)


if __name__ == "__main__":
    main()
