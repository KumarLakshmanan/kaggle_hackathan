def gate_headroom(wins, n, effect_pp=5.0):
    """How much room is left in a gate, and the smallest effect it can resolve.

    wins, n   : your current record on the gate
    effect_pp : the improvement you care about, in percentage points of win rate

    `room_up` is the number of games that could still flip your way. If the effect
    you are hunting is bigger than that, the gate literally cannot show it to you.
    """
    rate = wins / n
    room_up, room_down = n - wins, wins
    detectable = 100.0 * room_up / n
    # a rough two-sided resolution floor: one standard error of the win count
    se_pp = 100.0 * (rate * (1 - rate) / n) ** 0.5
    verdict = ("SATURATED - can only report regressions" if effect_pp > detectable else
               "coarse - the effect is near the gate's own noise" if effect_pp < se_pp else
               "usable")
    return {
        "win rate": f"{100 * rate:.0f}%",
        "games that can still flip up": room_up,
        "largest gain the gate can show": f"{detectable:.0f} pp",
        "one standard error": f"{se_pp:.1f} pp",
        "verdict": verdict,
    }


# my gate for three days, and the one that replaced it
for label, (w, n) in {"old gate": (58, 60), "added a 50% opponent": (77, 90)}.items():
    print(f"{label:24}", gate_headroom(w, n, effect_pp=5.0))