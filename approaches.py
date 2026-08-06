"""Local Kaggriculture candidate registry and controlled ablations."""

import main
from dynamic_agent import dynamic_agent
from submission_kaito_v20 import agent as kaito_v20_agent


def _step(obs):
    return min(
        max(0, int(main._get(obs, "step", 0) or 0)),
        len(main._ACTIONS) - 1,
    )


def _old_base(obs):
    return main._copy_action(main._ACTIONS[_step(obs)])


def old_raw(obs):
    """v21 route with only live hired-hand alignment."""
    return main._align_hands(_old_base(obs), obs)


def old_weed_only(obs):
    """v21 route plus visible weed transaction recovery."""
    step = _step(obs)
    return main._weed_repair_action(obs, _old_base(obs), step)


def old_preempt(obs):
    """v21 route with safe market ordering and public-state preemption."""
    step = _step(obs)
    action = main._weed_repair_action(obs, _old_base(obs), step)
    action = main._safe_market(obs, action)
    return main._preempt_action(obs, action, step)


def old_v21(obs):
    """Full promoted production policy."""
    return main.agent(obs)


def old_terminal(obs):
    """Safe/preemptive route with terminal liquidation enabled."""
    step = _step(obs)
    action = main._weed_repair_action(obs, _old_base(obs), step)
    action = main._safe_market(obs, action)
    action = main._preempt_action(obs, action, step)
    if step == 718:
        action = main._terminal_market(obs, action)
    return main._align_hands(action, obs)


def kaito_v20(obs):
    """Previously promoted Kaito v20 candidate, retained for comparison."""
    return kaito_v20_agent(obs)


def dynamic_baseline(obs):
    """The original schema-mismatched dynamic candidate."""
    return dynamic_agent(obs)


# Names used by the earlier benchmark notebook remain available.
route_raw = old_raw
route_safe = old_weed_only
route_memory = old_v21
route_memory_no_terminal = old_preempt
route_memory_terminal_all = old_terminal
route_terminal_day29 = old_terminal
route_reactive_maintenance = old_v21
route_all_cows = old_v21
route_two_cows = old_v21
route_four_cows = old_v21


CANDIDATES = {
    "dynamic_baseline": dynamic_baseline,
    "old_raw": old_raw,
    "old_weed_only": old_weed_only,
    "old_preempt": old_preempt,
    "old_v21": old_v21,
    "old_terminal": old_terminal,
    "kaito_v20": kaito_v20,
}
