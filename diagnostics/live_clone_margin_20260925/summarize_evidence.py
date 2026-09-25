"""Read-only per-item aggregation of replay-reconciled live sale receipts."""

from collections import defaultdict
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
evidence = json.loads((HERE / "live_clone_margin_evidence.json").read_text(encoding="utf-8"))
carrot_unit_shortfalls = 0
negative_modeled_sale_cash = 0

for episode in evidence["episodes"]:
    if episode["outcome"] != "loss":
        continue
    ours = int(episode["our_seat"])
    rival = 1 - ours
    items = defaultdict(lambda: {0: [0, 0], 1: [0, 0]})
    for event in episode["model_sale_cash_by_day_item"]:
        row = items[event["item"]][int(event["seat"])]
        row[0] += int(event["filled"])
        row[1] += int(event["receipt"])
    item_differences = sorted(
        (
            (item, data[ours][0], data[rival][0],
             data[ours][1] - data[rival][1], data[ours][1], data[rival][1])
            for item, data in items.items()
        ),
        key=lambda row: row[3],
    )
    carrot_unit_shortfalls += int(items["CARROT"][ours][0] < items["CARROT"][rival][0])
    negative_modeled_sale_cash += int(sum(row[3] for row in item_differences) < 0)
    first_negative = next(
        (day for day in episode["day_cash"] if day["margin"] < 0), None
    )
    print(
        f"episode={episode['episode_id']} margin={episode['margin']:+.0f} "
        f"seat={ours} first_negative_day={None if first_negative is None else first_negative['day']}"
    )
    print(
        "  reconciled sale cash differential=",
        sum(row[3] for row in item_differences),
        "versus terminal margin=", episode["margin"],
    )
    for item, own_units, rival_units, diff, own_cash, rival_cash in item_differences:
        if own_units or rival_units:
            print(
                f"  {item:11s} units={own_units:4d}/{rival_units:4d} "
                f"cash={own_cash:6d}/{rival_cash:6d} diff={diff:+6d}"
            )

print("LOSS SUMMARY: carrot unit shortfalls", carrot_unit_shortfalls,
      "of 11; negative gross modeled sale cash", negative_modeled_sale_cash,
      "of 11 (unadjusted for product purchases)")
