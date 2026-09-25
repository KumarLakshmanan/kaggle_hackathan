# WHAT: play one agent on identical boards against a barely-trading opponent and
# against a fully-trading one, and compare its bank.
# WHY: if the two numbers differ a lot, every result you have ever measured
# against a non-trading opponent is about a different economy.
from kaggle_environments import make

SEEDS = [11, 23, 57, 91]          # fixed so both conditions see identical boards


def bank_of(agent, opponent, seeds):
    '''Mean bank for `agent` in seat 0, over `seeds`. Same boards every time.'''
    out = []
    for s in seeds:
        env = make("kaggriculture",
                   configuration={"episodeSteps": 720, "seed": s}, debug=False)
        env.run([agent, opponent])
        out.append(env.steps[-1][0]["reward"])   # seat 0 final coins
    return sum(out) / len(out)


# `random` places few sensible orders, so the market stays nearly uncontested.
uncontested = bank_of("starter", "random", SEEDS)
# `starter` vs itself: both sides sell into the same book on the same schedule.
contested = bank_of("starter", "starter", SEEDS)

print("uncontested (vs random) mean bank %.0f" % uncontested)
print("contested   (vs self)   mean bank %.0f" % contested)

# IMPORTANT: the built-in `starter` barely farms -- it finishes near the 3000
# starting money -- so it has almost nothing to sell and cannot move prices.
# The gap only appears for an agent that actually trades. Swap your own in.
if uncontested < 2 * 3000:
    print("`starter` banks near the 3000 start: too weak to contest anything.")
    print("substitute your own agent above -- mine showed 121k vs 81k on real boards.")
else:
    print("gap %.0f (%.0f%%)" % (uncontested - contested,
                                 100.0 * (uncontested - contested) / uncontested))

# WHAT: pull your own ladder episodes -- per-agent reward, opponent rating, board seed.
# WHY: these are the ground truth you validate a local harness against. Without
# them you are comparing your simulator to your simulator.
import json, os, urllib.request

API = "https://www.kaggle.com/api/i/competitions.EpisodeService/"


def _token():
    '''Bearer token from ~/.kaggle/access_token, or None if unavailable.'''
    p = os.path.expanduser("~/.kaggle/access_token")
    if not os.path.exists(p):
        return None
    raw = open(p).read().strip()
    try:
        return json.loads(raw).get("access_token") or json.loads(raw).get("token")
    except Exception:
        return raw                      # older tokens are stored bare


def call(method, body, token):
    req = urllib.request.Request(
        API + method, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0",
                 "Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def my_episodes(submission_id, token):
    '''(opponent_rating, my_bank, their_bank) per completed episode.'''
    out = []
    for e in call("ListEpisodes", {"submissionId": submission_id}, token)["episodes"]:
        if e.get("state") != "COMPLETED":
            continue
        me = [a for a in e["agents"] if a.get("submissionId") == submission_id]
        op = [a for a in e["agents"] if a.get("submissionId") != submission_id]
        if me and op and me[0].get("reward") is not None:
            out.append((op[0].get("initialScore"), me[0]["reward"], op[0]["reward"]))
    return out


tok = _token()
if tok is None:
    print("no ~/.kaggle/access_token here -- run this locally with your own token")
    print("then: my_episodes(<your submission id>, tok)")
else:
    print("token found; call my_episodes(<your submission id>, tok)")

# WHAT: given two agents' results on the SAME boards, report both deltas.
# WHY: margin and win rate can point at different agents. Print both, decide on
# the one the competition actually pays for -- here, win rate.
def paired_deltas(a, b):
    '''a, b: {board_key: (my_bank, their_bank)} measured on identical boards.'''
    shared = sorted(set(a) & set(b))
    if not shared:
        return None
    win = lambda r: 1.0 if r[0] > r[1] else 0.0        # noqa: E731
    dwin = sum(win(a[k]) - win(b[k]) for k in shared) / len(shared)
    dmar = sum((a[k][0] - a[k][1]) - (b[k][0] - b[k][1]) for k in shared) / len(shared)
    return {"n": len(shared), "dwin_pp": 100.0 * dwin, "dmargin": dmar}


# A worked example built to the shape my real pair had: B wins more games,
# A banks more per game. 50 boards so a 6 pp difference is representable.
A, B = {}, {}
for i in range(50):
    if i < 43:                       # both win: A wins by more
        A[i], B[i] = (110500, 90000), (108000, 90000)
    elif i < 46:                      # close ones B converts and A does not
        A[i], B[i] = (94000, 95000), (96000, 95000)
    else:                             # both lose
        A[i], B[i] = (80000, 99000), (80000, 99000)
d = paired_deltas(B, A)
print("B vs A on %d identical boards: dwin %+.1f pp, dmargin %+.0f"
      % (d["n"], d["dwin_pp"], d["dmargin"]))
print("margin prefers A; win rate prefers B; Bradley-Terry pays for B")

# WHAT: paired A/B harness. Same boards, same opponents, both seats, bootstrap CI.
# WHY: an unpaired comparison on 24 boards has a confidence interval so wide it
# will confirm whatever you hoped. Pairing is what buys resolution.
import random
from kaggle_environments import make


def play(agent, opponent, seed, seat):
    '''One episode; returns (agent_bank, opponent_bank). `seat` 0 or 1.'''
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([agent, opponent] if seat == 0 else [opponent, agent])
    final = env.steps[-1]
    return final[seat]["reward"], final[1 - seat]["reward"]


def evaluate(agent, opponents, seeds):
    '''Play every (seed, opponent, seat). The key identifies the board exactly,
    so two agents' results line up for pairing.'''
    return {"%s|%s|%d" % (op, s, seat): play(agent, op, s, seat)
            for s in seeds for op in opponents for seat in (0, 1)}


def bootstrap(deltas, iters=4000, seed=12345):
    '''95% CI of the mean of `deltas` by resampling with replacement.'''
    rnd, n, means = random.Random(seed), len(deltas), []
    for _ in range(iters):
        means.append(sum(deltas[rnd.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return means[int(0.025 * iters)], means[int(0.975 * iters)]


def compare(cand, base, opponents, seeds):
    '''Win-rate delta of `cand` over `base`, with a CI, on identical boards.'''
    ca, ba = evaluate(cand, opponents, seeds), evaluate(base, opponents, seeds)
    keys = sorted(set(ca) & set(ba))
    win = lambda r: 1.0 if r[0] > r[1] else 0.0        # noqa: E731
    dw = [win(ca[k]) - win(ba[k]) for k in keys]
    lo, hi = bootstrap(dw)
    mean = sum(dw) / len(dw)
    # a change worth under half a point of win rate is noise however tight the CI
    verdict = ("no material difference" if abs(mean) < 0.005 else
               "BETTER" if lo > 0 else "WORSE" if hi < 0 else "not significant")
    return {"n": len(keys), "dwin_pp": 100.0 * mean,
            "ci": (100.0 * lo, 100.0 * hi), "verdict": verdict}


# Demo: `starter` against itself is a true null -- the harness should say so.
r = compare("starter", "starter", ["random"], [11, 23])
print("null check: n=%d dwin %+.1f pp ci [%+.1f, %+.1f] -> %s"
      % (r["n"], r["dwin_pp"], r["ci"][0], r["ci"][1], r["verdict"]))

# WHAT: detect agents that silently fail into all-PASS instead of playing.
# WHY: their own try/except hides the exception, and the resulting bank reads as
# a strategy result rather than a crash.
from kaggle_environments import make

START_MONEY = 3000


def broken_agent(obs, config=None):
    '''Deliberately broken: throws every turn, swallows it, returns PASS.'''
    try:
        raise ValueError("pretend this is an index bug you have not noticed")
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}


def _is_pass(action):
    '''True if this turn did nothing at all.'''
    if not action:
        return True
    return (action.get("farmer") in (None, ["PASS"])
            and not action.get("hands") and not action.get("market"))


def is_alive(agent, seed=11):
    '''Count turns on which the agent actually did something.

    Checking ACTIONS rather than final bank matters: a weak-but-real agent can
    finish near the starting money too, and a bank threshold would call it dead.
    '''
    env = make("kaggriculture",
               configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([agent, "random"])
    acts = [s[0].get("action") for s in env.steps[1:]]
    active = sum(1 for a in acts if not _is_pass(a))
    return active, env.steps[-1][0]["reward"]


for name, ag in (("broken_agent", broken_agent), ("starter", "starter")):
    active, bank = is_alive(ag)
    print("%-13s acted on %3d of 719 turns, bank %8.0f  %s"
          % (name, active, bank,
             "NOT PLAYING (all-PASS)" if active == 0 else "ok"))

# WHAT: bucket your episodes by opponent rating and report win rate per band.
# WHY: the headline score mixes easy early games with hard later ones. The band
# where you hover near 50% is your real level; everything else is history.
BANDS = [(0, 1500), (1500, 1750), (1750, 2000), (2000, 2250), (2250, 10 ** 9)]


def by_band(episodes):
    '''episodes: (opponent_rating, my_bank, their_bank) -- see section 3.'''
    rows = []
    for lo, hi in BANDS:
        sel = [e for e in episodes if e[0] is not None and lo <= e[0] < hi]
        if not sel:
            continue
        wins = sum(1 for _, mine, theirs in sel if mine > theirs)
        margin = sum(mine - theirs for _, mine, theirs in sel) / len(sel)
        rows.append((lo, hi, len(sel), 100.0 * wins / len(sel), margin))
    return rows


# One of my own converged submissions, 270 episodes, reconstructed to its real
# per-band win rates. It had stopped climbing and was sliding: at the band
# holding most of its games it was winning 42%, not 50%.
def _band(rating, n, win_pct, won, lost):
    '''n episodes at `rating`, `win_pct` of them wins.'''
    w = round(n * win_pct / 100.0)
    return [(rating,) + won] * w + [(rating,) + lost] * (n - w)


example = (_band(1400, 17, 76, (120000, 80000), (70000, 99000))
           + _band(1600, 185, 42, (99000, 95000), (92000, 96000))
           + _band(1850, 67, 28, (97000, 93000), (90000, 95000))
           + _band(2100, 1, 0, (88000, 80000), (88000, 92800)))
for lo, hi, n, win, margin in by_band(example):
    print("band %5d-%-8d n=%-4d win %3.0f%%  margin %+8.0f" % (lo, hi, n, win, margin))
print("50% at your own band means converged; below means the field moved past you")

