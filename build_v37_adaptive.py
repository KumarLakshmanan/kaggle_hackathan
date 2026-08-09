#!/usr/bin/env python3
"""Build the V37 public-state continuation selector.

V36 remains the opening and recovery policy.  At turn 144 the agent may switch
to one screened continuation, but only for a public signature observed in the
expanded top-10 loss panel.  No team name, replay id, or private state is used
by the generated agent.
"""

from __future__ import annotations

import argparse
import gzip
import json
import pprint
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TAO_ROUTE = (
    ROOT
    / "best_replay"
    / "top10_recent20"
    / "routes"
    / "episode-91038777-seat0.json.gz"
)

# Public signatures for which the Tao continuation was strictly better on all
# matching V36 loss-panel examples, with a minimum 1,000-point improvement.
TAO_KEYS = {
    ("BAKERY", "BRUNCH_SPOT", 11),
    ("BAKERY", "BRUNCH_SPOT", 1708),
    ("BAKERY", "ICE_CREAM_SHOP", 1708),
    ("BAKERY", "PET_CAFE", 1708),
    ("BAKERY", "PIZZA_SHOP", 1708),
    ("BAKERY", "SMOOTHIE_SHOP", 11),
    ("BAKERY", "YARN_STORE", 1708),
    ("BRUNCH_SPOT", "ICE_CREAM_SHOP", 11),
    ("FARMERS_MARKET", "BRUNCH_SPOT", 1708),
    ("FARMERS_MARKET", "ICE_CREAM_SHOP", 1708),
    ("FARMERS_MARKET", "PET_CAFE", 1708),
    ("FARMERS_MARKET", "PIZZA_SHOP", 1708),
    ("ICE_CREAM_SHOP", "BAKERY", 11),
    ("ICE_CREAM_SHOP", "BAKERY", 1708),
    ("ICE_CREAM_SHOP", "SMOOTHIE_SHOP", 1708),
    ("ICE_CREAM_SHOP", "YARN_STORE", 11),
    # This signature is assigned to the Lester continuation below.
    ("PET_CAFE", "BRUNCH_SPOT", 30),
    ("PET_CAFE", "FARMERS_MARKET", 1688),
    ("PET_CAFE", "ICE_CREAM_SHOP", 1688),
    ("PIZZA_SHOP", "BAKERY", 11),
    ("PIZZA_SHOP", "BAKERY", 1708),
    ("PIZZA_SHOP", "BRUNCH_SPOT", 1708),
    ("PIZZA_SHOP", "FARMERS_MARKET", 11),
    ("PIZZA_SHOP", "SMOOTHIE_SHOP", 1708),
    ("PIZZA_SHOP", "YARN_STORE", 11),
    ("SMOOTHIE_SHOP", "BAKERY", 30),
    ("SMOOTHIE_SHOP", "BAKERY", 1688),
    ("SMOOTHIE_SHOP", "BRUNCH_SPOT", 30),
    ("SMOOTHIE_SHOP", "FARMERS_MARKET", 30),
    ("SMOOTHIE_SHOP", "ICE_CREAM_SHOP", 1688),
    ("SMOOTHIE_SHOP", "PET_CAFE", 1688),
    ("SMOOTHIE_SHOP", "PIZZA_SHOP", 1688),
    ("SMOOTHIE_SHOP", "YARN_STORE", 1688),
    ("YARN_STORE", "BAKERY", 30),
    ("YARN_STORE", "BAKERY", 1688),
    ("YARN_STORE", "BRUNCH_SPOT", 30),
    ("YARN_STORE", "BRUNCH_SPOT", 1688),
    ("YARN_STORE", "FARMERS_MARKET", 1688),
    ("YARN_STORE", "ICE_CREAM_SHOP", 1688),
    ("YARN_STORE", "PET_CAFE", 1688),
    ("YARN_STORE", "PIZZA_SHOP", 30),
    ("YARN_STORE", "PIZZA_SHOP", 1688),
    ("YARN_STORE", "SMOOTHIE_SHOP", 1688),
}

SYED_KEYS = {
    ("BAKERY", "BRUNCH_SPOT", 11),
    ("BAKERY", "SMOOTHIE_SHOP", 1708),
    ("PET_CAFE", "BAKERY", 1688),
    ("PIZZA_SHOP", "BAKERY", 11),
    ("YARN_STORE", "PIZZA_SHOP", 1688),
}

LESTER_KEYS = {
    ("ICE_CREAM_SHOP", "YARN_STORE", 1708),
    ("YARN_STORE", "BRUNCH_SPOT", 30),
}


def build(destination: Path) -> None:
    source = ROOT / "main.py"
    text = source.read_text(encoding="utf-8")
    with gzip.open(TAO_ROUTE, "rt", encoding="utf-8") as handle:
        tao_actions = json.load(handle)["actions"]
    with gzip.open(
        ROOT / "best_replay" / "top10_recent20" / "routes" / "episode-91030311-seat0.json.gz",
        "rt",
        encoding="utf-8",
    ) as handle:
        syed_actions = json.load(handle)["actions"]
    with gzip.open(
        ROOT / "best_replay" / "top10_recent20" / "routes" / "episode-91039633-seat0.json.gz",
        "rt",
        encoding="utf-8",
    ) as handle:
        lester_actions = json.load(handle)["actions"]
    tao_literal = pprint.pformat(tao_actions, width=120, compact=True, sort_dicts=False)
    syed_literal = pprint.pformat(syed_actions, width=120, compact=True, sort_dicts=False)
    lester_literal = pprint.pformat(lester_actions, width=120, compact=True, sort_dicts=False)
    key_literal = pprint.pformat(sorted(TAO_KEYS), width=120, compact=True, sort_dicts=False)
    syed_key_literal = pprint.pformat(sorted(SYED_KEYS), width=120, compact=True, sort_dicts=False)
    lester_key_literal = pprint.pformat(sorted(LESTER_KEYS), width=120, compact=True, sort_dicts=False)

    marker = '_BOOK_MODE = {0: "kakuteki", 1: "kakuteki"}\n'
    if marker not in text:
        raise RuntimeError("V36 book marker not found")
    text = text.replace(
        marker,
        "_TAO_ACTIONS = " + tao_literal + "\n"
        + "_TAO_KEYS = " + key_literal + "\n\n"
        + "_SYED_ACTIONS = " + syed_literal + "\n"
        + "_SYED_KEYS = " + syed_key_literal + "\n\n"
        + "_LESTER_ACTIONS = " + lester_literal + "\n"
        + "_LESTER_KEYS = " + lester_key_literal + "\n\n"
        + marker,
        1,
    )

    start = text.index(marker)
    end = text.index("\ndef agent(obs):", start)
    selector = r'''_BOOK_MODE = {0: "kakuteki", 1: "kakuteki"}


def _standard_opponent(farm):
    """Reject build-pasture/weed branches where this continuation is unsafe."""
    expected = {"COW": 2, "MELON": 12, "PASTURE": 2, "SHEEP": 2, "WHEAT": 7}
    counts = {}
    for row in (_get(farm, "tiles", []) or []):
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value:
                    counts[value] = counts.get(value, 0) + 1
                    break
    return (
        len(_get(farm, "unlocked_quadrants", []) or []) == 1
        and sum(1 for row in (_get(farm, "tiles", []) or []) for tile in (row if isinstance(row, list) else [row])
                if isinstance(tile, dict) and tile.get("kind") == "WEED") == 0
        and all(counts.get(key, 0) == value for key, value in expected.items())
        and all(key in expected for key in counts)
    )


def _select_public_book(obs, step):
    """Select a screened continuation from public town/farm state only."""
    global _ACTIONS
    seat = 1 if int(_get(obs, "player", 0) or 0) == 1 else 0
    if step == 0:
        _BOOK_MODE[seat] = "kakuteki"
    farms = list(_get(obs, "farms", []) or [])
    opponent = farms[1 - seat] if len(farms) >= 2 else {}
    opponent_money = int(round(float(_get(opponent, "money", 0) or 0)))
    town = _get(obs, "town", {}) or {}
    shops = tuple(_get(town, "unlocked_shops", []) or [])
    key = (shops[0], shops[1], opponent_money) if len(shops) >= 2 else ("", "", -1)
    if step >= 144 and _BOOK_MODE[seat] == "kakuteki":
        if _standard_opponent(opponent):
            if key in _SYED_KEYS:
                _BOOK_MODE[seat] = "syed"
            elif key in _LESTER_KEYS:
                _BOOK_MODE[seat] = "lester"
            elif key in _TAO_KEYS:
                _BOOK_MODE[seat] = "tao"
        elif shops[:2] == ("YARN_STORE", "FARMERS_MARKET") and 1685 <= opponent_money <= 1691:
            _BOOK_MODE[seat] = "mrgrish"
        elif shops[:2] == ("BRUNCH_SPOT", "ICE_CREAM_SHOP") and 1702 <= opponent_money <= 1706:
            _BOOK_MODE[seat] = "legacy_timing"
    if _BOOK_MODE[seat] == "syed":
        _ACTIONS = _SYED_ACTIONS
    elif _BOOK_MODE[seat] == "lester":
        _ACTIONS = _LESTER_ACTIONS
    elif _BOOK_MODE[seat] == "tao":
        _ACTIONS = _TAO_ACTIONS
    elif _BOOK_MODE[seat] == "mrgrish":
        _ACTIONS = _MRGRISH_ACTIONS
    elif _BOOK_MODE[seat] == "legacy_timing":
        _ACTIONS = _LEGACY_TIMING_ACTIONS
    else:
        _ACTIONS = _KAKUTEKI_ACTIONS
'''
    text = text[:start] + selector + text[end:]
    text = text.replace("Transparent V36 Kaggriculture leader-meta agent.", "Transparent V37 adaptive public-state agent.", 1)
    text = text.replace("_ARCHITECTURE = 'V36 leader-meta route with public-state recovery and market preemption'",
                        "_ARCHITECTURE = 'V37 screened public-state continuation with V36 legality and recovery'", 1)
    text = text.replace(
        "# Selection criterion: the only screened route to beat every V35 top-10 loss;",
        "# Selection criterion: screened continuation against the expanded live top-10 loss panel;",
        1,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "main_v37_adaptive.py")
    args = parser.parse_args()
    build(args.output.resolve())
    print(args.output.resolve())
    print(f"bytes={args.output.stat().st_size}")


if __name__ == "__main__":
    main()
