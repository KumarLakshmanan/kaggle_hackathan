"""Count a strict upper bound on same-turn adjacent SELL swap opportunities.

Reads the previously downloaded 24 public replays. It deliberately does not
infer fill, funding, or post-unit stock; those need a separate causal test.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import main as incumbent  # noqa: E402; use the submitted policy's unit-action projector

PREMIUM = frozenset(("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"))
OUR_NAME = "Lakshmanan R"


def classify_preceding(order: object) -> str | None:
    if not isinstance(order, list) or not order:
        return None
    if order[0] in ("BUY_SEED", "HIRE"):
        return str(order[0])
    if order[0] == "SELL":
        return "SELL"  # Stock/fill checks are deliberately deferred.
    return None


def scan_one(path: Path, outcome: str, margin: float) -> dict:
    with path.open(encoding="utf-8") as stream:
        replay = json.load(stream)
    ours = replay["info"]["TeamNames"].index(OUR_NAME)
    events: list[dict] = []
    for index in range(1, len(replay["steps"])):
        action = replay["steps"][index][ours].get("action") or {}
        observation = replay["steps"][index - 1][ours].get("observation") or {}
        # Kaggle's downloaded replay omits the explicit ``step`` key from
        # seat-1 observations; the 720 indexed rows still retain every turn.
        # Never filter a seat on that optional field.
        if "day" not in observation or "hour" not in observation:
            continue
        market = action.get("market") or []
        if len(market) < 2:
            continue
        if any(
            isinstance(order, list)
            and len(order) > 1
            and order[0] in ("BUY_PRODUCT", "SELL")
            and order[1] in ("WHEAT", "FERTILIZER")
            for order in market
        ):
            continue
        prices = (observation.get("market") or {}).get("prices") or {}
        projected = incumbent.projected_shed(action, incumbent.FarmView(observation))
        for slot in range(1, len(market)):
            later = market[slot]
            before = market[slot - 1]
            kind = classify_preceding(before)
            if kind is None or not isinstance(later, list) or len(later) < 3:
                continue
            if later[0] != "SELL" or later[1] not in PREMIUM:
                continue
            product = later[1]
            if sum(
                isinstance(order, list)
                and len(order) >= 3
                and order[0] == "SELL"
                and order[1] == product
                for order in market
            ) != 1:
                continue
            try:
                if int(later[2]) <= 0 or float(prices.get(product, 0)) <= 1:
                    continue
            except (TypeError, ValueError):
                continue
            inert_before = False
            if kind == "SELL" and len(before) >= 3:
                prior = market[: slot - 1]
                # A prior product purchase could supply this stock; do not label
                # the preceding sale inert when market effects are uncertain.
                if not any(
                    isinstance(order, list)
                    and len(order) >= 3
                    and order[0] == "BUY_PRODUCT"
                    and order[1] == before[1]
                    for order in prior
                ):
                    prior_sold = sum(
                        max(0, int(order[2]))
                        for order in prior
                        if isinstance(order, list)
                        and len(order) >= 3
                        and order[0] == "SELL"
                        and order[1] == before[1]
                    )
                    inert_before = int(projected.get(before[1], 0)) <= prior_sold
            events.append(
                {
                    "step": index - 1,
                    "slot": slot,
                    "before_kind": kind,
                    "product": product,
                    "quantity_requested": int(later[2]),
                    "quoted_price": float(prices[product]),
                    "stock_before_units": int((observation.get("private") or {}).get("shed", {}).get(product, 0)),
                    "before_sell_provably_inert": inert_before,
                }
            )
    return {
        "episode_id": replay["info"]["EpisodeId"],
        "outcome": outcome,
        "margin": margin,
        "events": events,
    }


def main() -> None:
    audit = json.loads((HERE / "audit_latest_24.json").read_text(encoding="utf-8"))
    rows = [
        scan_one(
            HERE / f"episode-{entry['episode_id']}-replay.json",
            entry["outcome"],
            entry["margin"],
        )
        for entry in audit["episodes"]
    ]
    counts = Counter(event["before_kind"] for row in rows for event in row["events"])
    inert = [
        (row, event)
        for row in rows
        for event in row["events"]
        if event["before_kind"] in ("BUY_SEED", "HIRE")
        or event["before_sell_provably_inert"]
    ]
    exposed = [row for row in rows if row["events"]]
    close_losses = [row for row in exposed if row["outcome"] == "loss" and row["margin"] > -1100]
    print("Adjacent syntactic pairs by earlier order:", dict(counts))
    print("Strictly eligible independent/inert earlier orders:", len(inert))
    print("Strictly eligible episodes:", len({row["episode_id"] for row, _ in inert}))
    print("Strictly eligible close losses:", len({row["episode_id"] for row, _ in inert if row["outcome"] == "loss" and row["margin"] > -1100}))
    print("Exposed episodes:", len(exposed), "/", len(rows))
    print("Exposed close-loss episodes:", len(close_losses), "/ 8")
    print("Exposed loss episodes:", sum(row["outcome"] == "loss" for row in exposed), "/ 11")
    for row in rows:
        if row["events"]:
            by_kind = Counter(event["before_kind"] for event in row["events"])
            print(row["episode_id"], row["outcome"], len(row["events"]), dict(by_kind), row["events"][:2])


if __name__ == "__main__":
    main()
