import pandas as pd
from IPython.display import display

route_atlas = pd.DataFrame([{'route_index': 0, 'label': 'BALANCED', 'purpose': 'baseline balanced plan', 'submission_id': 55892163, 'episode_id': 103823935, 'source_seat': 0, 'action_sha256': '3319bb4e555847149dd5c82d3626a697056455d120fca487de52e1d5f4a9bfd4', 'trace_sha256': '702e954bd84fcd99362bda431ea5e86981198507c9d4dd3d2854d6321e481be0', 'first_divergence_from_base': None, 'move_actions': 3470, 'plant_actions': 243, 'harvest_actions': 467, 'animal_actions': 1037, 'buy_orders': 128, 'sell_orders': 285}, {'route_index': 2, 'label': 'CASH_RECOVERY', 'purpose': 'recover from a negative cash gap', 'submission_id': 55865730, 'episode_id': 104056237, 'source_seat': 1, 'action_sha256': '39be02a28445bcd831735e8234903f1ccc1f5f2951ec66989bb9dcd0ea7e5df3', 'trace_sha256': '16a7629bee11f12d13a022e4a11ae88d8a6a35dc9cf14094ea9f050265843f21', 'first_divergence_from_base': 264, 'move_actions': 3473, 'plant_actions': 243, 'harvest_actions': 467, 'animal_actions': 1035, 'buy_orders': 128, 'sell_orders': 279}, {'route_index': 3, 'label': 'YARN_ENGINE', 'purpose': 'build around the Yarn Store', 'submission_id': 55865730, 'episode_id': 103609700, 'source_seat': 0, 'action_sha256': '94ef053e8ec78494c3df5d4e77a38e5e1d4306f263fbe8bf89ce6d4aab1572fe', 'trace_sha256': '198ab4df3ebf8b6777397f73b179141ca02c900eea632991c4929f09a40f4e08', 'first_divergence_from_base': 144, 'move_actions': 3275, 'plant_actions': 239, 'harvest_actions': 459, 'animal_actions': 1196, 'buy_orders': 130, 'sell_orders': 286}, {'route_index': 14, 'label': 'YARN_LATE', 'purpose': 'connect a third-shop Yarn tail', 'submission_id': 55892163, 'episode_id': 103576156, 'source_seat': 1, 'action_sha256': '45edb4cacfc0b74a450222454b0de14559399e3ae10267ea22035a50b2523729', 'trace_sha256': '8a02db62aa17124bc0d8ac692b442541b83349937ef75d569e55ccd00c33e955', 'first_divergence_from_base': 216, 'move_actions': 3279, 'plant_actions': 239, 'harvest_actions': 459, 'animal_actions': 1197, 'buy_orders': 131, 'sell_orders': 287}, {'route_index': 16, 'label': 'LAND_RECOVERY', 'purpose': 'recover from a negative land gap', 'submission_id': 55865730, 'episode_id': 103926612, 'source_seat': 0, 'action_sha256': 'ec38433bc7080fca2139d2e2cae735f2c4a3c23c145a8e60c6762a41ff4ffab0', 'trace_sha256': 'bb7ab81bab101354bfe17b3739dc83558243e8d3e93485b02c816bfbf50d650a', 'first_divergence_from_base': 144, 'move_actions': 3042, 'plant_actions': 239, 'harvest_actions': 459, 'animal_actions': 1184, 'buy_orders': 129, 'sell_orders': 253}, {'route_index': 18, 'label': 'WHEAT_RECOVERY', 'purpose': 'use wheat price and cash gap in the tail', 'submission_id': 55865730, 'episode_id': 103908697, 'source_seat': 0, 'action_sha256': '355effb1b7a24b0fe98715e5b86b30e6cd19ff2312922f6c3ba845dd11f598bf', 'trace_sha256': '13507bd1490055bfeed59e43afe00ae9f704664ff918f65f0d7fed30401f1c80', 'first_divergence_from_base': 144, 'move_actions': 3042, 'plant_actions': 239, 'harvest_actions': 459, 'animal_actions': 1184, 'buy_orders': 129, 'sell_orders': 255}])
identity = route_atlas.rename(columns={
    "label": "plan", "purpose": "role", "first_divergence_from_base": "first divergence",
    "episode_id": "public episode",
})[["plan", "role", "first divergence", "public episode"]].copy()
identity["first divergence"] = identity["first divergence"].map(
    lambda value: "base route" if pd.isna(value) else f"step {int(value)}"
)

def fieldbook_table(frame):
    return (frame.style.hide(axis="index")
        .set_properties(**{"text-align": "left", "padding": "9px 12px", "border-color": "#e2d8c6"})
        .set_table_styles([
            {"selector": "th", "props": [("background", "#285943"), ("color", "white"), ("text-align", "left")] },
            {"selector": "tbody tr:nth-child(even)", "props": [("background", "#f7f2e7")] },
        ]))

display(fieldbook_table(identity).set_properties(
    subset=["role"], **{"min-width": "250px", "white-space": "normal"}
))


%%writefile fieldbook_logic.py
# SPDX-License-Identifier: Apache-2.0
"""ShopForge Fieldbook: six readable plans and a small public-state tree.

Generated from the public ShopForge episodes listed in ROUTE_SOURCES.
There is no compressed action blob and no exact-money lookup table.
"""

from __future__ import annotations

import copy

ITEMS = ('WHEAT',
 'CARROT',
 'TOMATO',
 'STRAWBERRY',
 'MELON',
 'EGG',
 'MILK',
 'WOOL',
 'FERTILIZER',
 'GOOSE',
 'COW',
 'SHEEP')
PRODUCTS = ITEMS[:9]
ROUTE_SOURCES = {0: {'action_sha256': '3319bb4e555847149dd5c82d3626a697056455d120fca487de52e1d5f4a9bfd4',
     'episode_id': 103823935,
     'label': 'BALANCED'},
 2: {'action_sha256': '39be02a28445bcd831735e8234903f1ccc1f5f2951ec66989bb9dcd0ea7e5df3',
     'episode_id': 104056237,
     'label': 'CASH_RECOVERY'},
 3: {'action_sha256': '94ef053e8ec78494c3df5d4e77a38e5e1d4306f263fbe8bf89ce6d4aab1572fe',
     'episode_id': 103609700,
     'label': 'YARN_ENGINE'},
 14: {'action_sha256': '45edb4cacfc0b74a450222454b0de14559399e3ae10267ea22035a50b2523729',
      'episode_id': 103576156,
      'label': 'YARN_LATE'},
 16: {'action_sha256': 'ec38433bc7080fca2139d2e2cae735f2c4a3c23c145a8e60c6762a41ff4ffab0',
      'episode_id': 103926612,
      'label': 'LAND_RECOVERY'},
 18: {'action_sha256': '355effb1b7a24b0fe98715e5b86b30e6cd19ff2312922f6c3ba845dd11f598bf',
      'episode_id': 103908697,
      'label': 'WHEAT_RECOVERY'}}
ROUTE_NAMES = {index: row["label"] for index, row in ROUTE_SOURCES.items()}

DEFAULT_SETTINGS = {
    "branch_depth": 2,
    "sell_lead": True,
    "terminal_liquidation": True,
    "severe_cash_gap": -199.0,
    "very_severe_cash_gap": -721.5,
    "wheat_cheap": 29.5,
    "low_cash": 242.5,
}

# One line is: step | farmer, hands... | market orders.
# The first unit is the farmer. Remaining units are farm hands.
from fieldbook_tapes import PLAN_SCRIPTS

# <FIELD_BOOK_PLAN_SCRIPTS>


def _get(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(value, key, default)


def _parse_token(token):
    parts = token.split(":")
    action = [parts[0]]
    for value in parts[1:]:
        action.append(int(value) if value.lstrip("-").isdigit() else value)
    return action


def _decode_plan(script):
    result = {}
    for line in script.splitlines():
        step_text, units_text, market_text = line.split("|", 2)
        units = [_parse_token(token) for token in units_text.split(",")]
        market = [] if market_text == "-" else [
            _parse_token(token) for token in market_text.split(",")
        ]
        result[int(step_text)] = {
            "farmer": units[0],
            "hands": units[1:],
            "market": market,
        }
    return result


_SEGMENTS = {name: _decode_plan(script) for name, script in PLAN_SCRIPTS.items()}


def _compose(root_name, tail_name):
    actions = [None] * 719
    for segment_name in ("OPENING_000_143", root_name, tail_name):
        for step, action in _SEGMENTS[segment_name].items():
            if actions[step] is not None:
                raise ValueError(f"overlapping Fieldbook step {step}")
            actions[step] = action
    if any(action is None for action in actions):
        raise ValueError("Fieldbook route has a missing step")
    return actions


ROUTES = {
    0: _compose("ROOT_BALANCED_144_215", "TAIL_BALANCED_216_718"),
    2: _compose("ROOT_BALANCED_144_215", "TAIL_CASH_RECOVERY_216_718"),
    3: _compose("ROOT_YARN_144_215", "TAIL_YARN_ENGINE_216_718"),
    14: _compose("ROOT_BALANCED_144_215", "TAIL_YARN_LATE_216_718"),
    16: _compose("ROOT_LAND_RECOVERY_144_215", "TAIL_LAND_RECOVERY_216_718"),
    18: _compose("ROOT_LAND_RECOVERY_144_215", "TAIL_WHEAT_RECOVERY_216_718"),
}


def _step(observation):
    raw = _get(observation, "step")
    if raw is not None:
        return int(raw)
    return int(_get(observation, "day", 0) or 0) * 24 + int(
        _get(observation, "hour", 0) or 0
    )


def _shops(observation):
    town = _get(observation, "town", {}) or {}
    return list(_get(town, "unlocked_shops", []) or [])


def _farm_pair(observation):
    farms = list(_get(observation, "farms", []) or [])
    player = int(_get(observation, "player", 0) or 0)
    own = farms[player] if player < len(farms) else {}
    rival = farms[1 - player] if len(farms) >= 2 else {}
    return player, own, rival


def _capture_step144(observation):
    _, own, rival = _farm_pair(observation)
    market = _get(observation, "market", {}) or {}
    prices = _get(market, "prices", {}) or {}
    own_money = float(_get(own, "money", 0.0) or 0.0)
    rival_money = float(_get(rival, "money", 0.0) or 0.0)
    own_land = len(list(_get(own, "unlocked_quadrants", []) or []))
    rival_land = len(list(_get(rival, "unlocked_quadrants", []) or []))
    return {
        "shops": _shops(observation)[:2],
        "cash": own_money,
        "cash_gap": own_money - rival_money,
        "land_gap": own_land - rival_land,
        "wheat_price": float(_get(prices, "WHEAT", 0.0) or 0.0),
    }


def _root_choice(cache):
    shops = cache["shops"]
    first = shops[0] if len(shops) >= 1 else None
    second = shops[1] if len(shops) >= 2 else None
    if first == "YARN_STORE":
        return "YARN", 3
    if second == "YARN_STORE":
        if cache["land_gap"] < 0:
            return "LAND_RECOVERY", 16
        return "YARN", 3
    return "BALANCED", 0


def _terminal_choice(group, cache, third_shop, settings):
    if group == "YARN":
        return 3
    if group == "LAND_RECOVERY":
        if cache["cash_gap"] <= settings["severe_cash_gap"]:
            if cache["wheat_price"] <= settings["wheat_cheap"]:
                return 18 if cache["cash"] <= settings["low_cash"] else 16
            return 16 if cache["cash_gap"] <= settings["very_severe_cash_gap"] else 18
        second = cache["shops"][1] if len(cache["shops"]) >= 2 else None
        if second != "BRUNCH_SPOT" and third_shop != "FARMERS_MARKET":
            return 16
        return 18
    second = cache["shops"][1] if len(cache["shops"]) >= 2 else None
    if third_shop != "YARN_STORE" and second != "YARN_STORE":
        return 2 if cache["cash_gap"] < 0 else 0
    return 14


def _configuration(configuration, key, default):
    return _get(configuration or {}, key, default)


def _order_limit(configuration):
    return max(0, min(16, int(_configuration(configuration, "maxMarketOrdersPerTurn", 10))))


def _shed_adjacent(position, board_size):
    if not isinstance(position, (list, tuple)) or len(position) < 2:
        return False
    half = board_size // 2
    return position[0] in {half - 1, half} and position[1] in {half - 1, half}


def _projected_shed(observation, action, configuration):
    _, own, _ = _farm_pair(observation)
    private = _get(observation, "private", {}) or {}
    shed = _get(private, "shed", {}) or {}
    projected = {item: max(0, int(_get(shed, item, 0) or 0)) for item in PRODUCTS}
    total = sum(projected.values())
    capacity = int(_configuration(configuration, "shedCapacity", 100))
    board_size = int(_configuration(configuration, "boardSize", 10))
    positions = [_get(own, "farmer", None), *list(_get(own, "hands", []) or [])]
    inventories = list(_get(private, "inventories", []) or [])
    unit_actions = [action.get("farmer") or ["PASS"], *list(action.get("hands") or [])]
    for index, unit_action in enumerate(unit_actions[: len(positions)]):
        if not _shed_adjacent(positions[index], board_size):
            continue
        operation = unit_action[0] if unit_action else "PASS"
        if operation == "PICKUP" and len(unit_action) >= 2 and unit_action[1] in projected:
            requested = int(unit_action[2]) if len(unit_action) >= 3 else 1
            quantity = min(projected[unit_action[1]], max(0, requested))
            projected[unit_action[1]] -= quantity
            total -= quantity
        elif operation == "DROP":
            inventory = inventories[index] if index < len(inventories) else {}
            for item in ITEMS:
                held = max(0, int(_get(inventory, item, 0) or 0))
                room = max(0, capacity - total)
                dropped = min(held, room)
                if item in projected:
                    projected[item] += dropped
                total += dropped
    return projected


def _suppress_advanced_sale(action, sell_state, step):
    if sell_state.get("due_step") != step:
        return action
    remaining = dict(sell_state.get("suppress", {}))
    kept = []
    for order in action.get("market", []):
        order = list(order)
        if order and order[0] == "SELL" and len(order) >= 3 and remaining.get(order[1], 0) > 0:
            removed = min(max(0, int(order[2])), remaining[order[1]])
            order[2] -= removed
            remaining[order[1]] -= removed
        if not order or order[0] != "SELL" or int(order[2]) > 0:
            kept.append(order)
    action["market"] = kept
    return action


def _lead_sale(observation, action, future_action, sell_state, step, configuration):
    next_state = {"due_step": -1, "suppress": {}}
    future_step = step + 1
    unlock_period = int(_configuration(configuration, "townShopUnlockInterval", 3)) * int(
        _configuration(configuration, "turnsPerDay", 24)
    )
    demand_period = int(_configuration(configuration, "townShopSellInterval", 4))
    if future_step >= 719 or future_step % max(1, unlock_period) == 0 or step % max(1, demand_period) == 0:
        sell_state.clear()
        sell_state.update(next_state)
        return action
    projected = _projected_shed(observation, action, configuration)
    prices = _get(_get(observation, "market", {}) or {}, "prices", {}) or {}
    planned = {item: 0 for item in PRODUCTS}
    for order in future_action.get("market", []):
        if order and order[0] == "SELL" and order[1] in planned:
            planned[order[1]] += max(0, int(order[2]))
    already = {order[1] for order in action.get("market", []) if order and order[0] == "SELL"}
    for item in PRODUCTS:
        if item in {"WHEAT", "FERTILIZER"} or planned[item] <= 0 or item in already:
            continue
        quantity = min(projected[item], planned[item])
        if quantity <= 0 or float(_get(prices, item, 0) or 0) < 2:
            continue
        if len(action.get("market", [])) >= _order_limit(configuration):
            break
        action.setdefault("market", []).append(["SELL", item, quantity])
        next_state["suppress"][item] = quantity
    if next_state["suppress"]:
        next_state["due_step"] = future_step
    sell_state.clear()
    sell_state.update(next_state)
    return action


def _terminal_sale(observation, action, step, configuration):
    episode_steps = int(_configuration(configuration, "episodeSteps", 720))
    if step < episode_steps - 2:
        return action
    projected = _projected_shed(observation, action, configuration)
    action["market"] = [
        ["SELL", item, quantity]
        for item, quantity in projected.items()
        if quantity > 0
    ][:_order_limit(configuration)]
    return action


class FieldbookRuntime:
    """Stateful but readable route selection and SELL timing."""

    def __init__(self, **overrides):
        self.settings = {**DEFAULT_SETTINGS, **overrides}
        self.route_state = {}
        self.sell_state = {}

    def _route(self, observation, step, player):
        if self.settings["branch_depth"] <= 0 or step < 144:
            return 0
        state = self.route_state.get(player)
        if state is None or state.get("stage", 0) < 2:
            cache = _capture_step144(observation)
            group, route = _root_choice(cache)
            state = {"stage": 2, "cache": cache, "group": group, "route": route}
            self.route_state[player] = state
        if self.settings["branch_depth"] >= 2 and step >= 216 and state["stage"] < 3:
            shops = _shops(observation)
            third = shops[2] if len(shops) >= 3 else None
            state["route"] = _terminal_choice(state["group"], state["cache"], third, self.settings)
            state["stage"] = 3
        return state["route"]

    def act(self, observation, configuration=None):
        step = min(max(_step(observation), 0), 718)
        player, own, _ = _farm_pair(observation)
        if step == 0:
            self.route_state.pop(player, None)
            self.sell_state[player] = {"due_step": -1, "suppress": {}}
        route = self._route(observation, step, player)
        action = copy.deepcopy(ROUTES[route][step])
        expected_hands = len(list(_get(own, "hands", []) or []))
        hands = list(action.get("hands") or [])
        hands.extend([["PASS"] for _ in range(max(0, expected_hands - len(hands)))])
        action["hands"] = hands[:expected_hands]

        state = self.sell_state.setdefault(player, {"due_step": -1, "suppress": {}})
        action = _suppress_advanced_sale(action, state, step)
        if self.settings["sell_lead"]:
            future = ROUTES[route][step + 1] if step + 1 < 719 else {"market": []}
            action = _lead_sale(observation, action, future, state, step, configuration)
        else:
            state.clear()
            state.update({"due_step": -1, "suppress": {}})
        if self.settings["terminal_liquidation"]:
            action = _terminal_sale(observation, action, step, configuration)
        return action


def make_agent(**overrides):
    runtime = FieldbookRuntime(**overrides)

    def policy(observation, configuration=None):
        return runtime.act(observation, configuration)

    policy.runtime = runtime
    return policy


agent = make_agent()
main = agent


import hashlib
from pathlib import Path

tape_candidates = [
    Path("fieldbook_tapes.py"),
    Path("/kaggle/input/shopforge-fieldbook-tapes/fieldbook_tapes.py"),
]
tape_path = next((path for path in tape_candidates if path.exists()), None)
expected_tape_sha256 = "114224c60244d2d905078ecaea409b3116994861f474e9717ddcd456a9f062f0"
assert tape_path is not None, "Add the private Fieldbook tape Dataset as a Notebook input"
assert hashlib.sha256(tape_path.read_bytes()).hexdigest() == expected_tape_sha256
tape_lines = tape_path.read_text(encoding="utf-8").splitlines()
print(f"separate tape: {len(tape_lines):,} lines / {tape_path.stat().st_size:,} bytes")
print("edit fieldbook_tapes.py to change individual planned actions")


import hashlib
import importlib.util
from pathlib import Path

TAPE_BEGIN = "# === BEGIN FIELD BOOK PLAN SCRIPTS ==="
TAPE_END = "# === END FIELD BOOK PLAN SCRIPTS ==="
TAPE_PLACEHOLDER = "from fieldbook_tapes import PLAN_SCRIPTS\n\n# <FIELD_BOOK_PLAN_SCRIPTS>"

logic_source = Path("fieldbook_logic.py").read_text(encoding="utf-8")
tape_source = tape_path.read_text(encoding="utf-8")
tape_begin = tape_source.index(TAPE_BEGIN) + len(TAPE_BEGIN) + 1
tape_end = tape_source.index("\n" + TAPE_END, tape_begin)
tape_block = tape_source[tape_begin:tape_end]
assert logic_source.count(TAPE_PLACEHOLDER) == 1
assembled_source = logic_source.replace(TAPE_PLACEHOLDER, tape_block)
Path("fieldbook_agent.py").write_text(assembled_source, encoding="utf-8")
Path("main.py").write_text(assembled_source, encoding="utf-8")

spec = importlib.util.spec_from_file_location("fieldbook_agent", "fieldbook_agent.py")
fieldbook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fieldbook)
artifact_sha256 = hashlib.sha256(Path("fieldbook_agent.py").read_bytes()).hexdigest()
submission_sha256 = hashlib.sha256(Path("main.py").read_bytes()).hexdigest()
assert submission_sha256 == artifact_sha256
print("agent SHA-256:", artifact_sha256)
print("main.py SHA-256:", submission_sha256)
print("routes:", {index: fieldbook.ROUTE_NAMES[index] for index in fieldbook.ROUTES})
assert len(fieldbook.ROUTES) == 6
assert all(len(route) == 719 for route in fieldbook.ROUTES.values())

tape_structure = pd.DataFrame([
    ("OPENING", "day 0–6", 144, "shared by all routes"),
    ("ROOT", "day 6–9", 72, "selected on day 6"),
    ("TAIL", "day 9–30", 503, "selected on day 9, then fixed"),
], columns=["segment", "period", "steps", "selection"])
display(fieldbook_table(tape_structure))


strategy_rules = pd.DataFrame([
    (6, 144, "first shop is Yarn", "YARN_ENGINE"),
    (6, 144, "second shop is Yarn; land gap < 0", "LAND_RECOVERY"),
    (6, 144, "otherwise", "BALANCED"),
    (9, 216, "BALANCED; cash gap < 0", "CASH_RECOVERY"),
    (9, 216, "third shop is Yarn", "YARN_LATE"),
    (9, 216, "land recovery; wheat is cheap", "WHEAT_RECOVERY"),
], columns=["day", "step", "visible condition", "plan"])
display(fieldbook_table(strategy_rules))


from importlib.metadata import version
from kaggle_environments import make

def play_pair(seed, fieldbook_seat):
    fixed = fieldbook.make_agent(branch_depth=0, sell_lead=False, terminal_liquidation=False)
    adaptive = fieldbook.make_agent(branch_depth=2, sell_lead=True, terminal_liquidation=True)
    agents = [adaptive, fixed] if fieldbook_seat == 0 else [fixed, adaptive]
    env = make("kaggriculture", configuration={"episodeSteps":720, "seed":seed}, debug=False)
    env.run(agents)
    rewards = [float(state.reward) for state in env.state]
    fieldbook_reward, fixed_reward = rewards[fieldbook_seat], rewards[1 - fieldbook_seat]
    point = 1.0 if fieldbook_reward > fixed_reward else 0.5 if fieldbook_reward == fixed_reward else 0.0
    return {"seed":seed, "seat":fieldbook_seat, "point":point, "margin":fieldbook_reward-fixed_reward}

required_engine = "1.32.7"
installed_engine = version("kaggle-environments")
if installed_engine != required_engine:
    print(
        f"SKIPPED: this image has kaggle-environments {installed_engine}; "
        f"the recorded comparison requires {required_engine}."
    )
else:
    demo_seeds = [390700001, 390700002]
    demo_rows = [play_pair(seed, seat) for seed in demo_seeds for seat in (0, 1)]
    demo = pd.DataFrame(demo_rows)
    display(demo)
    summary = {"games":len(demo), "point_rate":demo.point.mean(), "mean_margin":demo.margin.mean()}
    print(summary)


# Change one thing at a time, then compare on unused seeds.
experiments = {
    "fixed": fieldbook.make_agent(branch_depth=0, sell_lead=False, terminal_liquidation=False),
    "root_only": fieldbook.make_agent(branch_depth=1, sell_lead=False, terminal_liquidation=True),
    "full": fieldbook.make_agent(),
    "wheat_cheap_32": fieldbook.make_agent(wheat_cheap=32.0),
}
milestones = pd.DataFrame([
    (3, "observe shop 1", "continue the shared opening"),
    (6, "observe shop 2", "choose an intermediate plan"),
    (9, "observe shop 3", "choose the long tail"),
    (12, "shop 4 and beyond", "no reselection yet; next target"),
], columns=["day", "shop milestone", "current behavior"])
display(fieldbook_table(milestones))
print("change one rule, then evaluate on unused seeds:", list(experiments))


# Only this exact file is a submission candidate. Do not submit here.
from importlib.metadata import version
print("kaggle-environments:", version("kaggle-environments"))
print("submission candidate: main.py")
print("submission SHA-256:", artifact_sha256)
print("KAGGLE NOTEBOOK: yhay81/fieldbook-commit-for-three-days")
print("RELEASE ACTIONS: OUTSIDE THIS NOTEBOOK")
