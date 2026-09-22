import math
import statistics
from kaggle_environments import make

ENV = "kaggriculture"


def wilson(k, n, z=1.96):
    # 95% Wilson interval for k successes in n trials
    if n == 0:
        return 0.0, 1.0
    p = k / float(n)
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - s) / d), min(1.0, (c + s) / d)


def duel(agent_a, agent_b, pairs=20, base_seed=1000, verbose=True):
    # Each seed is played TWICE with the seats swapped, so the seating
    # advantage cancels within the pair instead of averaging out over it.
    wins = losses = ties = 0
    margins = []
    for i in range(pairs):
        seed = base_seed + i
        for seat in (0, 1):
            order = [agent_a, agent_b] if seat == 0 else [agent_b, agent_a]
            env = make(ENV, configuration={"seed": seed})
            env.run(order)
            money = [f["money"] for f in env.state[0]["observation"]["farms"]]
            a, b = money[seat], money[1 - seat]
            margins.append(a - b)
            if a > b:
                wins += 1
            elif a < b:
                losses += 1
            else:
                ties += 1
    n = 2 * pairs
    dec = wins + losses                      # decisive episodes
    lo, hi = wilson(wins, n)                 # ties treated as non-wins
    dlo, dhi = wilson(wins, dec) if dec else (0.0, 1.0)
    drate = wins / float(dec) if dec else float("nan")
    out = dict(n=n, pairs=pairs, wins=wins, losses=losses, ties=ties,
               decisive=dec, rate=wins / float(n), lo=lo, hi=hi,
               decisive_rate=drate, dlo=dlo, dhi=dhi,
               median_margin=statistics.median(margins))
    if verbose:
        print("  {:>3} episodes ({} seeds x 2 seats)".format(n, pairs))
        print("  win {:<3} loss {:<3} tie {:<3}".format(wins, losses, ties))
        print("  share of all episodes won : {:6.1%}   95% CI [{:.1%}, {:.1%}]"
              .format(out["rate"], lo, hi))
        if dec:
            print("  share of DECISIVE won    : {:6.1%}   95% CI [{:.1%}, {:.1%}]   (n={})"
                  .format(drate, dlo, dhi, dec))
        print("  median money margin {:+,.0f}".format(out["median_margin"]))
        # The separation verdict uses decisive episodes. A tie is not evidence
        # for either agent, and counting it against A would report a drawn
        # match-up as a loss.
        if not dec:
            print("  -> every episode was a tie: no separation possible")
        elif dlo <= 0.5 <= dhi:
            print("  -> decisive-game interval covers 50%: does NOT separate them")
        else:
            print("  -> decisive-game interval excludes 50%")
        if ties and dec:
            print("  -> {}/{} episodes were ties ({:.0%}). The first rate is dragged"
                  .format(ties, n, ties / float(n)))
            print("     down by them; the decisive rate is the one to read.")
        elif ties:
            print("  -> all {} episodes were ties, so there is no decisive rate to"
                  .format(n))
            print("     read. Two agents that always draw cannot be ranked by wins;")
            print("     compare the money margin, or change the match-up.")
    return out

print("{:>7}{:>11}{:>18}{:>30}".format(
    "seeds", "episodes", "95% CI at 50%", "smallest rate it separates"))
for pairs in (5, 10, 25, 50, 100, 250, 500):
    n = 2 * pairs
    lo, hi = wilson(n // 2, n)
    print("{:>7}{:>11}{:>18}{:>30}".format(
        pairs, n, "+/- {:.1%}".format((hi - lo) / 2), "{:.0%}".format(hi)))
print()
print("So 20 episodes cannot tell 50% from 70%, and 100 cannot tell 50% from")
print("60%. If you are comparing two versions of your own agent, assume you")
print("are in the close case and budget accordingly.")

PAIRS = 20   # 40 episodes per match-up; about a minute each

print("starter vs random")
r1 = duel("starter", "random", pairs=PAIRS)
print()
print("random vs pass")
r2 = duel("random", "pass", pairs=PAIRS)
print()
print("random vs random   (the rig measuring itself)")
r3 = duel("random", "random", pairs=PAIRS)

def my_agent(obs):
    # ---- YOUR AGENT HERE -------------------------------------------------
    # Anything the environment accepts. This placeholder does nothing, so
    # out of the box it behaves like the built-in "pass" agent.
    return []
    # ----------------------------------------------------------------------


print("my_agent vs starter")
mine = duel(my_agent, "starter", pairs=10)