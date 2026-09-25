def channel_swap(policy_a, policy_b, play_season):
    """Play all four combinations of two policies' farm and market channels.

    policy_a, policy_b : callables taking an observation and returning
                         {"farmer": [...], "hands": [...], "market": [...]}
    play_season        : callable taking one such policy and returning final coins,
                         with the town and the opponent held fixed across calls

    Returns coins for each combination. Read the two mixed rows: if either is close to the
    all-A or all-B row, the channels are separable and per-turn imitation can work. If both
    collapse, the policy is one plan and copying it turn by turn will not reproduce it.
    """
    def mixed(farm_from, market_from):
        def policy(obs):
            f = farm_from(obs) or {}
            m = market_from(obs) or {}
            return {"farmer": f.get("farmer") or ["PASS"],
                    "hands": f.get("hands") or [],
                    "market": m.get("market") or []}
        return play_season(policy)

    return {
        "farm A, market A": play_season(policy_a),
        "farm A, market B": mixed(policy_a, policy_b),
        "farm B, market A": mixed(policy_b, policy_a),
        "farm B, market B": play_season(policy_b),
    }


def separability(result):
    """Share of the better pure policy that survives the better mix. Mine was 2%."""
    pure = max(result["farm A, market A"], result["farm B, market B"])
    mix = max(result["farm A, market B"], result["farm B, market A"])
    return mix / pure if pure else float("nan")


# My numbers, for calibration:
mine = {"farm A, market A": 2423, "farm A, market B": 0,
        "farm B, market A": 2317, "farm B, market B": 107726}
print(f"separability: {separability(mine):.1%}")