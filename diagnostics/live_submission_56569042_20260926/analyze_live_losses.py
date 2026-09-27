"""Read-only farm, market, and cash summary of corrected-upload public losses."""

from collections import Counter
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT = max(HERE.glob("audit_latest_*.json"),
            key=lambda path: int(path.stem.rsplit("_", 1)[1]))
OUT = HERE / f"live_losses_{AUDIT.stem.rsplit('_', 1)[1]}_diagnosis.json"
DAYS = (0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 29)


def counts(farm):
    return dict(Counter(
        tile.get("crop") or tile.get("animal") or tile.get("kind")
        for row in farm["tiles"] for tile in row if isinstance(tile, dict)
    ))


def summarize(row):
    episode_id = row["episode_id"]
    replay = json.loads((HERE / f"episode-{episode_id}-replay.json").read_text(encoding="utf8"))
    own, rival = row["our_seat"], 1 - row["our_seat"]
    days = []
    for day in DAYS:
        turn = replay["steps"][day * 24]
        obs = turn[own]["observation"]
        farms = obs["farms"]
        days.append({
            "day": day,
            "shops": obs["town"]["unlocked_shops"],
            "own_cash": farms[own]["money"],
            "rival_cash": farms[rival]["money"],
            "own_tiles": counts(farms[own]),
            "rival_tiles": counts(farms[rival]),
            "own_shed": {k: v for k, v in turn[own]["observation"]["private"]["shed"].items() if v},
            "rival_shed": {k: v for k, v in turn[rival]["observation"]["private"]["shed"].items() if v},
        })
    market_match_by_day = []
    physical_match_by_day = []
    sales = [Counter(), Counter()]
    buys = [Counter(), Counter()]
    first_market_divergence = None
    for day in range(30):
        market_matches = physical_matches = 0
        for hour, turn in enumerate(replay["steps"][day * 24:(day + 1) * 24]):
            actions = [turn[i].get("action") or {} for i in (0, 1)]
            obs = turn[own]["observation"]
            farms = obs["farms"]
            market_equal = (actions[0].get("market") or []) == (actions[1].get("market") or [])
            market_matches += market_equal
            physical_matches += (farms[0]["tiles"] == farms[1]["tiles"]
                                 and farms[0]["farmer"] == farms[1]["farmer"]
                                 and farms[0]["hands"] == farms[1]["hands"])
            if not market_equal and first_market_divergence is None:
                first_market_divergence = day * 24 + hour
            for seat in (0, 1):
                for order in actions[seat].get("market") or []:
                    if len(order) >= 3 and order[0] == "SELL":
                        sales[seat][order[1]] += order[2]
                    elif len(order) >= 3 and order[0] == "BUY_PRODUCT":
                        buys[seat][order[1]] += order[2]
        market_match_by_day.append(market_matches)
        physical_match_by_day.append(physical_matches)
    terminal = replay["steps"][-1]
    return {
        "episode_id": episode_id, "opponent": row["opponent"], "margin": row["margin"],
        "our_seat": own, "seed": row["seed"], "first_market_divergence": first_market_divergence,
        "market_match_by_day": market_match_by_day,
        "physical_match_by_day": physical_match_by_day,
        "own_requested_sales": dict(sales[own]), "rival_requested_sales": dict(sales[rival]),
        "own_requested_product_buys": dict(buys[own]),
        "rival_requested_product_buys": dict(buys[rival]),
        "days": days,
        "terminal_own_private": terminal[own]["observation"]["private"],
        "terminal_rival_private": terminal[rival]["observation"]["private"],
    }


def main():
    audit = json.loads(AUDIT.read_text(encoding="utf8"))
    losses = [summarize(row) for row in audit["episodes"] if row["outcome"] == "loss"]
    OUT.write_text(json.dumps(losses, indent=2, ensure_ascii=False), encoding="utf8")
    for row in losses:
        print(row["episode_id"], row["opponent"], row["margin"],
              "first market divergence", row["first_market_divergence"],
              "market matches", sum(row["market_match_by_day"]),
              "physical matches", sum(row["physical_match_by_day"]))
        for day in row["days"]:
            if day["day"] in (6, 12, 18, 24, 29):
                print(" ", day["day"], day["shops"],
                      "cash", day["own_cash"], day["rival_cash"],
                      "tiles", day["own_tiles"], day["rival_tiles"])
        print("  sales", row["own_requested_sales"], row["rival_requested_sales"])
    print(OUT)


if __name__ == "__main__":
    main()
