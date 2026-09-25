"""Early strawberry-commitment omission diagnostic, not a submission agent.

At the first incumbent strawberry-seed purchase, use only the currently
visible shops. If none can consume strawberry, omit this whole seed/plant
cohort. Other labor and routes are deliberately unchanged. This is a lower-
bound ablation of the cash saved by avoiding the crop, not a complete planner:
unneeded workers may still be hired and attempt no-op tasks. Future shops,
replay identifiers, seeds, and opponent-private state are never inspected.
"""

from __future__ import annotations

import copy
import main as _base


STRAWBERRY_SHOPS = frozenset(
    ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET")
)
_state = {"decided": False, "omit": False}
_report = {"eligible": 0, "skipped_seed_units": 0, "skipped_plant_actions": 0}


def agent(observation, configuration=None):
    step = int(observation.get("step", -1))
    if step == 0:
        _state.update(decided=False, omit=False)
        _report.update(eligible=0, skipped_seed_units=0, skipped_plant_actions=0)

    action = _base.agent(observation, configuration)
    if not isinstance(action, dict):
        return action

    market = action.get("market") or []
    has_seed_buy = any(
        isinstance(order, (list, tuple)) and len(order) >= 3
        and order[:2] == ["BUY_SEED", "STRAWBERRY"] and int(order[2]) > 0
        for order in market
    )
    if has_seed_buy and not _state["decided"]:
        shops = tuple((observation.get("town") or {}).get("unlocked_shops") or ())
        _state["decided"] = True
        _state["omit"] = bool(shops) and not any(
            name in STRAWBERRY_SHOPS for name in shops
        )
        _report["eligible"] = int(_state["omit"])

    if not _state["omit"]:
        return action

    result = copy.deepcopy(action)
    kept = []
    for order in result.get("market") or []:
        if (isinstance(order, (list, tuple)) and len(order) >= 3
                and order[:2] == ["BUY_SEED", "STRAWBERRY"]):
            _report["skipped_seed_units"] += max(0, int(order[2]))
        else:
            kept.append(order)
    result["market"] = kept

    for slot in ("farmer",):
        command = result.get(slot)
        if isinstance(command, (list, tuple)) and command[:2] == ["PLANT", "STRAWBERRY"]:
            result[slot] = ["PASS"]
            _report["skipped_plant_actions"] += 1
    for index, command in enumerate(result.get("hands") or []):
        if isinstance(command, (list, tuple)) and command[:2] == ["PLANT", "STRAWBERRY"]:
            result["hands"][index] = ["PASS"]
            _report["skipped_plant_actions"] += 1
    return result


agent.telemetry = _report
kaggle_submission_agent = agent
