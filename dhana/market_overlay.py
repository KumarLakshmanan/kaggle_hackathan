# Dhana live-observation improvements, 2026-09-22.
# No test seeds, replay identities or opponent private state are consulted.
_DHANA_BASE = agent
DHANA_OPENING_QUANTITY = 15
DHANA_SCAVENGE = True
_DHANA_STATS = {"idle_recoveries": 0, "overlay_errors": 0}


def _dhana_collect_idle(obs, action):
    """While trailing, replace redundant care with available extra production.

    Do not disrupt movement, planting, sale timing or useful care. Stop before
    the final liquidation phase and leave space for the normal delivery plan.
    """
    step = int(obs.get("step", 0))
    if not DHANA_SCAVENGE or not 72 <= step < 672:
        return action
    player = int(obs["player"])
    if obs["farms"][player]["money"] >= obs["farms"][1-player]["money"]:
        return action
    private = obs.get("private", {})
    carried = sum(sum(v.values()) for v in private.get("inventories", []))
    if sum(private.get("shed", {}).values()) + carried > 75:
        return action
    farm = obs["farms"][player]
    positions = [farm["farmer"], *farm.get("hands", [])]
    commands = [list(action.get("farmer", ["PASS"])),
                *[list(c) for c in action.get("hands", [])]]
    claimed = set()
    changed = 0
    for i, (position, command) in enumerate(zip(positions, commands)):
        x, y = position
        tile = farm["tiles"][y][x]
        if not isinstance(tile, dict) or (x, y) in claimed:
            continue
        op = command[0] if command else "PASS"
        noop = (op == "PASS" or (op == "CARE" and tile.get("cared_today"))
                or (op == "FEED" and tile.get("fed_today"))
                or (op == "WATER" and tile.get("watered_today")))
        if not noop:
            continue
        if tile.get("yield_units", 0) > 0 and (tile.get("animal") or tile.get("crop") in ("TOMATO", "STRAWBERRY")):
            commands[i] = ["HARVEST"]
        elif tile.get("animal") and tile.get("fertilizer_available"):
            commands[i] = ["COLLECT_FERTILIZER"]
        else:
            continue
        claimed.add((x, y))
        changed += 1
    if not changed:
        return action
    _DHANA_STATS["idle_recoveries"] += changed
    return dict(action, farmer=commands[0], hands=commands[1:])


def agent(observation, configuration=None):
    step = int(observation.get("step", 0))
    if step == 0:
        _DHANA_STATS.update(idle_recoveries=0, overlay_errors=0)
    action = _DHANA_BASE(observation, configuration)
    try:
        action = _dhana_collect_idle(observation, action)
        if DHANA_OPENING_QUANTITY and step == 0:
            original = action.get("market", [])
            if original[:2] == [["BUY_PRODUCT", "WHEAT", 20], ["SELL", "WHEAT", 15]]:
                quantity = max(5, min(60, int(DHANA_OPENING_QUANTITY)))
                market = [["BUY_PRODUCT", "WHEAT", quantity]]
                if quantity > 5:
                    market.append(["SELL", "WHEAT", quantity-5])
                # Net wheat and all subsequent orders (including seeds) stay intact.
                action = dict(action, market=market + original[2:])
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        _DHANA_STATS["overlay_errors"] += 1
    return action


agent.telemetry = _DHANA_STATS
