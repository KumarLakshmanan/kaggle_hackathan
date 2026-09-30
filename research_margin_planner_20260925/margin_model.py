"""Observation-only marginal *competitive* investment forecasts.

Known engine price/production helpers come from the independently tested
economics sidecar. Future work, sales timing, rival choices and shop draws are
approximations; this module does not claim an exact simulator continuation.
"""

from __future__ import annotations

from pathlib import Path
import sys

_PRIOR = Path(__file__).resolve().parents[1] / "research_dynamic_planner_20260925"
sys.path.insert(0, str(_PRIOR))
import economics as e


MODES = ("terminal_margin", "short_cycle")
SHORT_DAYS = 12


def _assets(observation, horizon, planned_counts):
    today = int(observation.get("day", 0))
    player = int(observation.get("player", 0))
    own, rival = e._empty(horizon), e._empty(horizon)
    for seat, farm in enumerate(observation["farms"]):
        target = own if seat == player else rival
        for row in farm["tiles"]:
            for tile in row:
                if (isinstance(tile, dict) and
                        (tile.get("animal") in e.ANIMALS or tile.get("crop") in e.CROPS)):
                    e._add(target, e._profile(tile, today, horizon))
    for item, quantity in (planned_counts or {}).items():
        if item in e.ANIMALS or item in e.CROPS:
            e._add(own, e._new_profile(item, today, horizon), quantity)
    return own, rival


def _future_demand(observation, configuration, horizon, scenario):
    today = int(observation.get("day", 0))
    tpd = int(configuration.get("turnsPerDay", 24))
    known = e.demand_per_day(observation, configuration)
    shop_rate = tpd / max(1, int(configuration.get("townShopSellInterval", 4)))
    mean_shop = {item: 0.0 for item in e.PRODUCTS}
    for products in e.SHOP_PRODUCTS.values():
        for item in products:
            mean_shop[item] += (
                shop_rate * (2 if len(products) == 1 else 1) /
                len(e.SHOP_PRODUCTS)
            )
    unlock_every = max(1, int(configuration.get("townShopUnlockInterval", 3)))
    remaining = max(0, 8 - len(observation.get("town", {}).get("unlocked_shops", [])))
    expected_new_shops = [
        min(remaining, (today+d)//unlock_every - today//unlock_every)
        for d in range(horizon)
    ]
    shop_scale = 1.0 if scenario == 0 else 0.5
    return {
        item: [known[item] + n*mean_shop[item]*shop_scale
               for n in expected_new_shops]
        for item in e.PRODUCTS
    }


def _project(item, observation, configuration, own, rival, project, demand,
             rival_scale):
    """Return incremental own cash and rival cash from one asset.

    Baseline and treatment stock evolve separately. A sale's effect on the
    rival is an *externality*, not the new asset's gross receipts. Negative
    WHEAT/FERTILIZER flows are purchases/inputs and receive negative cash.
    """
    inventory = observation["market"]["inventory"]
    overrides = configuration.get("marketParams")
    own_cash, rival_cash = 0.0, 0.0
    horizon = len(next(iter(project.values())))
    for product in e.PRODUCTS:
        baseline_stock = float(inventory[product])
        treatment_stock = baseline_stock
        for d in range(horizon):
            baseline_stock -= demand[product][d]
            treatment_stock -= demand[product][d]
            own_flow = own[product][d]
            rival_flow = rival_scale * rival[product][d]
            baseline_quote, baseline_stock = e._market_step(
                product, baseline_stock, own_flow+rival_flow, overrides)
            extra_flow = project[product][d]
            treatment_quote, treatment_stock = e._market_step(
                product, treatment_stock,
                own_flow+rival_flow+extra_flow, overrides)
            change = treatment_quote-baseline_quote
            own_cash += own_flow*change + extra_flow*treatment_quote
            rival_cash += rival_flow*change
    return own_cash, rival_cash


def investment_values(observation, configuration, planned_counts=None,
                      mode="terminal_margin"):
    if mode not in MODES:
        raise ValueError(f"Unknown investment mode {mode!r}")
    tpd = int(configuration.get("turnsPerDay", 24))
    today = int(observation.get("day", int(observation.get("step", 0))//tpd))
    last_day = (int(configuration.get("episodeSteps", 720))-2)//tpd
    full_horizon = last_day-today+1
    if full_horizon <= 1:
        return {}
    horizon = min(full_horizon, SHORT_DAYS) if mode == "short_cycle" else full_horizon
    own, rival = _assets(observation, horizon, planned_counts)
    demands = [_future_demand(observation, configuration, horizon, s)
               for s in (0, 1)]
    result = {}
    for item in tuple(e.CROPS)+tuple(e.ANIMALS):
        if item in e.ANIMALS:
            capital, first, interval, _cap, _product = e.ANIMALS[item]
            duration = horizon
            actions = 4.25+1/interval
            allowed = horizon > first+3
        else:
            capital, first, peak, interval, _cap = e.CROPS[item]
            duration = (first+3*interval+1 if interval else
                        (10 if item == "MELON" else peak)+1)
            actions = 1.4+(4/duration if interval else 2/duration)
            # Short-cycle mode demands a completed harvest-to-sale horizon.
            allowed = full_horizon >= duration and horizon >= duration
        if not allowed:
            result[item] = dict(score=-1e9, net=-capital, capital=capital,
                                horizon=duration, daily_actions=actions,
                                own_scenarios=[], rival_scenarios=[], output={})
            continue
        project = e._new_profile(item, today, horizon)
        own_scenarios, rival_scenarios, margin_scenarios = [], [], []
        for scenario, rival_scale in ((0, 1.0), (1, 1.2)):
            own_cash, rival_cash = _project(
                item, observation, configuration, own, rival, project,
                demands[scenario], rival_scale)
            own_net = own_cash-capital-4*actions*duration
            own_scenarios.append(own_net)
            rival_scenarios.append(rival_cash)
            margin_scenarios.append(own_net-rival_cash)
        # The cautious scenario assumes both more rival supply and fewer
        # future shop purchases; no future realization is read by the agent.
        own_net = .65*own_scenarios[0]+.35*min(own_scenarios)
        conservative_margin = .65*margin_scenarios[0]+.35*min(margin_scenarios)
        score = conservative_margin / max(1, duration)
        result[item] = dict(
            score=score, net=own_net, margin_net=conservative_margin,
            capital=capital, horizon=duration, daily_actions=actions,
            own_scenarios=own_scenarios, rival_scenarios=rival_scenarios,
            margin_scenarios=margin_scenarios,
            output={k: sum(v) for k, v in project.items() if sum(v)},
        )
    return result
