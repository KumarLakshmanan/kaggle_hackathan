"""Build V31 using only validated public shop-prefix observations."""

from __future__ import annotations

import gzip
import hashlib
import json
import pprint
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _route(name: str) -> list[dict]:
    path = ROOT / "best_replay" / "routes" / name
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)["actions"]


def _replace_table(text: str, name: str, next_name: str, actions: list[dict]) -> str:
    start = text.index(f"{name} =")
    end = text.index(f"\n{next_name} =", start)
    rendered = f"{name} = {pprint.pformat(actions, width=120, compact=True, sort_dicts=False)}"
    return text[:start] + rendered + text[end:]


def _digest(actions: list[dict]) -> str:
    payload = json.dumps(actions, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def build(destination: Path) -> None:
    primary = _route("episode-90622597-seat1.json.gz")
    thunder = _route("episode-90630506-seat0.json.gz")
    aastik_counter = _route("episode-90619447-seat1.json.gz")
    seb_202_counter = _route("episode-90616293-seat0.json.gz")
    seb_210_counter = _route("episode-90659792-seat0.json.gz")

    text = (ROOT / "main_v28_wufang_seb_detect.py").read_text(encoding="utf-8")
    text = _replace_table(text, "_PRIMARY_ACTIONS", "_ALTERNATE_ACTIONS", primary)
    extras = (
        "\n# Counter books selected from public observations at turn 144.\n"
        f"_THUNDER_COUNTER_ACTIONS = {pprint.pformat(thunder, width=120, compact=True, sort_dicts=False)}\n\n"
        f"_AASTIK_COUNTER_ACTIONS = {pprint.pformat(aastik_counter, width=120, compact=True, sort_dicts=False)}\n"
        f"_SEB_202_COUNTER_ACTIONS = {pprint.pformat(seb_202_counter, width=120, compact=True, sort_dicts=False)}\n\n"
        f"_SEB_210_COUNTER_ACTIONS = {pprint.pformat(seb_210_counter, width=120, compact=True, sort_dicts=False)}\n"
    )
    text = text.replace("\n_ACTIONS = _PRIMARY_ACTIONS", extras + "\n_ACTIONS = _PRIMARY_ACTIONS", 1)
    text = text.replace(
        "_ROUTE_ACTION_SHA256 = '4a0c36676bc16852de643df803a7fd4406bee6333022634ddd6ff8d50df54e01'",
        f"_ROUTE_ACTION_SHA256 = '{_digest(primary)}'",
    )

    selector_start = text.index("_PORTFOLIO_MODE =")
    selector_end = text.index("\ndef _counter_order", selector_start)
    selector = '''_PORTFOLIO_MODE = {0: "primary", 1: "primary"}
_OBSERVABLE_BOOK = {0: "fallback", 1: "fallback"}
_OPPONENT_PASTURE = {0: False, 1: False}

# These are live shop pairs observed under the shared opening, not hidden
# seeds or replay IDs. Unknown pairs retain the broadly robust Wufang book.
_PUBLIC_SHOP_COUNTERS = {
    ("FARMERS_MARKET", "YARN_STORE"): "thunder",
    ("PET_CAFE", "BAKERY"): "thunder",
    ("FARMERS_MARKET", "SMOOTHIE_SHOP"): "thunder",
    ("BRUNCH_SPOT", "BAKERY"): "aastik",
}
_PUBLIC_SEB_SHOP_COUNTERS = {
    ("BRUNCH_SPOT", "YARN_STORE"): "seb202",
    ("BRUNCH_SPOT", "ICE_CREAM_SHOP"): "seb210",
}


def _activate_action_book(obs, step):
    """Select compatible books from public opponent and town state."""
    global _ACTIONS
    seat = 1 if int(_get(obs, "player", 0) or 0) == 1 else 0
    if step == 0:
        _PORTFOLIO_MODE[seat] = "primary"
        _OBSERVABLE_BOOK[seat] = "fallback"
        _OPPONENT_PASTURE[seat] = False
    elif step == 1:
        farms = list(_get(obs, "farms", []) or [])
        opponent = farms[1 - seat] if len(farms) >= 2 else {}
        opponent_money = float(_get(opponent, "money", 10**9) or 0)
        opponent_hands = len(_get(opponent, "hands", []) or [])
        opponent_center = _tile_at(opponent, [4, 4])
        pasture_opening = (
            opponent_hands >= 6
            and isinstance(opponent_center, dict)
            and opponent_center.get("kind") == "PASTURE"
        )
        _OPPONENT_PASTURE[seat] = pasture_opening
        _PORTFOLIO_MODE[seat] = (
            "alternate"
            if 18.0 <= opponent_money <= 32.0 or pasture_opening
            else "primary"
        )
    mode = _PORTFOLIO_MODE[seat]
    if mode == "alternate" and step >= 144 and _OBSERVABLE_BOOK[seat] == "fallback":
        town = _get(obs, "town", {}) or {}
        shops = tuple(_get(town, "unlocked_shops", []) or [])
        counter_map = (
            _PUBLIC_SEB_SHOP_COUNTERS
            if _OPPONENT_PASTURE[seat]
            else _PUBLIC_SHOP_COUNTERS
        )
        _OBSERVABLE_BOOK[seat] = counter_map.get(shops[:2], "wufang")
    selected = _OBSERVABLE_BOOK[seat]
    if mode == "primary":
        _ACTIONS = _PRIMARY_ACTIONS
    elif selected == "thunder":
        _ACTIONS = _THUNDER_COUNTER_ACTIONS
    elif selected == "aastik":
        _ACTIONS = _AASTIK_COUNTER_ACTIONS
    elif selected == "seb202":
        _ACTIONS = _SEB_202_COUNTER_ACTIONS
    elif selected == "seb210":
        _ACTIONS = _SEB_210_COUNTER_ACTIONS
    else:
        _ACTIONS = _ALTERNATE_ACTIONS
    return mode
'''
    text = text[:selector_start] + selector + text[selector_end:]

    counter_start = text.index("def _counter_order(action, step):")
    counter_end = text.index("\ndef _legal_unit_actions", counter_start)
    text = (
        text[:counter_start]
        + "def _counter_order(action, step):\n    return action\n\n"
        + text[counter_end + 1 :]
    )
    delay = '''def _remaining_seb_market_delay(obs, action, step):
    """Hold strawberries through the remaining Seb replay's late glut."""
    seat = 1 if int(_get(obs, "player", 0) or 0) == 1 else 0
    town = _get(obs, "town", {}) or {}
    shops = tuple(_get(town, "unlocked_shops", []) or [])
    remaining_seb = (
        _OPPONENT_PASTURE.get(seat, False)
        and shops[:2] == ("FARMERS_MARKET", "BRUNCH_SPOT")
    )
    if remaining_seb and 648 <= step < 718:
        action["market"] = [
            order
            for order in action.get("market", []) or []
            if not (
                len(order) >= 3
                and order[0] == "SELL"
                and order[1] == "STRAWBERRY"
            )
        ]
    return action


'''
    text = text.replace("def agent(obs):", delay + "def agent(obs):", 1)
    text = text.replace(
        "        action = _safe_market(obs, action)\n        if step == len(_ACTIONS) - 1:",
        "        action = _safe_market(obs, action)\n"
        "        action = _remaining_seb_market_delay(obs, action, step)\n"
        "        if step == len(_ACTIONS) - 1:",
        1,
    )
    text = text.replace(
        "V17 transparent route, recovery, and all-product market search",
        "V32 transparent observable counter portfolio",
    )
    destination.write_text(text, encoding="utf-8", newline="\n")
    print(destination.resolve())
    print(f"bytes={destination.stat().st_size}")


if __name__ == "__main__":
    build(ROOT / "main_v32_observable_portfolio.py")
