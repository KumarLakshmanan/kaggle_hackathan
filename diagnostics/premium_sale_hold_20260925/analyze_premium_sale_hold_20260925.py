"""Summarize exact native trace capacity and observable timing opportunities."""

from __future__ import annotations

import gzip
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from kaggle_environments.envs.kaggriculture import kaggriculture as game


STUDY = Path(__file__).resolve().parent
COHORT = (112933589, 112941285, 112935831, 112939403)
PREMIUM = ("STRAWBERRY", "MELON", "MILK", "WOOL")
CAPACITY = int(game.specification["configuration"]["shedCapacity"]["default"])
SHOP_INTERVAL = 4
CENTER_INTERVAL = 24


def _load(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def _demand(observation: dict[str, Any], item: str, step: int) -> tuple[int, int]:
    shops = list((observation.get("town") or {}).get("unlocked_shops") or [])
    shop_units = 0
    if step % SHOP_INTERVAL == 0:
        for name in shops:
            products = game.SHOPS.get(name, ())
            if item in products:
                shop_units += 2 if len(products) == 1 else 1
    center_units = int(
        step % CENTER_INTERVAL == 0
        and item in getattr(game, "TOWN_CENTER_PRODUCTS", ())
    )
    return shop_units, center_units


def _series(payload: dict[str, Any], item: str, seat: int) -> dict[str, Any]:
    own_trace = payload["traces"][seat]
    rival_trace = payload["traces"][1 - seat]
    own_sales: dict[int, list[float]] = defaultdict(list)
    rival_sales: dict[int, list[float]] = defaultdict(list)
    for event in payload["events"]:
        if (
            event.get("phase") != "market_unit"
            or not event.get("success")
            or event.get("operation") != "SELL"
            or event.get("item") != item
        ):
            continue
        target = own_sales if int(event.get("player", -1)) == seat else rival_sales
        target[int(event["step"])].append(float(event.get("cash_delta", 0) or 0))

    aggregate = {
        "order_steps": 0,
        "order_units": 0,
        "sold_units": 0,
        "receipts": 0.0,
        "low_shop_order_steps": 0,
        "low_shop_order_units": 0,
        "low_shop_sold_units": 0,
        "scheduled_pulse_steps": 0,
        "scheduled_pulse_units": 0,
        "scheduled_pulse_sold": 0,
        "scheduled_pulse_with_next_sale": 0,
        "next_quote_up_steps": 0,
        "next_quote_up_units": 0,
        "next_quote_up_baseline_cash_proxy": 0.0,
        "max_safe_hold_headroom": 0,
        "max_shed": 0,
        "occupied_shed_observations": 0,
        "observations": 0,
        "prices": [],
        "events": [],
    }
    for index, record in enumerate(own_trace):
        step = int(record.get("step", -1))
        observation = record.get("observation") or {}
        action = record.get("action") or {}
        shed = (observation.get("private") or {}).get("shed") or {}
        shed_total = sum(max(0, int(v or 0)) for v in shed.values())
        carry = sum(
            max(0, int(v or 0))
            for inventory in ((observation.get("private") or {}).get("inventories") or [])
            for v in (inventory or {}).values()
        )
        market = observation.get("market") or {}
        prices = market.get("prices") or {}
        market_inventory = market.get("inventory") or {}
        price = int(prices.get(item, 0) or 0)
        aggregate["observations"] += 1
        aggregate["max_shed"] = max(aggregate["max_shed"], shed_total)
        aggregate["occupied_shed_observations"] += int(shed_total >= CAPACITY)
        if price > 0:
            aggregate["prices"].append(price)

        order_quantity = sum(
            max(0, int(order[2]))
            for order in action.get("market", []) or []
            if isinstance(order, (list, tuple))
            and len(order) >= 3
            and order[0] == "SELL"
            and order[1] == item
        )
        if order_quantity <= 0:
            continue
        actual_prices = own_sales.get(step, [])
        sold_now = len(actual_prices)
        receipts_now = sum(actual_prices)
        shop_demand, center_demand = _demand(observation, item, step)
        known_demand = shop_demand + center_demand
        shop_count = sum(
            item in game.SHOPS.get(name, ())
            for name in ((observation.get("town") or {}).get("unlocked_shops") or [])
        )
        aggregate["order_steps"] += 1
        aggregate["order_units"] += order_quantity
        aggregate["sold_units"] += sold_now
        aggregate["receipts"] += receipts_now
        if shop_count == 0:
            aggregate["low_shop_order_steps"] += 1
            aggregate["low_shop_order_units"] += order_quantity
            aggregate["low_shop_sold_units"] += sold_now
        if known_demand:
            aggregate["scheduled_pulse_steps"] += 1
            aggregate["scheduled_pulse_units"] += order_quantity
            aggregate["scheduled_pulse_sold"] += sold_now

        next_quote = None
        next_sale_prices = own_sales.get(step + 1, [])
        if index + 1 < len(own_trace):
            next_observation = own_trace[index + 1].get("observation") or {}
            next_quote = int(
                (((next_observation.get("market") or {}).get("prices") or {}).get(item, 0)) or 0
            )
        if sold_now and next_sale_prices:
            aggregate["scheduled_pulse_with_next_sale"] += int(bool(known_demand))
            current_average = receipts_now / sold_now
            next_average = sum(next_sale_prices) / len(next_sale_prices)
            movable = min(sold_now, len(next_sale_prices))
            if next_average > current_average:
                aggregate["next_quote_up_steps"] += 1
                aggregate["next_quote_up_units"] += movable
                aggregate["next_quote_up_baseline_cash_proxy"] += movable * (next_average - current_average)

        # Current-turn conservative headroom: one may retain only the amount
        # left after the baseline's observed successful sales and current carry.
        headroom = max(0, CAPACITY - (shed_total - sold_now) - carry)
        aggregate["max_safe_hold_headroom"] = max(aggregate["max_safe_hold_headroom"], headroom)
        aggregate["events"].append(
            {
                "step": step,
                "price": price,
                "market_inventory": int(market_inventory.get(item, 0) or 0),
                "visible_consuming_shops": int(shop_count),
                "scheduled_shop_demand_units": shop_demand,
                "scheduled_town_center_units": center_demand,
                "known_demand_units_after_market": known_demand,
                "sell_order_units": order_quantity,
                "sold_units": sold_now,
                "realized_receipts": receipts_now,
                "shed_total": shed_total,
                "shed_free": max(0, CAPACITY - shed_total),
                "carried_units": carry,
                "current_capacity_headroom_after_baseline_sales": headroom,
                "next_observed_price": next_quote,
                "next_same_product_sale_units": len(next_sale_prices),
                "next_same_product_rival_sale_units": len(rival_sales.get(step + 1, [])),
                "next_baseline_average_receipt": (
                    sum(next_sale_prices) / len(next_sale_prices) if next_sale_prices else None
                ),
            }
        )

    aggregate["price_min"] = min(aggregate["prices"]) if aggregate["prices"] else None
    aggregate["price_median"] = (
        sorted(aggregate["prices"])[len(aggregate["prices"]) // 2]
        if aggregate["prices"] else None
    )
    aggregate["price_max"] = max(aggregate["prices"]) if aggregate["prices"] else None
    del aggregate["prices"]
    return aggregate


def main() -> None:
    rows = []
    for episode_id in COHORT:
        for seat in (0, 1):
            path = STUDY / f"baseline_{episode_id}_seat{seat}.json.gz"
            payload = _load(path)
            row = {
                "team": payload["team"],
                "episode_id": episode_id,
                "stratum": payload["stratum"],
                "seat": seat,
                "own_cash": payload["candidate_reward"],
                "rival_cash": payload["opponent_reward"],
                "shop_sequence": list(payload["study_metrics"]["shop_sequence"]),
                "overflow_events": [
                    event for event in payload["overflow_events"] if int(event["player"]) == seat
                ],
                "premium": {item: _series(payload, item, seat) for item in PREMIUM},
            }
            rows.append(row)
            strawberry = row["premium"]["STRAWBERRY"]
            print(
                f"{row['team']} e{episode_id} seat={seat} cash={row['own_cash']:.0f}/"
                f"{row['rival_cash']:.0f} shops={'/'.join(row['shop_sequence'])} "
                f"straw={strawberry['sold_units']}u ${strawberry['receipts']:.0f} "
                f"orders={strawberry['order_steps']} no-shop={strawberry['low_shop_sold_units']}u "
                f"pulse={strawberry['scheduled_pulse_sold']}u "
                f"next-up=${strawberry['next_quote_up_baseline_cash_proxy']:.0f} "
                f"shed={strawberry['max_shed']} overflow="
                f"{sum(x['units'] for x in row['overflow_events'])}",
                flush=True,
            )
    output = {
        "engine_version": "1.32.7",
        "purpose": "Baseline trace opportunity/capacity screen; all events are observational, not causal treatment effects.",
        "premium_products": list(PREMIUM),
        "shed_capacity": CAPACITY,
        "rows": rows,
    }
    target = STUDY / "native_opportunity_capacity.json"
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite {target}")
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote={target}")


if __name__ == "__main__":
    main()
