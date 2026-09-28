"""Fund an incumbent-scheduled third-land production bundle by order priority.

The rule does not add a land, product, animal, seed, or worker order. It only
repositions an already scheduled third-quadrant BUY_LAND after all current
SELL orders when the installed market simulator projects a 500-coin reserve.
"""

import copy as _copy

import main as _base


_LAND_FUND_PARENT = _base.agent
_LAND_FUND_STATS = {
    "eligible_turns": 0,
    "activated_turns": 0,
    "activated_games": 0,
    "projection_errors": 0,
    "last_step": None,
    "last_projected_cash": None,
}


def _land_fund_project_cash_after_sales(observation, action, configuration):
    """Return exact own cash after this action's SELL orders, with no rival orders."""
    orders = action.get("market", []) or []
    land_indices = [i for i, order in enumerate(orders)
                    if order and order[0] == "BUY_LAND"]
    if len(land_indices) != 1:
        return None
    land_index = land_indices[0]
    sell_indices = [i for i, order in enumerate(orders)
                    if order and order[0] == "SELL"]
    if not sell_indices or any(i > land_index for i in sell_indices):
        return None

    sells = [list(orders[i]) for i in sell_indices]
    stock = _base._queue_stock(observation, action, configuration or {})
    own_cash, _rival_cash, _own_signature, _rival_signature = (
        _base._queue_simulate(
            observation, sells, [], stock, configuration or {}
        )
    )
    return float(own_cash)


def _land_fund_reorder(observation, action, configuration):
    step = int(observation.get("step", -1))
    if step < 0 or step >= 432:
        return action

    player = int(observation["player"])
    farm = observation["farms"][player]
    if len(farm.get("unlocked_quadrants", [])) != 2:
        return action

    orders = action.get("market", []) or []
    land_indices = [i for i, order in enumerate(orders)
                    if order and order[0] == "BUY_LAND"]
    if len(land_indices) != 1:
        return action
    land_index = land_indices[0]
    sell_count = sum(1 for order in orders if order and order[0] == "SELL")
    if sell_count == 0 or any(
        order and order[0] == "SELL" and i > land_index
        for i, order in enumerate(orders)
    ):
        return action
    if land_index == sell_count:
        return action

    _LAND_FUND_STATS["eligible_turns"] += 1
    projected_cash = _land_fund_project_cash_after_sales(
        observation, action, configuration
    )
    if projected_cash is None:
        return action
    _LAND_FUND_STATS["last_step"] = step
    _LAND_FUND_STATS["last_projected_cash"] = projected_cash
    if projected_cash < 2500.0:
        return action

    revised_orders = [list(order) if isinstance(order, (list, tuple)) else order
                      for order in orders]
    land_order = revised_orders.pop(land_index)
    revised_orders.insert(sell_count, land_order)
    action["market"] = revised_orders
    _LAND_FUND_STATS["activated_turns"] += 1
    _LAND_FUND_STATS["activated_games"] = 1
    return action


def agent(observation, configuration=None):
    if int(observation.get("step", -1)) == 0:
        for key in _LAND_FUND_STATS:
            if key == "last_step":
                _LAND_FUND_STATS[key] = None
            elif key == "last_projected_cash":
                _LAND_FUND_STATS[key] = None
            else:
                _LAND_FUND_STATS[key] = 0

    action = _copy.deepcopy(_LAND_FUND_PARENT(observation, configuration))
    try:
        return _land_fund_reorder(observation, action, configuration)
    except Exception:
        _LAND_FUND_STATS["projection_errors"] += 1
        return action


agent.telemetry = _LAND_FUND_STATS


def kaggle_production_bundle_landfund_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
