"""Standalone observation-legal late crop-swap experiment; not submitted."""

import importlib.util
from pathlib import Path
import sys
import time


SOURCE = Path(__file__).with_name("main.py")
MODULE_NAME = f"late_carrot_parent_{time.time_ns()}"
SPEC = importlib.util.spec_from_file_location(MODULE_NAME, SOURCE)
assert SPEC is not None and SPEC.loader is not None
INCUMBENT = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = INCUMBENT
SPEC.loader.exec_module(INCUMBENT)

ACTIVE = {}
STATS = {"activations": 0, "seed_orders_changed": 0,
         "plant_commands_changed": 0, "missed_skeleton": 0}


def _replace_seed(action: dict, source: str, quantity: int, target: str, new_quantity: int):
    market = [list(order) if isinstance(order, list) else order
              for order in (action.get("market") or [])]
    for order in market:
        if isinstance(order, list) and order == ["BUY_SEED", source, quantity]:
            order[1] = target
            order[2] = new_quantity
            STATS["seed_orders_changed"] += 1
            return dict(action, market=market)
    STATS["missed_skeleton"] += 1
    return action


def agent(observation, configuration=None):
    action = INCUMBENT.agent(observation, configuration)
    try:
        step = int(observation["step"])
        seat = int(observation["player"])
        if step == 0:
            ACTIVE[seat] = False
            for key in STATS:
                STATS[key] = 0
        if not INCUMBENT._ig_standard(configuration):
            return action
        if step == 652:
            market = action.get("market") or []
            money = float(observation["farms"][seat]["money"])
            eligible = (
                money >= 1000
                and any(isinstance(order, list) and order == ["BUY_SEED", "WHEAT", 2]
                        for order in market)
            )
            ACTIVE[seat] = eligible
            if eligible:
                STATS["activations"] += 1
        if not ACTIVE.get(seat, False):
            return action
        if step == 652:
            action = _replace_seed(action, "WHEAT", 2, "CARROT", 3)
        elif step in (653, 654):
            action = _replace_seed(action, "WHEAT", 1, "CARROT", 1)
        elif step in (656, 657, 658):
            farmer = list(action.get("farmer") or ["PASS"])
            hands = [list(order) for order in (action.get("hands") or [])]
            changed = 0
            for unit in [farmer, *hands]:
                if unit[:2] == ["PLANT", "WHEAT"]:
                    unit[1] = "CARROT"
                    changed += 1
            STATS["plant_commands_changed"] += changed
            if changed:
                action = dict(action, farmer=farmer, hands=hands)
            if step == 657:
                market = action.get("market") or []
                revised = [order for order in market
                           if not (isinstance(order, list)
                                   and order == ["BUY_SEED", "WHEAT", 2])]
                if len(revised) != len(market):
                    action = dict(action, market=revised)
                else:
                    STATS["missed_skeleton"] += 1
        state = INCUMBENT._RACE_STATE.get(seat)
        if state is not None and state.get("prev_action") is not None and state.get("step") == step:
            state["prev_action"] = action
        return action
    except Exception:
        STATS["missed_skeleton"] += 1
        return action


agent.telemetry = STATS
kaggle_submission_agent = agent
