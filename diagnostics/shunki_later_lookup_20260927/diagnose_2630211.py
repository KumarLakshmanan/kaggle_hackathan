"""Read-only exact event ledger for the largest fresh development loss."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from trace_paired_game_events import run  # noqa: E402

SEED = 2630211
MAIN = ROOT / "main.py"
CANDIDATE = ROOT / "exp_shunki_later_lookup_20260927.py"


def summarize(data: dict) -> dict:
    items = [Counter(), Counter()]
    sales = [Counter(), Counter()]
    units = [Counter(), Counter()]
    atomics = [Counter(), Counter()]
    for event in data["events"]:
        if not event.get("success") or event.get("player") not in (0, 1):
            continue
        player = int(event["player"])
        if event["phase"] == "market_unit":
            item = event["item"]
            amount = float(event["cash_delta"])
            items[player][item] += amount
            if event["operation"] == "SELL":
                sales[player][item] += amount
                units[player][item] += 1
        elif event["phase"] == "market_atomic":
            atomics[player][event["operation"]] += (
                float(event["cash_after"]) - float(event["cash_before"]))
    daily = []
    for day in range(30):
        row = data["turns"][24 * (day + 1) - 1]
        daily.append([float(x["cash"]) for x in row["players_after"]])
    shops = []
    for step in (72, 144, 216, 288, 360, 432, 504, 576, 648):
        observation = data["traces"][0][step]["observation"]
        shops.append({"step": step,
                      "shops": observation["town"]["unlocked_shops"]})
    return {"cash": [data["candidate_reward"], data["opponent_reward"]],
            "items_net": [dict(x) for x in items],
            "sale_cash": [dict(x) for x in sales],
            "sale_units": [dict(x) for x in units],
            "atomic": [dict(x) for x in atomics],
            "daily_cash": daily, "shops": shops}


def main() -> None:
    control = summarize(run(str(MAIN), str(MAIN), SEED, 0))
    candidate = summarize(run(str(CANDIDATE), str(MAIN), SEED, 0))
    assert control["cash"] == [96306.0, 96306.0] or control["cash"][0] == control["cash"][1]
    assert candidate["cash"] == [104535.0, 112454.0]
    item_delta = []
    for player in (0, 1):
        keys = set(control["items_net"][player]) | set(candidate["items_net"][player])
        item_delta.append({item: candidate["items_net"][player].get(item, 0)
                            - control["items_net"][player].get(item, 0)
                           for item in sorted(keys)})
    result = {"seed": SEED, "control": control, "candidate": candidate,
              "net_item_delta_by_player": item_delta,
              "daily_cash_delta_by_player": [
                  [candidate["daily_cash"][day][player]
                   - control["daily_cash"][day][player] for player in (0, 1)]
                  for day in range(30)]}
    (HERE / "loss_2630211_ledger.json").write_text(
        json.dumps(result, indent=2), encoding="utf8")
    print("shops", candidate["shops"])
    print("cash", control["cash"], candidate["cash"])
    print("item delta by player", item_delta)
    print("atomic delta by player", [
        {k: candidate["atomic"][i].get(k, 0) - control["atomic"][i].get(k, 0)
         for k in set(control["atomic"][i]) | set(candidate["atomic"][i])}
        for i in (0, 1)])
    print("daily cash delta", result["daily_cash_delta_by_player"])


if __name__ == "__main__":
    main()
