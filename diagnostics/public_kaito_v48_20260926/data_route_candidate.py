"""Data-only v48 route screen. No downloaded Python source is imported or run."""

from copy import deepcopy
import json
from pathlib import Path


ROUTES = json.loads(Path(__file__).with_name("routes_untrusted.json").read_text(encoding="utf-8"))
assert set(ROUTES) == {"default", "yarn_fast", "farm_fast", "yarn_second", "yarn_third", "bakery_capital"}
assert all(len(actions) == 719 for actions in ROUTES.values())
selected = {0: "default", 1: "default"}
last_step = {0: -1, 1: -1}
telemetry = {"calls": 0, "switches": 0}


def _asset_counts(farm):
    counts = {"COW": 0, "SHEEP": 0, "MELON": 0, "GOOSE": 0}
    for row in farm.get("tiles", []) or []:
        for tile in row:
            if isinstance(tile, dict):
                for field in ("crop", "animal"):
                    value = tile.get(field)
                    if value in counts:
                        counts[value] += 1
    return counts


def _route_event(obs, seat, step):
    shops = list((obs.get("town", {}) or {}).get("unlocked_shops", []) or [])
    if shops and shops[0] == "YARN_STORE" and step >= 88:
        return "yarn_fast"
    if shops and shops[0] == "FARMERS_MARKET" and step >= 120:
        return "farm_fast"
    if len(shops) >= 2 and shops[0] not in {"YARN_STORE", "FARMERS_MARKET"} and shops[1] == "YARN_STORE" and step >= 153:
        return "yarn_second"
    if len(shops) >= 3 and shops[2] == "YARN_STORE" and tuple(shops[:2]) in {("BRUNCH_SPOT", "PET_CAFE"), ("PET_CAFE", "FARMERS_MARKET")} and step >= 216:
        return "yarn_third"
    if step == 160 and len(shops) >= 2 and shops[:2] == ["BAKERY", "PIZZA_SHOP"]:
        farms = list(obs.get("farms", []) or [])
        if len(farms) >= 2:
            counts = _asset_counts(farms[1 - seat])
            if counts["COW"] >= 3 and counts["SHEEP"] >= 2 and counts["MELON"] >= 10 and counts["GOOSE"] == 0:
                return "bakery_capital"
    return None


def agent(obs, configuration=None):
    seat = int(obs.get("player", 0) or 0)
    step = int(obs.get("step", 0) or 0)
    if step == 0 or step < last_step[seat]:
        selected[seat] = "default"
    last_step[seat] = step
    if selected[seat] == "default":
        event = _route_event(obs, seat, step)
        if event:
            selected[seat] = event
            telemetry["switches"] += 1
    action = deepcopy(ROUTES[selected[seat]][min(max(step, 0), 718)])
    farms = list(obs.get("farms", []) or [])
    n_hands = len((farms[seat] if seat < len(farms) else {}).get("hands", []) or [])
    hands = action.get("hands") or []
    action["hands"] = hands[:n_hands] + [["PASS"] for _ in range(max(0, n_hands - len(hands)))]
    telemetry["calls"] += 1
    return action
