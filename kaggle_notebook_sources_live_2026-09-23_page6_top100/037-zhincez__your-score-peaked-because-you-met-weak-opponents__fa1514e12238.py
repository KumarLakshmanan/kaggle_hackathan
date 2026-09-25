from statistics import mean, median

BANDS = [(0, 1500), (1500, 1750), (1750, 2000), (2000, 2250), (2250, 10**9)]


def by_band(games, bands=BANDS):
    """games: iterable of (opponent_rating, won, coin_margin).

    Prints win rate per opponent-strength band. Compare two submissions inside the
    band that holds most of your games; the raw public score compares two different
    fields and cannot be read that way.
    """
    total = len(games)
    print(f"{'opponent rating':>18}{'games':>8}{'share':>8}{'win rate':>10}{'median margin':>16}")
    rows = []
    for lo, hi in bands:
        sel = [g for g in games if lo <= g[0] < hi]
        if not sel:
            continue
        w = sum(1 for g in sel if g[1])
        rows.append((lo, hi, len(sel), w, median(g[2] for g in sel)))
        label = f"{lo}-{hi}" if hi < 10**9 else f"{lo}+"
        print(f"{label:>18}{len(sel):>8}{100*len(sel)/total:>7.0f}%"
              f"{100*w/len(sel):>9.0f}%{rows[-1][4]:>16,.0f}")
    big = max(rows, key=lambda r: r[2])
    print()
    print(f"{100*big[2]/total:.0f}% of games are in the {big[0]}-{big[1]} band, "
          f"where you win {100*big[3]/big[2]:.0f}%.")
    print("That is the number to compare submissions on. Not the score, and never the peak.")


# a synthetic stand-in with the shape I measured, so the cell runs without the API:
# lopsided at both ends, a coin flip in the middle, and the middle holds most games.
import random
rng = random.Random(23)
games = ([(rng.uniform(1200, 1500), True, rng.uniform(20000, 50000)) for _ in range(18)]
         + [(rng.uniform(1500, 1750), True, rng.uniform(5000, 15000)) for _ in range(5)]
         + [(rng.uniform(1750, 2000), rng.random() < 0.51, rng.gauss(-670, 6000)) for _ in range(141)]
         + [(rng.uniform(2000, 2200), rng.random() < 0.11, rng.gauss(-6015, 4000)) for _ in range(9)])
by_band(games)

# To use your own, list your episodes and build the triples:
#   POST https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes
#        {"submissionId": <your submission id>}
# each episode carries both agents with `reward` and `initialScore`; take the agent
# whose submissionId is NOT yours as the opponent.