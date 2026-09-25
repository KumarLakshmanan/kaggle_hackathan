SUBMISSION_ID = 56148474   # <- YOUR submission id here. The default is one of mine,
                           # for the reason in the note above. "RANK:n" reads whoever
                           # sits at rank n right now, resolved when you run it, and
                           # "KING" is RANK:1.
MAX_EPISODES  = 40       # newest first. Each replay is ~25 MB, so this is the slow part.
FAMILY_GATE   = None     # None = read the threshold off your own data (recommended)

import json, collections, statistics as st
import requests
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

LIST_URL   = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{id}.json"
FAM, OUT, GRID, MUTED = "#C2410C", "#0F172A", "#EEF2F7", "#64748B"


def style(ax, title, sub=None):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#CBD5E1")
    ax.tick_params(labelsize=8.5, colors=MUTED, length=3)
    ax.grid(axis="y", color=GRID, lw=1.0)
    ax.set_axisbelow(True)
    ax.set_title(title, fontsize=11, loc="left", pad=18 if sub else 10,
                 color="#0F172A", fontweight="bold")
    if sub:
        ax.annotate(sub, xy=(0, 1.03), xycoords="axes fraction",
                    fontsize=8.8, color=MUTED, va="bottom")


def reading(text):
    print("\n   READING: " + text + "\n")


def leaderboard():
    r = requests.post("https://www.kaggle.com/api/i/competitions.LeaderboardService/GetLeaderboard",
                      json={"competitionId": 147734}, timeout=30)
    return r.json()["publicLeaderboard"]


def resolve_rank(n):
    """The submission sitting at rank n right now, read from the public
    leaderboard. A rank is a timestamp rather than a property, so this is
    whoever is there at the moment you run it, not a fixed agent."""
    rows = leaderboard()
    row = rows[min(max(1, n), len(rows)) - 1]
    print(f"rank {n} right now: {row.get('teamName', '?')} at {row.get('displayScore')}, "
          f"submission {row['submissionId']}")
    return int(row["submissionId"])


_sid = str(SUBMISSION_ID).upper()
if _sid == "KING":
    SUBMISSION_ID = resolve_rank(1)
elif _sid.startswith("RANK:"):
    SUBMISSION_ID = resolve_rank(int(_sid.split(":")[1]))
SUBMISSION_ID = int(SUBMISSION_ID)


def episodes(sub):
    r = requests.post(LIST_URL, json={"submissionId": sub}, timeout=30).json()
    out = []
    for e in r.get("episodes", []):
        if e.get("state") != "COMPLETED" or e.get("type") != "EPISODE_TYPE_PUBLIC":
            continue
        me = next((a for a in e["agents"] if a.get("submissionId") == sub), None)
        op = next((a for a in e["agents"] if a.get("submissionId") != sub), None)
        if not me or not op:
            continue
        out.append({"id": e["id"], "end": e.get("endTime", ""),
                    "mine": me.get("reward") or 0, "theirs": op.get("reward") or 0,
                    "opp_sub": op.get("submissionId"),
                    "opp_score": op.get("updatedScore"), "my_score": me.get("updatedScore")})
    out.sort(key=lambda x: x["end"], reverse=True)
    return out


PASS = {"farmer": ["PASS"], "hands": [], "market": []}


MY_TEAM = None          # learned from the first decided game, used to settle draws


def pull(ep):
    """Both streams of one episode, from my seat's point of view."""
    global MY_TEAM
    r = requests.get(REPLAY_URL.format(id=ep["id"]), timeout=90).json()
    steps = r["steps"]
    names = (r.get("info") or {}).get("TeamNames") or ["", ""]
    rewards = r.get("rewards") or []
    # the seat is the one whose final reward matches the one the listing credits
    # to me: the agents array is not seat order. A DRAWN game cannot be settled
    # that way, so the team name learned from a decided game settles it instead.
    if len(rewards) == 2 and round(rewards[0]) != round(rewards[1]):
        seat = 0 if round(rewards[0]) == round(ep["mine"]) else 1
        if MY_TEAM is None and seat < len(names):
            MY_TEAM = names[seat]
    elif MY_TEAM in names:
        seat = names.index(MY_TEAM)
    else:
        raise ValueError("drawn game and my team name not learned yet")
    them = 1 - seat
    mine = [steps[t + 1][seat].get("action") or dict(PASS) for t in range(len(steps) - 1)]
    theirs = [steps[t + 1][them].get("action") or dict(PASS) for t in range(len(steps) - 1)]
    return mine, theirs, names[them] if them < len(names) else ""


eps = episodes(SUBMISSION_ID)[:MAX_EPISODES]
print(f"submission {SUBMISSION_ID}: {len(eps)} recent episodes, "
      f"{sum(1 for e in eps if e['mine'] > e['theirs'])} won, "
      f"{sum(1 for e in eps if e['mine'] < e['theirs'])} lost")

games = []
# decided games first: a draw cannot tell us which seat was ours, and by the
# time we reach one the team name has been learned from a decided game
for i, e in enumerate(sorted(eps, key=lambda x: x["mine"] == x["theirs"])):
    try:
        mine, theirs, opp_name = pull(e)
    except Exception as exc:
        print(f"  episode {e['id']}: {type(exc).__name__}")
        continue
    games.append({**e, "mine_acts": mine, "their_acts": theirs, "opp": opp_name})
    if (i + 1) % 10 == 0:
        print(f"  {i+1}/{len(eps)} replays read")
print(f"{len(games)} replays in hand")


def opening_agreement(a, b, upto=144):
    n = min(len(a), len(b), upto)
    return sum(1 for t in range(n) if a[t] == b[t]) / n if n else 0.0


for g in games:
    g["agree"] = opening_agreement(g["mine_acts"], g["their_acts"])

vals = sorted(g["agree"] for g in games)
gap, cut = 0.0, 0.5
for i in range(1, len(vals)):
    if vals[i] - vals[i - 1] > gap:
        gap, cut = vals[i] - vals[i - 1], (vals[i] + vals[i - 1]) / 2
CUT = FAMILY_GATE if FAMILY_GATE is not None else cut
bimodal = gap >= 0.25
for g in games:
    g["family"] = g["agree"] >= CUT
kin = [g for g in games if g["family"]]

fig, ax = plt.subplots(figsize=(9.4, 3.2))
ax.hist([g["agree"] for g in games if not g["family"]], bins=25, range=(0, 1),
        color=OUT, alpha=0.9, label="outside your lineage")
ax.hist([g["agree"] for g in games if g["family"]], bins=25, range=(0, 1),
        color=FAM, alpha=0.95, label="your lineage")
ax.axvline(CUT, color=MUTED, lw=1.4, ls=(0, (4, 3)))
ax.annotate(f"line at {CUT:.2f}", (CUT, ax.get_ylim()[1] * 0.92), fontsize=8.5,
            color=MUTED, ha="right" if CUT > 0.5 else "left",
            xytext=(-6 if CUT > 0.5 else 6, 0), textcoords="offset points")
style(ax, "How much of your opening each rival plays",
      f"turns 0-143, one bar per rival. The widest empty band in this distribution is "
      f"{gap:.2f} wide, and the line sits in it.")
ax.set_xlabel("agreement with my actions, turns 0-143", fontsize=9)
ax.set_ylabel("opponents", fontsize=9)
ax.legend(frameon=False, fontsize=8.5)
plt.tight_layout(); plt.show()

if not bimodal:
    reading(f"your opponents do NOT separate into two clouds (widest gap {gap:.2f} < 0.25), "
            "so treat the split below as a convenience rather than a measurement.")
else:
    reading(f"{len(kin)} of {len(games)} recent opponents play your opening, and the two "
            f"groups are cleanly separated: the nearest stranger agrees with you "
            f"{max([g['agree'] for g in games if not g['family']] or [0]):.0%} of the time, "
            f"the most distant relative {min([g['agree'] for g in kin] or [0]):.0%}.")


wins = [g for g in games if g["mine"] > g["theirs"]]
losses = [g for g in games if g["mine"] < g["theirs"]]
lf = [g for g in losses if g["family"]]
lo = [g for g in losses if not g["family"]]

fig, ax = plt.subplots(figsize=(9.4, 4.6))
for grp, colour, lab, mk, sz in ((wins, "#94A3B8", "games I won", "o", 38),
                                 (lo, OUT, "defeats, outside my lineage", "X", 70),
                                 (lf, FAM, "defeats, to my own lineage", "X", 70)):
    if grp:
        ax.scatter([g["agree"] for g in grp], [g["mine"] - g["theirs"] for g in grp],
                   s=sz, color=colour, alpha=0.85, marker=mk, linewidths=0, label=lab)
ax.axhline(0, color="#94A3B8", lw=1)
ax.axvline(CUT, color=MUTED, lw=1.2, ls=(0, (4, 3)))
ax.annotate("strangers", (CUT * 0.5, ax.get_ylim()[1] * 0.93), fontsize=9,
            color=MUTED, ha="center")
ax.annotate("your lineage", ((CUT + 1) / 2, ax.get_ylim()[1] * 0.93), fontsize=9,
            color=FAM, ha="center")
style(ax, "Every game, by how close the rival is to you",
      "one dot per episode; crosses are defeats")
ax.set_xlabel("how much of my opening the rival plays", fontsize=9)
ax.set_ylabel("my margin at the bell", fontsize=9)
ax.legend(frameon=False, fontsize=8.5, loc="upper center",
          bbox_to_anchor=(0.5, -0.16), ncol=3)
plt.tight_layout(); plt.show()

# with no two clouds there is no lineage to split by, and the lines below
# would be describing one cloud cut down the middle
near = [abs(g["mine"] - g["theirs"]) for g in games if g["family"]] if bimodal else []
far = [abs(g["mine"] - g["theirs"]) for g in games if not g["family"]] if bimodal else []
if not bimodal:
    reading("section 2 found no two clouds, so nothing here is a relative and this "
            "chart is one cloud with a line through it. Read the dots, ignore the "
            "colours.")
elif near and far:
    ratio = st.median(far) / max(st.median(near), 1)
    if ratio >= 1.4:
        reading(f"closeness DOES compress your games: a game against your lineage is decided "
                f"by a median of ${st.median(near):,.0f} against ${st.median(far):,.0f} "
                f"elsewhere, {ratio:.1f}x wider. An edge worth a few hundred dollars is "
                f"noise against strangers and decisive against relatives.")
    elif ratio <= 0.7:
        reading(f"the opposite of the usual pattern: your lineage games are the WIDE ones "
                f"(${st.median(near):,.0f} against ${st.median(far):,.0f}). Something about "
                f"your plan separates hard from its own relatives.")
    else:
        reading(f"closeness does not change the size of your games much "
                f"(${st.median(near):,.0f} against ${st.median(far):,.0f}). The interesting "
                f"split for you is by OUTCOME rather than by kinship, below.")
if losses and bimodal:
    print(f"   defeats: {len(losses)} of {len(games)} games, {len(lf)} to your lineage "
          f"and {len(lo)} to outsiders")
elif losses:
    print(f"   defeats: {len(losses)} of {len(games)} games")
    if bimodal and lf and lo:
        mf = st.median([g["mine"] - g["theirs"] for g in lf])
        mo = st.median([g["mine"] - g["theirs"] for g in lo])
        print(f"   median defeat: {mf:+,.0f} to relatives, {mo:+,.0f} to outsiders")
        if lf and wins:
            wf = [g["mine"] - g["theirs"] for g in wins if g["family"]]
            if wf:
                print(f"   and when you BEAT a relative you take {st.median(wf):+,.0f}: "
                      f"the asymmetry, not the spread, is where your money is")


REVEALS = [72, 144, 216, 288, 360, 432, 504, 576]
WIN = 48          # window for the moving agreement: wide enough that a
                  # single repaired turn does not read as a departure
FLOOR, RECOVER = 0.5, 0.8


def agreement_curve(a, b, w=WIN):
    n = min(len(a), len(b))
    return [(t, sum(1 for k in range(t, min(t + w, n)) if a[k] == b[k]) / min(w, n - t))
            for t in range(0, n - 1, w // 2)]


def departure(curve):
    """The first window whose agreement drops below FLOOR and never recovers
    above RECOVER afterwards: a parting of ways rather than a blip."""
    for i, (t, v) in enumerate(curve):
        if v < FLOOR and all(v2 <= RECOVER for _, v2 in curve[i + 1:]):
            return t
    return None


for g in lf:
    g["curve"] = agreement_curve(g["mine_acts"], g["their_acts"])
    g["left_at"] = departure(g["curve"])

if lf:
    fig, ax = plt.subplots(figsize=(9.4, 4.0))
    ax.axvspan(0, 72, color="#FEF3C7", alpha=0.75, lw=0)
    for r in REVEALS:
        ax.axvline(r, color="#E2E8F0", lw=1)
    for g in lf:
        xs = [t for t, _ in g["curve"]]; ys = [v for _, v in g["curve"]]
        ax.plot(xs, ys, color=FAM, alpha=0.55, lw=1.6)
        if g["left_at"] is not None:
            ax.scatter([g["left_at"]], [dict(g["curve"]).get(g["left_at"], 0)],
                       s=46, color=FAM, zorder=5, linewidths=0)
    ax.axhline(FLOOR, color=MUTED, lw=1, ls=(0, (4, 3)))
    ax.annotate("departure line", (720, FLOOR), fontsize=8, color=MUTED,
                ha="right", va="bottom")
    ax.annotate("nothing to react to yet:\na difference here is\na different OPENING",
                (76, 0.30), fontsize=8, color="#92400E", ha="left")
    for r in REVEALS:
        ax.annotate(str(r), (r, 1.03), fontsize=7, color=MUTED, ha="center")
    style(ax, "How long each relative keeps playing your stream",
          f"moving agreement over {WIN}-turn windows, one line per relative that beat you; "
          "grey lines are the shop reveals")
    ax.set_xlabel("turn", fontsize=9); ax.set_ylabel("agreement in window", fontsize=9)
    ax.set_ylim(0, 1.12); ax.set_xlim(-8, 745)
    # the median line, so the shape of the cohort is readable through the tangle
    grid = sorted({t for g in lf for t, _ in g["curve"]})
    medl = [(t, st.median([dict(g["curve"])[t] for g in lf if t in dict(g["curve"])]))
            for t in grid]
    medl = [(t, v) for t, v in medl if v is not None]
    ax.plot([t for t, _ in medl], [v for _, v in medl], color="#7C2D12", lw=2.8,
            label="median of the cohort")
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    plt.tight_layout(); plt.show()

    lefts = [g["left_at"] for g in lf if g["left_at"] is not None]
    stayed = len(lf) - len(lefts)
    early = sum(1 for f in lefts if f < 72)
    near = sum(1 for f in lefts if f >= 72 and min(abs(f - r) for r in REVEALS) <= WIN // 2)
    mid = len(lefts) - early - near
    def n_of(k, one, many):
        return f"{k} {one if k == 1 else many}"

    parts = []
    if stayed: parts.append(n_of(stayed, "never leaves at all: it plays", "never leave at all: they play")
                            + " your plan and beat you INSIDE it, which section 5 is about")
    if early: parts.append(n_of(early, "was", "were") + " never with you: a different OPENING")
    if near: parts.append(n_of(near, "leaves", "leave") + " at a reveal: a ROUTING difference")
    if mid: parts.append(n_of(mid, "leaves", "leave") + " between reveals: a POLICY difference")
    rel = "relative" if len(lf) == 1 else "relatives"
    verb = "beat" if len(lf) == 1 else "beat"
    reading(f"of the {len(lf)} {rel} that {verb} you, " + "; ".join(parts) + ".")
    if lefts:
        m = st.median(lefts)
        print(f"   median departure turn {m:.0f} (day {m//24:.0f})")
        if 420 <= m <= 446:
            print("   NOTE: turn 432 is both the sixth shop reveal AND the start of")
            print("   day 18, so a departure there is genuinely ambiguous between a")
            print("   routing choice and a policy keyed on the calendar. The two need")
            print("   different answers, and only a controlled re-run separates them.")
else:
    if not bimodal:
        reading("section 2 found no two clouds, so nothing here is a relative and there "
                "is nothing to take apart. Either nobody in this field runs your plan, "
                "or none of them drew you in this window.")
    else:
        reading("you have relatives, but none of them beat you in this window. Sections "
                "4 and 5 need a defeat by one to have anything to say.")


PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER")


def sells(stream):
    out = collections.defaultdict(list)
    for t, a in enumerate(stream):
        for o in ((a or {}).get("market") or []):
            if o and o[0] == "SELL" and len(o) >= 3 and o[1] in PRODUCTS:
                out[o[1]].append((t, int(o[2])))
    return out


def anatomy(mine, theirs):
    a, b = sells(mine), sells(theirs)
    cls, leads = collections.Counter(), []
    for prod in set(a) | set(b):
        mp, tp = a.get(prod, []), b.get(prod, [])
        used = set()
        for (t, q) in mp:
            best = None
            for j, (t2, q2) in enumerate(tp):
                if j in used or q2 != q:
                    continue
                if best is None or abs(t2 - t) < abs(tp[best][0] - t):
                    best = j
            if best is None:
                cls["NOT AT ALL"] += 1
            else:
                used.add(best)
                dt = tp[best][0] - t
                cls["EARLIER" if dt < 0 else "LATER" if dt > 0 else "SAME"] += 1
                if dt < 0:
                    leads.append(-dt)
        cls["MORE"] += sum(1 for j in range(len(tp)) if j not in used)
    return cls, leads


agg, all_leads, rows = collections.Counter(), [], []
for g in sorted(lf, key=lambda g: g["mine"] - g["theirs"])[:12]:
    cls, leads = anatomy(g["mine_acts"], g["their_acts"])
    agg.update(cls); all_leads += leads
    rows.append((g, cls))

if rows:
    same = agg.pop("SAME", 0)
    total = same + sum(agg.values())
    print(f"{same:,} of {total:,} of my orders were matched exactly, same turn and same "
          f"size ({100*same/max(total,1):.0f}%). That is the spine we share.\n")
    print(f"{'rival':<24}{'margin':>10}   what they did differently")
    for g, cls in rows:
        diff = sorted(((k, v) for k, v in cls.items() if k != "SAME"), key=lambda kv: -kv[1])
        print(f"{(g['opp'] or str(g['opp_sub']))[:22]:<24}{g['mine']-g['theirs']:>+10,.0f}   "
              + ", ".join(f"{k.lower()} {v}" for k, v in diff[:3]))

    order = ["EARLIER", "LATER", "MORE", "NOT AT ALL"]
    labels = ["sold it\nEARLIER", "held it\nLONGER", "sold lots I\nnever ordered",
              "never sold what\nI sold"]
    fig, ax = plt.subplots(figsize=(9.4, 3.4))
    bars = ax.bar(labels, [agg.get(k, 0) for k in order],
                  color=[FAM if agg.get(k, 0) == max(agg.get(x, 0) for x in order) else OUT
                         for k in order], width=0.62)
    for b, k in zip(bars, order):
        ax.annotate(f"{agg.get(k,0):,}", (b.get_x() + b.get_width()/2, b.get_height()),
                    ha="center", va="bottom", fontsize=9, color="#0F172A",
                    xytext=(0, 3), textcoords="offset points")
    style(ax, "What my relatives did with the lots I sold",
          "only the orders that differ; the matched spine is excluded")
    ax.set_ylabel("orders", fontsize=9)
    plt.tight_layout(); plt.show()

    VERDICT = {"EARLIER": "a TIMING edge: they are in front of you on the same lots, so the "
                          "price they take is the price you would have taken one beat later",
               "LATER": "a HOLDING strategy: they are betting on the price curve rather than "
                        "on getting there first",
               "MORE": "a VOLUME edge: they are converting something into sales that you are "
                       "leaving on the farm, which is a production or liquidation difference "
                       "rather than a market one",
               "NOT AT ALL": "a SELECTION difference: they decline lots you sell, which usually "
                             "means they refuse to sell into a price you are accepting"}
    ranked = agg.most_common()
    tot = sum(agg.values())
    (d1, n1) = ranked[0]
    close = [k for k, v in ranked[1:] if n1 and (n1 - v) / n1 <= 0.15]
    if close:
        # a two-point lead over three thousand orders is not a lead
        picked = [d1] + close
        names = ", ".join(picked[:-1]) + " and " + picked[-1]
        word = {2: "two", 3: "three", 4: "four"}.get(len(picked), str(len(picked)))
        counts = ", ".join(f"{k} {v:,}" for k, v in ranked[:1 + len(close)])
        reading(f"{word} differences are tied at the top, {names} ({counts} of {tot:,} orders "
                f"that differ), so read them together rather than picking one.")
        for k in [d1] + close:
            print(f"   {k}: {VERDICT[k]}.")
    else:
        lead = (f", clear of the next by {100*(n1-ranked[1][1])/n1:.0f}%"
                if len(ranked) > 1 else ", and it is the only kind of difference there is")
        reading(f"the dominant difference is {d1} ({n1:,} orders of {tot:,} that differ)"
                f"{lead}. That is {VERDICT[d1]}.")
    if all_leads:
        print(f"   when they did get in front, they were ahead by a median of "
              f"{st.median(all_leads):.0f} turns.")
else:
    reading("no family defeats to take apart. Sections 4 and 5 only have work to do "
            "when somebody is running your plan against you; if they are empty, "
            "your gap is a strength gap and the answer is a better agent rather "
            "than a better flag.")
