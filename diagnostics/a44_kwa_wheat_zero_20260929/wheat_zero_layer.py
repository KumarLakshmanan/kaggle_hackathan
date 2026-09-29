"""Public, source-only kwa route splice at observation 72."""

_A44_KWA_WHEAT_ZERO_KEY = 'BRUNCH_SPOT|M8+|C<S|G0'
_A44_KWA_WHEAT_ZERO_ROUTE = 113535489
_A44_KWA_WHEAT_ZERO_PARENT = agent
_A44_KWA_WHEAT_ZERO_ACTIVE = False
_A44_KWA_WHEAT_ZERO_STATS = {
    'a44_kwa_wheat_zero_branch72': '',
    'a44_kwa_wheat_zero_key72': '',
    'a44_kwa_wheat_zero_rival_wheat_plots72': None,
    'a44_kwa_wheat_zero_active72': False,
    'a44_kwa_wheat_zero_route72': '',
    'a44_kwa_wheat_zero_turns': 0,
    'a44_kwa_wheat_zero_errors': 0,
}


def _a44_kwa_wheat_zero_plot_count(observation):
    rival = observation['farms'][1 - int(observation['player'])]
    return sum(
        1
        for row in rival['tiles']
        for tile in row
        if isinstance(tile, dict) and tile.get('crop') == 'WHEAT'
    )


def _a44_kwa_wheat_zero_active(step, bridge_branch, public_key, rival_wheat_plots):
    return (
        int(step) == 72
        and bridge_branch == 'source'
        and public_key == _A44_KWA_WHEAT_ZERO_KEY
        and int(rival_wheat_plots) == 0
    )


def _a44_kwa_wheat_zero_reset_state():
    global _A44_KWA_WHEAT_ZERO_ACTIVE
    _A44_KWA_WHEAT_ZERO_ACTIVE = False
    _A44_KWA_WHEAT_ZERO_STATS.update(
        a44_kwa_wheat_zero_branch72='',
        a44_kwa_wheat_zero_key72='',
        a44_kwa_wheat_zero_rival_wheat_plots72=None,
        a44_kwa_wheat_zero_active72=False,
        a44_kwa_wheat_zero_route72='',
        a44_kwa_wheat_zero_turns=0,
        a44_kwa_wheat_zero_errors=0,
    )


def _a44_kwa_wheat_zero_commit():
    # Reuse the frozen 6d source-map helper. It writes BRUNCH descendants and
    # the BRUNCH fallback; it does not change the Smoothie or FARMICE branch.
    _a44_goose4_commit(_A44_KWA_WHEAT_ZERO_KEY, _A44_KWA_WHEAT_ZERO_ROUTE)


def agent(observation, configuration=None):
    global _A44_KWA_WHEAT_ZERO_ACTIVE
    step = int(observation['step'])
    bridge_branch = _BRIDGE_SELECTED
    if step == 0:
        # The frozen 6d parent resets the route map and FARMICE state in its
        # unconditional call below. This wrapper resets only its own telemetry.
        _a44_kwa_wheat_zero_reset_state()
    if step == 72:
        key = ''
        wheat_plots = None
        if bridge_branch == 'source':
            key = _a44_goose4_key(observation)
            wheat_plots = _a44_kwa_wheat_zero_plot_count(observation)
        _A44_KWA_WHEAT_ZERO_STATS.update(
            a44_kwa_wheat_zero_branch72=bridge_branch,
            a44_kwa_wheat_zero_key72=key,
            a44_kwa_wheat_zero_rival_wheat_plots72=wheat_plots,
        )
        if _a44_kwa_wheat_zero_active(step, bridge_branch, key, wheat_plots or 0):
            try:
                _a44_kwa_wheat_zero_commit()
                _A44_KWA_WHEAT_ZERO_ACTIVE = True
                _A44_KWA_WHEAT_ZERO_STATS.update(
                    a44_kwa_wheat_zero_active72=True,
                    a44_kwa_wheat_zero_route72=str(_A44_KWA_WHEAT_ZERO_ROUTE),
                )
            except Exception:
                _A44_KWA_WHEAT_ZERO_STATS['a44_kwa_wheat_zero_errors'] += 1

    # Keep the integrated parent path unconditional and single-call. Outside
    # the exact step-72 predicate, this wrapper does not mutate its action.
    result = _A44_KWA_WHEAT_ZERO_PARENT(observation, configuration)
    if step >= 72 and _A44_KWA_WHEAT_ZERO_ACTIVE:
        _A44_KWA_WHEAT_ZERO_STATS['a44_kwa_wheat_zero_turns'] += 1
    agent.telemetry.update(getattr(_A44_KWA_WHEAT_ZERO_PARENT, 'telemetry', {}))
    agent.telemetry.update(_A44_KWA_WHEAT_ZERO_STATS)
    return result


agent.telemetry = {}


def kaggle_a44_kwa_wheat_zero_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
