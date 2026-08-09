#!/usr/bin/env python3
"""Build a live-state router from one or more current top-ranked replay corpora.

Full Kaggle replays are streamed one at a time.  Only compact action routes and
numeric public/private state features are retained.  The generated submission
uses no replay id, seed, team name, or opponent-private information at runtime.
"""

from __future__ import annotations

import argparse
import array
import base64
import gzip
import importlib.util
import json
import subprocess
import tempfile
import zlib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_TEAM = "Seb (allegedly)"
PRODUCTS = (
    "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
    "EGG", "MILK", "WOOL", "FERTILIZER",
)
SHOPS = (
    "BAKERY", "PIZZA_SHOP", "BRUNCH_SPOT", "YARN_STORE",
    "ICE_CREAM_SHOP", "PET_CAFE", "SMOOTHIE_SHOP", "FARMERS_MARKET",
)


def _load_public_feature_function():
    path = (
        ROOT / "pipelines" / "kaggle_public_agents"
        / "bnzn261029__visible-state-all-router-over-seven-public-syouya.py"
    )
    spec = importlib.util.spec_from_file_location("public_router_features", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import feature reference {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._features


def _extended_features(observation: dict[str, Any], base_features) -> tuple[float, ...]:
    values = list(base_features(observation))
    unlocked = list((observation.get("town", {}) or {}).get("unlocked_shops", []) or [])
    values.extend(float(unlocked.count(name)) * 3.0 for name in SHOPS)
    for position in range(8):
        active = unlocked[position] if position < len(unlocked) else None
        values.extend(2.0 if active == name else 0.0 for name in SHOPS)
    inventory = ((observation.get("market", {}) or {}).get("inventory", {}) or {})
    values.extend((10000.0 - float(inventory.get(name, 10000) or 10000)) / 50.0 for name in PRODUCTS)
    return tuple(round(float(value), 4) for value in values)


def _read_gzip(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def _write_gzip(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=9) as handle:
        json.dump(payload, handle, sort_keys=True, separators=(",", ":"))


def _download_replay(kaggle: Path, episode_id: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"seb-router-{episode_id}-") as temp:
        subprocess.run(
            [str(kaggle), "competitions", "replay", str(episode_id), "-p", temp, "-q"],
            check=True,
        )
        replay_path = next(Path(temp).glob("*.json"))
        return json.loads(replay_path.read_text(encoding="utf-8"))


def collect_state_traces(
    manifest_path: Path,
    state_dir: Path,
    kaggle: Path,
    team_name: str,
) -> list[dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected = sorted(
        (row for row in manifest if row.get("teamName") == team_name),
        key=lambda row: int(row.get("recencyIndex", 10**9)),
    )
    if not selected:
        raise RuntimeError(f"team {team_name!r} is absent from {manifest_path}")
    base_features = _load_public_feature_function()
    collected = []
    for row in selected:
        episode_id = int(row["episodeId"])
        seat = int(row["source_seat"])
        state_path = state_dir / f"episode-{episode_id}-seat{seat}.json.gz"
        if state_path.exists():
            payload = _read_gzip(state_path)
            print(f"episode={episode_id} seat={seat} cached", flush=True)
        else:
            replay = _download_replay(kaggle, episode_id)
            names = list((replay.get("info", {}) or {}).get("TeamNames", []) or [])
            if seat >= len(names) or names[seat] != team_name:
                if team_name not in names:
                    raise RuntimeError(f"{team_name!r} absent from episode {episode_id}: {names}")
                seat = names.index(team_name)
                state_path = state_dir / f"episode-{episode_id}-seat{seat}.json.gz"
            frames = list(replay.get("steps", []) or [])
            features = [
                _extended_features(dict(frames[step][seat]["observation"]), base_features)
                for step in range(min(719, len(frames) - 1))
            ]
            payload = {
                "metadata": {
                    "episode_id": episode_id,
                    "source_seat": seat,
                    "team": team_name,
                    "opponent_team": names[1 - seat],
                    "seed": (replay.get("info", {}) or {}).get("seed"),
                },
                "features": features,
            }
            _write_gzip(state_path, payload)
            print(f"episode={episode_id} seat={seat} features={len(features)}", flush=True)
            del replay
        if len(payload.get("features", [])) != 719:
            raise RuntimeError(f"episode {episode_id} has {len(payload.get('features', []))} feature rows")
        collected.append({**row, "source_seat": seat, "state_path": str(state_path.resolve())})
    return collected


AGENT_TEMPLATE = r'''"""Modern replay-state router over current top-ranked public games.

The packed payload is ordinary JSON compressed to keep the standalone Kaggle
submission practical.  Runtime selection uses live observations only.
"""
import base64
import copy
import json
import sys
import zlib
from array import array

_PACKED = __PACKED__
_DATA = json.loads(zlib.decompress(base64.b85decode(_PACKED)).decode("utf-8"))
LABELS = _DATA["labels"]
TRACE_PACKED = _DATA["trace_packed"]
del _PACKED, _DATA
FORCED_LABELS = __FORCED_LABELS__
FORCED_TRACE_PACKED = __FORCED_TRACE_PACKED__
_PACKED_FEATURES = __PACKED_FEATURES__
_FEATURE_VALUES = array("h")
_FEATURE_COMPRESSED = base64.b85decode(_PACKED_FEATURES)
_FEATURE_DECODER = zlib.decompressobj()
_FEATURE_PENDING = b""
for _FEATURE_OFFSET in range(0, len(_FEATURE_COMPRESSED), 65536):
    _FEATURE_CHUNK = _FEATURE_PENDING + _FEATURE_DECODER.decompress(
        _FEATURE_COMPRESSED[_FEATURE_OFFSET:_FEATURE_OFFSET + 65536]
    )
    _FEATURE_USABLE = len(_FEATURE_CHUNK) - (len(_FEATURE_CHUNK) % 2)
    if _FEATURE_USABLE:
        _FEATURE_VALUES.frombytes(_FEATURE_CHUNK[:_FEATURE_USABLE])
    _FEATURE_PENDING = _FEATURE_CHUNK[_FEATURE_USABLE:]
_FEATURE_CHUNK = _FEATURE_PENDING + _FEATURE_DECODER.flush()
if _FEATURE_CHUNK:
    _FEATURE_VALUES.frombytes(_FEATURE_CHUNK)
if sys.byteorder != "little":
    _FEATURE_VALUES.byteswap()
del (
    _PACKED_FEATURES, _FEATURE_COMPRESSED, _FEATURE_DECODER,
    _FEATURE_PENDING, _FEATURE_OFFSET, _FEATURE_CHUNK, _FEATURE_USABLE,
)
FEATURE_WIDTH = __FEATURE_WIDTH__
FEATURE_SCALE = __FEATURE_SCALE__
TRACE_COUNT = len(TRACE_PACKED)
ACTION_STEPS = 719
FORCED_ROUTE_BY_LABEL = {
    label: TRACE_COUNT + index for index, label in enumerate(FORCED_LABELS)
}

PREFERRED_INDEX = __PREFERRED_INDEX__
LOCK_TURNS = 8
PRODUCTS = ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER')
CROPS = ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON')
ANIMALS = ('COW', 'SHEEP', 'GOOSE')
INVENTORY_NAMES = ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER', 'COW', 'SHEEP', 'GOOSE')
SHOPS = ('BAKERY', 'PIZZA_SHOP', 'BRUNCH_SPOT', 'YARN_STORE', 'ICE_CREAM_SHOP', 'PET_CAFE', 'SMOOTHIE_SHOP', 'FARMERS_MARKET')
MAX_INVENTORIES = 12
_ROUTE = PREFERRED_INDEX
_OPENING_HANDS = None
_ROUTE_ACTION_INDEX = -1
_ROUTE_ACTIONS = None
_FORCED_ROUTE = None

# Four late five-hire continuations have complementary performance.  Every
# mapped public town state strictly improved route-win count over the default
# in the current top-ten panel; unknown states keep the stronger default.
FAMILY5_ALT_SHOPS = frozenset({
    ('BAKERY', 'YARN_STORE'),
    ('BRUNCH_SPOT', 'YARN_STORE'),
    ('FARMERS_MARKET', 'YARN_STORE'),
    ('ICE_CREAM_SHOP', 'BAKERY'),
    ('ICE_CREAM_SHOP', 'PET_CAFE'),
    ('ICE_CREAM_SHOP', 'PIZZA_SHOP'),
    ('ICE_CREAM_SHOP', 'YARN_STORE'),
    ('PET_CAFE', 'BRUNCH_SPOT'),
    ('PET_CAFE', 'ICE_CREAM_SHOP'),
    ('PIZZA_SHOP', 'BRUNCH_SPOT'),
    ('PIZZA_SHOP', 'ICE_CREAM_SHOP'),
    ('PIZZA_SHOP', 'YARN_STORE'),
    ('YARN_STORE', 'BAKERY'),
    ('YARN_STORE', 'BRUNCH_SPOT'),
    ('YARN_STORE', 'ICE_CREAM_SHOP'),
    ('YARN_STORE', 'PET_CAFE'),
    ('YARN_STORE', 'SMOOTHIE_SHOP'),
})
FAMILY5_ALT_ALL = False
# Experimental/final third continuation hook.  The builder can pack an
# additional suffix and map only public shop states that benefit from it.
FAMILY5_ALT2_SHOPS = frozenset({
    ('BAKERY', 'SMOOTHIE_SHOP'),
    ('BRUNCH_SPOT', 'PET_CAFE'),
    ('FARMERS_MARKET', 'FARMERS_MARKET'),
    ('FARMERS_MARKET', 'ICE_CREAM_SHOP'),
    ('FARMERS_MARKET', 'PET_CAFE'),
    ('ICE_CREAM_SHOP', 'SMOOTHIE_SHOP'),
    ('PIZZA_SHOP', 'SMOOTHIE_SHOP'),
    ('SMOOTHIE_SHOP', 'FARMERS_MARKET'),
})
FAMILY5_ALT2_ALL = False
FAMILY5_ALT3_SHOPS = frozenset({
    ('PET_CAFE', 'SMOOTHIE_SHOP'),
    ('SMOOTHIE_SHOP', 'PIZZA_SHOP'),
    ('YARN_STORE', 'FARMERS_MARKET'),
})
FAMILY5_ALT3_ALL = False
_SHIFT_STATE = {
    0: {"last_step": -1, "due_step": -1, "due": {}},
    1: {"last_step": -1, "due_step": -1, "due": {}},
}
CLONE_PREEMPT_START = 600
CLONE_PREEMPT_DISTANCE = 2
OPENING_MARKET_OVERRIDE = [
    ["BUY_PRODUCT", "WHEAT", 5],
    ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"], ["HIRE"],
    ["BUY_ANIMAL", "COW", 2],
    ["BUY_ANIMAL", "SHEEP", 2],
    ["BUY_SEED", "WHEAT", 7],
    ["BUY_SEED", "MELON", 12],
]


def _features(obs):
    farms = obs.get("farms", []) or []
    player = int(obs.get("player", 0) or 0)
    farm = farms[player]
    opponent = farms[1 - player]
    private = obs.get("private", {}) or {}

    def profile(item):
        counts = {name: 0 for name in (*CROPS, *ANIMALS)}
        weeds = empty = ripe = 0
        for row in item.get("tiles", []) or []:
            for tile in row:
                if tile is None:
                    empty += 1
                elif isinstance(tile, dict):
                    if tile.get("kind") == "WEED":
                        weeds += 1
                    crop = tile.get("crop")
                    animal = tile.get("animal")
                    if crop in counts:
                        counts[crop] += 1
                    if animal in counts:
                        counts[animal] += 1
                    ripe += max(0, int(tile.get("yield_units", 0) or 0))
        return counts, weeds, empty, ripe

    own, own_weeds, own_empty, own_ripe = profile(farm)
    opp, opp_weeds, opp_empty, opp_ripe = profile(opponent)
    own_weed_map = [
        1.0 if isinstance(tile, dict) and tile.get("kind") == "WEED" else 0.0
        for row in (farm.get("tiles", []) or []) for tile in row
    ]
    opp_weed_map = [
        1.0 if isinstance(tile, dict) and tile.get("kind") == "WEED" else 0.0
        for row in (opponent.get("tiles", []) or []) for tile in row
    ]
    size = len(farm.get("tiles", []) or []) or 10
    farmer = farm.get("farmer", [0, 0]) or [0, 0]
    hands = farm.get("hands", []) or []
    half = size // 2
    quadrants = [0, 0, 0, 0]
    for pos in hands:
        x, y = int(pos[0]), int(pos[1])
        quadrants[(2 if y >= half else 0) + (1 if x >= half else 0)] += 1
    if hands:
        hand_x = sum(float(pos[0]) for pos in hands) / len(hands)
        hand_y = sum(float(pos[1]) for pos in hands) / len(hands)
    else:
        hand_x = hand_y = 0.0
    shed = private.get("shed", {}) or {}
    inventories = private.get("inventories", []) or []
    carried = sum(max(0, int(value or 0)) for inventory in inventories for value in (inventory or {}).values())
    inventory_profile = [
        float((inventories[index] or {}).get(name, 0) or 0) * 0.5
        if index < len(inventories) else 0.0
        for index in range(MAX_INVENTORIES)
        for name in INVENTORY_NAMES
    ]
    seeds = private.get("seeds", {}) or {}
    market = obs.get("market", {}) or {}
    prices = market.get("prices", {}) or {}
    values = [
        float(farm.get("money", 0) or 0) / 5000.0,
        float(len(hands)) * 3.0,
        float(len(farm.get("unlocked_quadrants", []) or [])) * 6.0,
        float(farmer[0]), float(farmer[1]), hand_x, hand_y,
        *(float(value) * 2.0 for value in quadrants),
        *(float(own[name]) for name in CROPS),
        *(float(own[name]) * 3.0 for name in ANIMALS),
        float(own_weeds) * 0.5, float(own_empty) * 0.5, float(own_ripe) * 0.2,
        *own_weed_map,
        *(float(shed.get(name, 0) or 0) * 0.1 for name in PRODUCTS),
        float(carried) * 0.3,
        *inventory_profile,
        *(float(seeds.get(name, 0) or 0) * 0.25 for name in CROPS),
        *(float(prices.get(name, 0) or 0) / 50.0 for name in PRODUCTS),
        float(len(opponent.get("hands", []) or [])) * 2.0,
        float(len(opponent.get("unlocked_quadrants", []) or [])) * 4.0,
        *(float(opp[name]) * (2.0 if name in ANIMALS else 0.75) for name in (*CROPS, *ANIMALS)),
        float(opp_weeds) * 0.25, float(opp_empty) * 0.25, float(opp_ripe) * 0.1,
        *opp_weed_map,
    ]
    unlocked = list((obs.get("town", {}) or {}).get("unlocked_shops", []) or [])
    values.extend(float(unlocked.count(name)) * 3.0 for name in SHOPS)
    for position in range(8):
        active = unlocked[position] if position < len(unlocked) else None
        values.extend(2.0 if active == name else 0.0 for name in SHOPS)
    market_inventory = market.get("inventory", {}) or {}
    values.extend((10000.0 - float(market_inventory.get(name, 10000) or 10000)) / 50.0 for name in PRODUCTS)
    return tuple(round(value, 4) for value in values)


def _pick(obs, step):
    live = [int(round(value * FEATURE_SCALE)) for value in _features(obs)]
    step_offset = step * TRACE_COUNT * FEATURE_WIDTH
    distances = []
    for index in range(TRACE_COUNT):
        offset = step_offset + index * FEATURE_WIDTH
        distances.append(sum(
            abs(value - _FEATURE_VALUES[offset + position])
            for position, value in enumerate(live)
        ))
    return min(
        range(TRACE_COUNT),
        key=lambda index: (distances[index], index != _ROUTE, index != PREFERRED_INDEX, index),
    )


def _opening_counter(obs):
    """Select a compatible counter from the opponent's public first move.

    The initial state is identical for every seed, so selection at step zero
    would be leakage or guessing.  At step one, hand count and money are public
    consequences of the opponent's submitted opening and are safe to use.
    """
    farms = obs.get("farms", []) or []
    player = int(obs.get("player", 0) or 0)
    if len(farms) < 2:
        return None
    opponent = farms[1 - player]
    hands = len(opponent.get("hands", []) or [])
    money = float(opponent.get("money", 0) or 0)
    label = None
    if hands <= 3 and 140 <= money <= 190:
        label = "health"
    elif hands == 5 and 40 <= money <= 70:
        label = "saikyo"
    elif hands == 5 and 10 <= money <= 35:
        # This continuation is the maximin winner across the two public-state
        # identical Kaito openings in the regression suite (+202 and +422).
        label = "health"
    elif hands >= 7:
        # Seven-or-more hired hands are an observable signature of the Seb
        # family.  Its dedicated crossover wins 13/20 of that family versus
        # 6/20 for the generic continuation while retaining the known
        # Francesco regression win.
        label = "seb"
    return FORCED_ROUTE_BY_LABEL.get(label)


def _route_actions(index):
    global _ROUTE_ACTION_INDEX, _ROUTE_ACTIONS
    if _ROUTE_ACTION_INDEX != index or _ROUTE_ACTIONS is None:
        packed = (
            TRACE_PACKED[index]
            if index < TRACE_COUNT
            else FORCED_TRACE_PACKED[index - TRACE_COUNT]
        )
        _ROUTE_ACTIONS = json.loads(
            zlib.decompress(base64.b85decode(packed)).decode("utf-8")
        )
        _ROUTE_ACTION_INDEX = index
    return _ROUTE_ACTIONS


def _clone_profile(farm):
    counts = {name: 0 for name in (*CROPS, *ANIMALS, "PASTURE", "COOP", "WEED")}
    for row in farm.get("tiles", []) or []:
        for tile in row:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value in counts:
                    counts[value] += 1
                    break
    return (
        len(farm.get("hands", []) or []),
        len(farm.get("unlocked_quadrants", []) or []),
        tuple(counts[name] for name in sorted(counts)),
    )


def _clone_distance(obs):
    farms = obs.get("farms", []) or []
    if len(farms) < 2:
        return 10 ** 9
    left = _clone_profile(farms[0])
    right = _clone_profile(farms[1])
    return (
        abs(left[0] - right[0])
        + 3 * abs(left[1] - right[1])
        + sum(abs(a - b) for a, b in zip(left[2], right[2]))
    )


def _clone_preempt(obs, action, step):
    """Move available next-turn clone sales one turn early near game end."""
    player = int(obs.get("player", 0) or 0)
    state = _SHIFT_STATE[player]
    if step == 0 or step < int(state.get("last_step", -1)):
        state = {"last_step": step, "due_step": -1, "due": {}}
        _SHIFT_STATE[player] = state
    state["last_step"] = step

    market = [list(order) for order in action.get("market", []) or []]
    if int(state.get("due_step", -1)) == step:
        due = dict(state.get("due", {}) or {})
        repaid = []
        for order in market:
            if len(order) >= 3 and order[0] == "SELL" and due.get(order[1], 0) > 0:
                reduction = min(max(0, int(order[2])), int(due[order[1]]))
                order[2] = max(0, int(order[2]) - reduction)
                due[order[1]] -= reduction
                if order[2] <= 0:
                    continue
            repaid.append(order)
        market = repaid
        state["due_step"], state["due"] = -1, {}
    elif int(state.get("due_step", -1)) < step:
        state["due_step"], state["due"] = -1, {}

    action["market"] = market[:10]
    if not (CLONE_PREEMPT_START <= step < ACTION_STEPS - 1):
        return action
    if state.get("due") or _clone_distance(obs) > CLONE_PREEMPT_DISTANCE:
        return action

    future = _route_actions(_ROUTE)[step + 1].get("market", []) or []
    if not any(len(order) >= 3 and order[0] == "SELL" for order in future):
        return action
    shed = dict((obs.get("private", {}) or {}).get("shed", {}) or {})
    for order in market:
        if len(order) >= 3 and order[0] == "SELL":
            shed[order[1]] = max(0, int(shed.get(order[1], 0) or 0) - max(0, int(order[2])))
    shifted = {}
    for order in future:
        if len(order) < 3 or order[0] != "SELL":
            continue
        item = order[1]
        quantity = min(max(0, int(order[2])), max(0, int(shed.get(item, 0) or 0)))
        if quantity <= 0:
            continue
        existing = next(
            (row for row in market if len(row) >= 3 and row[0] == "SELL" and row[1] == item),
            None,
        )
        if existing is not None:
            existing[2] = int(existing[2]) + quantity
        elif len(market) < 10:
            market.append(["SELL", item, quantity])
        else:
            continue
        shed[item] = max(0, int(shed.get(item, 0) or 0) - quantity)
        shifted[item] = shifted.get(item, 0) + quantity
    if shifted:
        state["due_step"] = step + 1
        state["due"] = shifted
        action["market"] = market[:10]
    return action


def agent(obs, config=None):
    global _ROUTE, _FORCED_ROUTE, _OPENING_HANDS
    try:
        clock = int(obs.get("day", 0) or 0) * 24 + int(obs.get("hour", 0) or 0)
        step = min(int(obs.get("step", clock) or 0), ACTION_STEPS - 1)
        if step == 0:
            _ROUTE = PREFERRED_INDEX
            _FORCED_ROUTE = None
            _OPENING_HANDS = None
        elif step == 1:
            farms = obs.get("farms", []) or []
            player = int(obs.get("player", 0) or 0)
            if len(farms) >= 2:
                _OPENING_HANDS = len(farms[1 - player].get("hands", []) or [])
            _FORCED_ROUTE = _opening_counter(obs)
        elif (
            step == 159
            and _OPENING_HANDS == 5
            and _FORCED_ROUTE == FORCED_ROUTE_BY_LABEL.get("health")
        ):
            shops = tuple(
                ((obs.get("town", {}) or {}).get("unlocked_shops", []) or [])[:2]
            )
            alternate3 = FORCED_ROUTE_BY_LABEL.get("family5_alt3")
            alternate2 = FORCED_ROUTE_BY_LABEL.get("family5_alt2")
            if alternate3 is not None and (
                FAMILY5_ALT3_ALL or shops in FAMILY5_ALT3_SHOPS
            ):
                _FORCED_ROUTE = alternate3
            elif alternate2 is not None and (
                FAMILY5_ALT2_ALL or shops in FAMILY5_ALT2_SHOPS
            ):
                _FORCED_ROUTE = alternate2
            elif FAMILY5_ALT_ALL or shops in FAMILY5_ALT_SHOPS:
                alternate = FORCED_ROUTE_BY_LABEL.get("family5_alt")
                if alternate is not None:
                    _FORCED_ROUTE = alternate
        if _FORCED_ROUTE is not None:
            _ROUTE = _FORCED_ROUTE
        elif step in (0, 1) or step % LOCK_TURNS == 0:
            _ROUTE = _pick(obs, step)
        action = copy.deepcopy(_route_actions(_ROUTE)[step])
        if step == 0 and OPENING_MARKET_OVERRIDE is not None:
            action["market"] = copy.deepcopy(OPENING_MARKET_OVERRIDE)
        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms", []) or []
        hand_count = len((farms[player] if player < len(farms) else {}).get("hands", []) or [])
        hands = list(action.get("hands", []) or [])
        if len(hands) < hand_count:
            hands.extend([["PASS"] for _ in range(hand_count - len(hands))])
        action["hands"] = hands[:hand_count]
        return _clone_preempt(obs, action, step)
    except Exception:
        player = int(obs.get("player", 0) or 0)
        farms = obs.get("farms", []) or []
        hand_count = len((farms[player] if player < len(farms) else {}).get("hands", []) or [])
        return {"farmer": ["PASS"], "hands": [["PASS"] for _ in range(hand_count)], "market": []}
'''


def build(
    rows: list[dict[str, Any]],
    destination: Path,
    forced_routes: list[tuple[str, Path]] | None = None,
) -> None:
    # Identical public opening states occur when two selected teams played each
    # other.  Put the higher-scoring source first so the deterministic distance
    # tie chooses the stronger side of that exact game.
    rows = sorted(
        rows,
        key=lambda row: (
            -float(row.get("reward", 0.0) or 0.0),
            int(row.get("episodeId", 0) or 0),
            int(row.get("source_seat", 0) or 0),
        ),
    )
    labels = []
    traces = []
    features_by_trace = []
    preferred_index = max(range(len(rows)), key=lambda index: float(rows[index].get("reward", 0.0) or 0.0))
    for row in rows:
        route = _read_gzip(Path(row["path"]))
        state = _read_gzip(Path(row["state_path"]))
        actions = route.get("actions", [])
        features = state.get("features", [])
        if len(actions) != 719 or len(features) != 719:
            raise RuntimeError(f"invalid trace lengths for episode {row['episodeId']}")
        labels.append(
            f"{row['episodeId']}:{row.get('teamName')}:{row['source_seat']}:{row.get('opponent_team')}"
        )
        traces.append(actions)
        features_by_trace.append(features)
    feature_width = len(features_by_trace[0][0])
    feature_scale = 100
    feature_values = array.array("h")
    for step in range(719):
        for trace_index in range(len(features_by_trace)):
            row = features_by_trace[trace_index][step]
            if len(row) != feature_width:
                raise RuntimeError("inconsistent feature width")
            quantized = [int(round(float(value) * feature_scale)) for value in row]
            if any(value < -32768 or value > 32767 for value in quantized):
                raise RuntimeError("feature exceeds signed 16-bit packed range")
            feature_values.extend(quantized)
    if feature_values.itemsize != 2:
        raise RuntimeError("unexpected signed-short width")
    if __import__("sys").byteorder != "little":
        feature_values.byteswap()
    packed_features = base64.b85encode(zlib.compress(feature_values.tobytes(), 9)).decode("ascii")
    trace_packed = [
        base64.b85encode(
            zlib.compress(json.dumps(trace, separators=(",", ":")).encode("utf-8"), 9)
        ).decode("ascii")
        for trace in traces
    ]
    forced_labels = []
    forced_trace_packed = []
    for label, path in forced_routes or []:
        route = _read_gzip(path)
        actions = route.get("actions", [])
        if len(actions) != 719:
            raise RuntimeError(f"invalid forced route length for {path}: {len(actions)}")
        forced_labels.append(label)
        forced_trace_packed.append(
            base64.b85encode(
                zlib.compress(json.dumps(actions, separators=(",", ":")).encode("utf-8"), 9)
            ).decode("ascii")
        )
    data = {"labels": labels, "trace_packed": trace_packed}
    packed = base64.b85encode(zlib.compress(json.dumps(data, separators=(",", ":")).encode("utf-8"), 9)).decode("ascii")
    source = (
        AGENT_TEMPLATE
        .replace("__PACKED__", repr(packed))
        .replace("__PACKED_FEATURES__", repr(packed_features))
        .replace("__FORCED_LABELS__", repr(forced_labels))
        .replace("__FORCED_TRACE_PACKED__", repr(forced_trace_packed))
        .replace("__FEATURE_WIDTH__", str(feature_width))
        .replace("__FEATURE_SCALE__", str(feature_scale))
        .replace("__PREFERRED_INDEX__", str(preferred_index))
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(source, encoding="utf-8", newline="\n")
    print(
        f"traces={len(traces)} forced={len(forced_trace_packed)} preferred={preferred_index} "
        f"actions_packed={len(packed)} features_packed={len(packed_features)}"
    )
    print(destination.resolve())
    print(f"bytes={destination.stat().st_size}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=ROOT / "best_replay/top10_recent20/manifest.json")
    parser.add_argument("--state-dir", type=Path, default=ROOT / "best_replay/top10_recent20/state_traces_seb")
    parser.add_argument("--kaggle", type=Path, default=ROOT / ".venv/bin/kaggle")
    parser.add_argument("--team", default=DEFAULT_TEAM)
    parser.add_argument(
        "--extra-team",
        action="append",
        default=[],
        metavar="TEAM=STATE_DIR",
        help="Add another team's traces, caching compact states in STATE_DIR",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "main_modern_seb_router.py")
    parser.add_argument(
        "--forced-route",
        action="append",
        default=[],
        metavar="LABEL=ROUTE_GZ",
        help="Pack a route selected only by an observable opening signature",
    )
    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="Download/cache compact state traces without building an agent",
    )
    args = parser.parse_args()
    rows = collect_state_traces(
        args.manifest.resolve(), args.state_dir.resolve(), args.kaggle.resolve(), args.team
    )
    for specification in args.extra_team:
        if "=" not in specification:
            parser.error("--extra-team must have the form TEAM=STATE_DIR")
        team_name, state_dir = specification.split("=", 1)
        rows.extend(
            collect_state_traces(
                args.manifest.resolve(),
                Path(state_dir).resolve(),
                args.kaggle.resolve(),
                team_name,
            )
        )
    if args.collect_only:
        print(f"collected={len(rows)}")
        return
    forced_routes = []
    for specification in args.forced_route:
        if "=" not in specification:
            parser.error("--forced-route must have the form LABEL=ROUTE_GZ")
        label, route_path = specification.split("=", 1)
        forced_routes.append((label, Path(route_path).resolve()))
    build(rows, args.output.resolve(), forced_routes)


if __name__ == "__main__":
    main()
