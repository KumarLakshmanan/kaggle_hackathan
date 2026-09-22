import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import comb
from pathlib import Path
from scipy import stats

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.6,
    "font.size": 9.5, "axes.titlesize": 11.5, "axes.titleweight": "bold",
    "axes.labelsize": 9.5, "legend.frameon": False,
    "lines.linewidth": 1.1, "lines.markersize": 4.0,
    "lines.solid_capstyle": "round", "axes.linewidth": 0.7,
    "xtick.major.width": 0.7, "ytick.major.width": 0.7, "patch.linewidth": 0.7,
})
INK, TEAL, AMBER, GREY, RED = "#0F172A", "#0F766E", "#B45309", "#94A3B8", "#B91C1C"

def find(name):
    for root in ("/kaggle/input", ".", "..", "data"):
        r = Path(root)
        if r.exists():
            for p in r.rglob(name):
                return p
    return None

WP = find("worked_example_paired.json")
if WP is None:
    raise FileNotFoundError(
        "worked_example_paired.json not found. Attach the dataset "
        "'destbreso/kaggriculture-benchmark-matchups' with Add Input, on the "
        "right of the editor, and make sure the version you attach is the "
        "latest one.")
W = json.loads(Path(WP).read_text())
G = pd.DataFrame(W["games"])
print(W["what"])
print()
for k in ("agent_A", "agent_B"):
    a = W[k]
    print(f"  {k[-1]}: an exact replay of {a['source']}, "
          f"episode {a['episode']}, seat {a['seat']}")
print(f"\n  {len(G)} games, {G.opponent.nunique()} distinct opponents, "
      f"seats {int((G.seat==0).sum())}/{int((G.seat==1).sum())}")

R = json.loads(Path(find("worked_example_routes.json")).read_text())

def make_replay_agent(route):
    '''Turn a recorded route into a player. This is the whole agent.'''
    PASS = {"farmer": ["PASS"], "hands": [], "market": []}

    def agent(obs):
        # DERIVE THE TURN, never read obs["step"]. Seat 1 receives a trimmed
        # observation with no `step` field: on the route below, 719 times out
        # of 719. Filling that absence with a default replays turn 0 forever.
        turn = int(obs["day"]) * 24 + int(obs["hour"])
        idx = turn + 1                    # a replay stores turn t at steps[t+1]
        if idx >= len(route):
            return dict(PASS)
        act = route[idx]
        if not isinstance(act, dict):
            return dict(PASS)
        return {"farmer": act.get("farmer") or ["PASS"],
                "hands": list(act.get("hands") or []),
                "market": list(act.get("market") or [])}
    return agent

agent_A = make_replay_agent(R["A"]["route"])
agent_B = make_replay_agent(R["B"]["route"])

rows = []
for k in ("A", "B"):
    r = R[k]
    rows.append({"agent": k, "donor": r["donor"], "rank": r["rank_at_capture"],
                 "rating at capture": r["rating_at_capture"], "turns": r["turns"],
                 "plan aligned": r["plan_aligned"],
                 "mutable turns": f"{r['mutable_turns']} ({r['mutable_share']})",
                 "medoid": r["medoid_similarity"]})
display(pd.DataFrame(rows))
for k in ("A", "B"):
    print(f"  {k}: {R[k]['source_field']}   sha256 {R[k]['sha256'][:16]}...")

import base64, hashlib, zlib

HEAD = [
 "# Kaggriculture agent: a pure replay of a recorded route. Lineage 7.R.",
 "#",
 "# ATTRIBUTION. The behaviour in this file is NOT ours and is not recovered",
 "# source. It is the observable action stream of a game played by {donor},",
 "# ranked {rank} at capture, taken from the competition's own public episode",
 "# API:",
 "#     {source}",
 "#     route sha256 {sha}",
 "#",
 "# WHAT IT DOES. It emits, at every turn, the action that team took at that",
 "# turn. It reads nothing, decides nothing, adapts to nothing.",
 "#",
 "# THE ONE TRAP. The turn is derived from day and hour and NEVER from",
 "# obs['step'], which is absent for seat 1 in a trimmed observation: on this",
 "# route, 719 times out of 719. Filling that absence with a default replays",
 "# turn 0 for the whole game, silently, and the agent still finishes every",
 "# episode looking perfectly healthy.",
 "import base64, json, zlib",
 "",
 "_BLOB = (",
]
TAIL = [
 ")",
 "ROUTE = json.loads(zlib.decompress(base64.b85decode(_BLOB)))",
 "PASS = {'farmer': ['PASS'], 'hands': [], 'market': []}",
 "",
 "",
 "def agent(obs):",
 "    turn = int(obs['day']) * 24 + int(obs['hour'])",
 "    idx = turn + 1",
 "    if idx >= len(ROUTE):",
 "        return dict(PASS)",
 "    act = ROUTE[idx]",
 "    if not isinstance(act, dict):",
 "        return dict(PASS)",
 "    return {'farmer': act.get('farmer') or ['PASS'],",
 "            'hands': list(act.get('hands') or []),",
 "            'market': list(act.get('market') or [])}",
 "",
]

for k in ('A', 'B'):
    r = R[k]
    raw = json.dumps(r['route'], separators=(',', ':')).encode()
    blob = base64.b85encode(zlib.compress(raw, 9)).decode()
    head = [h.format(donor=r['donor'], rank=r['rank_at_capture'],
                     source=r['source_field'],
                     sha=hashlib.sha256(raw).hexdigest()) for h in HEAD]
    body = ['    "%s"' % blob[i:i+100] for i in range(0, len(blob), 100)]
    src = "\n".join(head + body + TAIL)
    name = 'agent_%s_replay.py' % k
    Path(name).write_text(src)
    print('  wrote %-22s %6.1f kB   replays %s' % (name, len(src)/1024, r['donor']))

print()
print('  Standard library only. Drop one into a submission and it runs.')
print()
print('  ' + '-'*66)
print('  agent_A_replay.py, first lines and the shape of the rest:')
print('  ' + '-'*66)
preview = Path('agent_A_replay.py').read_text().splitlines()
for line in preview[:20]:
    print('  ' + line)
print('  ' + preview[20][:74] + ' ...')
print(f'  ... {len(preview)-24} more lines of route, then:')
for line in preview[-14:]:
    print('  ' + line)

G["A_margin"] = G.A_bank - G.A_opponent_bank
G["B_margin"] = G.B_bank - G.B_opponent_bank

def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z*z/n
    c = p + z*z/(2*n)
    h = z * np.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return (c-h)/d, (c+h)/d

rows = []
for name in ("A", "B"):
    w = int((G[f"{name}_margin"] > 0).sum())
    lo, hi = wilson(w, len(G))
    rows.append({"agent": name, "wins": f"{w}/{len(G)}",
                 "win rate": f"{100*w/len(G):.1f} %",
                 "95 % interval": f"[{100*lo:.1f} %, {100*hi:.1f} %]",
                 "median bank": f"{G[f'{name}_bank'].median():,.0f}"})
display(pd.DataFrame(rows))

wa = int((G.A_margin > 0).sum()); wb = int((G.B_margin > 0).sum())
tab = [[wa, len(G)-wa], [wb, len(G)-wb]]
print(f"Fisher exact on the two win counts: p = {stats.fisher_exact(tab)[1]:.3f}")
print("On this evidence the two agents are indistinguishable.")

print(f"  median margin, agent A   ${G.A_margin.median():>12,.0f}")
print(f"  median margin, agent B   ${G.B_margin.median():>12,.0f}")
print(f"  B wins by {G.B_margin.median()/G.A_margin.median():.2f} times as much, "
      f"on the same games")

G["paired"] = G.A_margin - G.B_margin
up = int((G.paired > 0).sum())
dn = int((G.paired < 0).sum())

def sign_test(up, dn):
    n = up + dn
    k = max(up, dn)
    return min(1.0, 2 * sum(comb(n, j) for j in range(k, n+1)) / 2**n)

print(f"  A ahead in       {up:>4} games")
print(f"  A behind in      {dn:>4} games")
print(f"  ties             {len(G)-up-dn:>4}")
print(f"  median of the paired difference   {G.paired.median():>+12,.0f}")
print(f"  sign test                         p = {sign_test(up, dn):.2e}")

fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.2))

ax = axes[0]
bins = np.linspace(min(G.A_margin.min(), G.B_margin.min()),
                   max(G.A_margin.max(), G.B_margin.max()), 34)
ax.hist(G.A_margin, bins=bins, color=TEAL, alpha=0.35, lw=0, label="agent A")
ax.hist(G.B_margin, bins=bins, histtype="step", color=AMBER, lw=1.2,
        label="agent B")
ax.axvline(0, color=GREY, lw=0.9)
ax.annotate("both are almost entirely\non the winning side of zero,\nwhich is why the win rates tie",
            xy=(0, ax.get_ylim()[1]*0.62), xytext=(14, 0),
            textcoords="offset points", fontsize=8.5, color=INK, va="center")
ax.set_xlabel("margin against the opponent, dollars"); ax.set_ylabel("games")
ax.xaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
ax.set_title("Counted separately: a tie against the ceiling", loc="left")
ax.legend(fontsize=8.5, loc="upper left")

ax = axes[1]
ax.hist(G.paired, bins=34, color=RED, alpha=0.35, lw=0)
ax.axvline(0, color=INK, lw=1.2)
ax.axvline(G.paired.median(), color=RED, lw=1.1, ls=(0, (4, 3)))
ax.annotate(f"median {G.paired.median():+,.0f}",
            xy=(G.paired.median(), ax.get_ylim()[1]*0.88), xytext=(-8, 0),
            textcoords="offset points", fontsize=9, color=RED, ha="right")
ax.set_xlabel("A minus B, on the same game, dollars"); ax.set_ylabel("games")
ax.xaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
ax.set_title(f"Differenced game by game: A behind in {dn} of {len(G)}", loc="left")
plt.tight_layout(); plt.show()

sa, sb = G.A_margin.std(ddof=1), G.B_margin.std(ddof=1)
sp, rho, n = G.paired.std(ddof=1), G.A_margin.corr(G.B_margin), len(G)
se_unpaired = np.sqrt(sa**2/n + sb**2/n)
se_paired = sp/np.sqrt(n)

print(f"  spread of A's margins    ${sa:>12,.0f}")
print(f"  spread of B's margins    ${sb:>12,.0f}")
print(f"  correlation between them  {rho:>+12.3f}")
print(f"  spread of the difference ${sp:>12,.0f}   "
      f"(algebra predicts ${np.sqrt(sa**2+sb**2-2*rho*sa*sb):,.0f})")
print()
print(f"  standard error on the mean difference")
print(f"    if the two runs were independent   ${se_unpaired:>10,.0f}")
print(f"    paired on the same games           ${se_paired:>10,.0f}")
print(f"    pairing is worth                    {se_unpaired/se_paired:>10.2f}x")
print()
# A ratio on the standard error converts to games by squaring it, because the
# error falls with the square root of the sample. Quote the games figure rather
# than the ratio, since the ratio invites being read as a saving in games.
print(f"  in games, which is what you actually spend:")
print(f"    200 independent games each carry as much information")
print(f"    as {200 * (se_paired/se_unpaired)**2:.0f} paired ones")

def sign_power(n, p, alpha=0.05):
    lo = stats.binom.ppf(alpha/2, n, 0.5) - 1
    hi = stats.binom.ppf(1-alpha/2, n, 0.5) + 1
    return float(stats.binom.cdf(lo, n, p) + stats.binom.sf(hi-1, n, p))

def n_for(p, target=0.80):
    return next((n for n in range(10, 20000) if sign_power(n, p) >= target), None)

obs = dn / (up + dn)
print(f"  observed paired rate: {100*obs:.1f} % of games favour one side")
print(f"  games needed to establish that at 80 % power: {n_for(obs)}")
print()
rows = []
for p in (0.55, 0.60, 0.65, 0.70, 0.74):
    n = n_for(p)
    rows.append({"a true paired rate of": f"{100*p:.0f} %",
                 "needs this many paired games": n,
                 "at 1.13 s a game": f"{2*n*1.13/60:.0f} min"})
display(pd.DataFrame(rows))

pa = float((G.A_margin > 0).mean())
pb = float((G.B_margin > 0).mean())
p_ = (pa + pb) / 2
za, zb = 1.96, 0.84                       # 5 % two-sided, 80 % power
n_wins = ((za*np.sqrt(2*p_*(1-p_)) + zb*np.sqrt(pa*(1-pa) + pb*(1-pb)))
          / (pa - pb))**2
discordant = int(((G.A_margin > 0) != (G.B_margin > 0)).sum())

print(f"  the two win rates differ by {100*(pa-pb):.2f} percentage points")
print(f"  games PER AGENT to establish that by counting wins: {n_wins:,.0f}")
print(f"  at 1.13 s a game, for both agents: {2*n_wins*1.13/3600:.1f} hours")
print()
print(f"  pairing does not rescue it either: only {discordant} of {len(G)} games")
print(f"  are discordant, one agent winning where the other lost, and a test on")
print(f"  {discordant} discordant pairs has no power at all")
print()
print(f"  switching to the margin instead: 35 paired games,")
print(f"  the same conclusion, {n_wins/35:,.0f} times cheaper")

BIG = pd.DataFrame(json.loads(Path(find("worked_example_paired_421.json")).read_text())["games"])
BIG["A_margin"] = BIG.A_bank - BIG.A_opponent_bank
BIG["B_margin"] = BIG.B_bank - BIG.B_opponent_bank
BIG["paired"] = BIG.A_margin - BIG.B_margin

rows = []
for label, df in (("112 games", G), ("421 games", BIG)):
    wa = int((df.A_margin > 0).sum()); wb = int((df.B_margin > 0).sum())
    u = int((df.paired > 0).sum()); d = int((df.paired < 0).sum())
    disc = int(((df.A_margin > 0) != (df.B_margin > 0)).sum())
    rows.append({"sample": label,
                 "A wins": f"{wa}/{len(df)}", "B wins": f"{wb}/{len(df)}",
                 "gap in win rate": f"{100*(wa-wb)/len(df):+.1f} pts",
                 "discordant games": disc,
                 "paired, A behind in": f"{d}/{u+d}",
                 "sign test p": f"{sign_test(u, d):.1e}"})
display(pd.DataFrame(rows))