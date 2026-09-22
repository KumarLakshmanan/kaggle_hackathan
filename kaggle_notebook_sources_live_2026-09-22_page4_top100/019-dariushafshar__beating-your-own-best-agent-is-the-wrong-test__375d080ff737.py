# A minimal panel scorer. Point AGENTS at your own modules and run.
# Every matchup plays BOTH seatings on a fixed seed set -- seat order matters in this game
# because market orders resolve in player order, so a one-sided test is a biased one.
import itertools, statistics

def play(make_a, make_b, seed, swap):
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([make_b(), make_a()] if swap else [make_a(), make_b()])
    f = env.steps[-1]
    i = 1 if swap else 0
    a, b = float(f[i].reward or 0), float(f[1-i].reward or 0)
    return 1.0 if a > b else (0.5 if a == b else 0.0)

def head_to_head(make_a, make_b, seeds):
    return statistics.mean(play(make_a, make_b, s, sw) for s in seeds for sw in (False, True))

def panel_table(agents, seeds):
    """agents: {name: zero-arg factory returning an agent callable}"""
    names = list(agents)
    grid = {a: {} for a in names}
    for a, b in itertools.permutations(names, 2):
        if b in grid[a]:
            continue
        w = head_to_head(agents[a], agents[b], seeds)
        grid[a][b], grid[b][a] = w, 1.0 - w
    print(f"{'agent':<16}" + "".join(f"{n[:9]:>11}" for n in names) + f"{'OVERALL':>11}")
    for a in sorted(names, key=lambda x: -statistics.mean(grid[x].values())):
        row = "".join(f"{grid[a].get(b, float('nan')):>10.0%} " if b != a else f"{'--':>11}"
                      for b in names)
        print(f"{a:<16}{row}{statistics.mean(grid[a].values()):>10.0%}")
    return grid

def best_covering_pair(grid, threshold=0.5):
    """The pair whose UNION beats the most panel members. NOTE (see the correction above):
    this is a PORTFOLIO hedge on E[max(rating_A, rating_B)] -- the two bots never help each
    other in any game. Coverage is a tiebreaker among individually strong pairs, not the
    selection criterion on its own."""
    names = list(grid)
    best = None
    for a, b in itertools.combinations(names, 2):
        covered = sum(1 for t in names if t not in (a, b)
                      and max(grid[a].get(t, 0), grid[b].get(t, 0)) > threshold)
        if best is None or covered > best[0]:
            best = (covered, a, b)
    print(f"\nbest covering pair: {best[1]} + {best[2]}  "
          f"(covers {best[0]} of {len(names)-2} other panel members)")
    return best

print("Ready. Build an AGENTS dict of factories and call panel_table(AGENTS, range(1000,1008)).")