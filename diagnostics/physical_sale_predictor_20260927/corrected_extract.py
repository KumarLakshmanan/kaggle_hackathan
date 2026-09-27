"""Align every action with the observation where it was chosen, not its result frame."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.multigood_sale_race_20260927 import extract_dataset as prior  # noqa: E402
from diagnostics.physical_sale_predictor_20260927.extract_features import physical  # noqa: E402

OLD_AUDIT = HERE.parent / "live_submission_56572390_20260926" / "audit_latest_100.json"
NEW_AUDIT = HERE / "audit_new.json"
OUTPUT = HERE / "physical_opportunities_corrected.json"


def sale_arrays(actions: list[dict]) -> dict[str, list[int | None]]:
    size = len(actions)
    arrays = {item: [None] * size for item in prior.PRODUCTS}
    next_sale = {item: None for item in prior.PRODUCTS}
    for turn in range(size-1, -1, -1):
        for item in prior.sale_items(actions[turn]):
            next_sale[item] = turn
        for item in prior.PRODUCTS:
            arrays[item][turn] = next_sale[item]
    return arrays


def extract(entry: dict, replay_dir: Path, train: bool) -> list[dict]:
    episode = int(entry["episode_id"])
    replay = json.loads((replay_dir / f"episode-{episode}-replay.json").read_text(encoding="utf8"))
    steps = replay["steps"]
    seat = int(entry["our_seat"])
    # Frame t is the observation AFTER action t-1. Actual action t appears
    # in frame t+1, as also used by the frozen public-route extractor.
    actions = [[steps[t+1][player].get("action") or {} for t in range(len(steps)-1)]
               for player in (0, 1)]
    own_next = sale_arrays(actions[seat])
    rival_next = sale_arrays(actions[1-seat])
    armed = {item: True for item in prior.PRODUCTS}
    last_sale = {item: -1000 for item in prior.PRODUCTS}
    quotes = {item: [] for item in prior.PRODUCTS}
    levels = {item: [] for item in prior.PRODUCTS}
    own_money = []
    rival_money = []
    rows = []
    for turn in range(min(719, len(steps)-1)):
        obs = steps[turn][seat]["observation"]
        assert int(obs.get("step", turn)) == turn and int(obs["player"]) == seat
        action = actions[seat][turn]
        farms = obs.get("farms") or []
        if len(farms) != 2:
            continue
        own, rival = farms[seat], farms[1-seat]
        market = obs.get("market") or {}
        prices, inventory = market.get("prices") or {}, market.get("inventory") or {}
        shed = (obs.get("private") or {}).get("shed") or {}
        sold = prior.sale_items(action)
        own_counts, rival_counts = prior.counts(own), prior.counts(rival)
        match = prior.physical_fraction(farms)
        own_money.append(float(own.get("money", 0) or 0))
        rival_money.append(float(rival.get("money", 0) or 0))
        for item in prior.PRODUCTS:
            quote = int(prices.get(item, 0) or 0)
            level = int(inventory.get(item, 0) or 0)
            quotes[item].append(quote)
            levels[item].append(level)
            stock = int(shed.get(item, 0) or 0)
            if stock < 3 or item in sold:
                armed[item] = True
            future_own = own_next[item][turn]
            if (armed[item] and 144 <= turn < 718 and stock >= 3
                    and item not in sold and prior.legal_slot(action, item)
                    and future_own is not None and 1 <= future_own-turn <= 24):
                # The decision-turn rival action is unobserved; label only
                # strictly subsequent turns 1..12.
                future_rival = (rival_next[item][turn+1]
                                if turn+1 < len(actions[1-seat]) else None)
                positive = (future_rival is not None and
                            1 <= future_rival-turn <= 12 and future_rival < future_own)
                features = {
                    "item": item, "step": turn, "hour": turn % 24,
                    "stock": stock, "quote": quote, "market_inventory": level,
                    "quote_delta_1": quote-quotes[item][max(0, turn-1)],
                    "quote_delta_4": quote-quotes[item][max(0, turn-4)],
                    "inventory_delta_1": level-levels[item][max(0, turn-1)],
                    "inventory_delta_4": level-levels[item][max(0, turn-4)],
                    "since_own_sale": min(120, turn-last_sale[item]),
                    "own_producers": own_counts.get(item, 0),
                    "rival_producers": rival_counts.get(item, 0),
                    "own_money_delta_4": own_money[-1]-own_money[max(0, len(own_money)-5)],
                    "rival_money_delta_4": rival_money[-1]-rival_money[max(0, len(rival_money)-5)],
                    "physical_match_fraction": match,
                    "market_order_count": len(action.get("market") or []),
                }
                features.update(physical(obs, seat, item))
                rows.append({"episode_id": episode, "step": turn, "train": train,
                             "features": features, "rival_before_own": int(positive),
                             "next_own_sale": future_own,
                             "next_rival_sale": future_rival})
                armed[item] = False
            if item in sold:
                last_sale[item] = turn
    return rows


def main() -> None:
    old = json.loads(OLD_AUDIT.read_text(encoding="utf8"))["episodes"]
    new = json.loads(NEW_AUDIT.read_text(encoding="utf8"))["episodes"]
    assert len(old) == 100 and len(new) == 17
    old_ids = {int(row["episode_id"]) for row in old}
    new_ids = {int(row["episode_id"]) for row in new}
    assert not old_ids & new_ids and min(new_ids) > max(old_ids)
    rows = []
    for index, entry in enumerate(old, 1):
        rows.extend(extract(entry, OLD_AUDIT.parent, True))
        if index % 20 == 0:
            print("old episodes", index, "rows", len(rows), flush=True)
    for entry in new:
        rows.extend(extract(entry, HERE, False))
    labels = Counter(("train" if row["train"] else "holdout", row["rival_before_own"])
                     for row in rows)
    positive_episodes = {row["episode_id"] for row in rows
                         if not row["train"] and row["rival_before_own"]}
    positive_items = Counter(row["features"]["item"] for row in rows
                             if not row["train"] and row["rival_before_own"])
    summary = {"labels": {f"{split}_{label}": n for (split, label), n in sorted(labels.items())},
               "holdout_positive_episodes": len(positive_episodes),
               "holdout_positive_items": dict(sorted(positive_items.items())),
               "data_gate": (labels[("holdout", 1)] >= 100 and len(positive_episodes) >= 10
                             and sum(n >= 10 for n in positive_items.values()) >= 2)}
    payload = {"old_audit_sha256": hashlib.sha256(OLD_AUDIT.read_bytes()).hexdigest(),
               "new_audit_sha256": hashlib.sha256(NEW_AUDIT.read_bytes()).hexdigest(),
               "development_episodes": 100, "holdout_episodes": 17,
               "frame_alignment": "observation frame t; action from frame t+1",
               "summary": summary, "rows": rows}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
