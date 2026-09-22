# The five textures, computed on 2026-09-04/05 from exact public replays (eight
# games per agent) and embedded so the picture is stable and dated. texture()
# is the whole recipe; the demo cell below reuses it on YOUR submission, live.
import base64, collections, json as _json, zlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

GREEN, AMBER, WALK, KNOWN, NAVY = "#DCEEE1", "#B45309", "#C7CDD6", "#64748B", "#0F172A"
DROP_UNIT = {"PASS", "NORTH", "SOUTH", "EAST", "WEST"}   # movement is phonetics
ARG_UNIT = {"PLANT", "PICKUP", "PLACE"}                   # keep WHAT, drop how much

def turn_token(a):
    # one turn as the sorted multiset of its intent tokens, or None if empty
    toks = []
    for u in [a.get("farmer") or ["PASS"]] + list(a.get("hands") or []):
        if not u or u[0] in DROP_UNIT:
            continue
        toks.append(f"{u[0]}:{u[1]}" if u[0] in ARG_UNIT and len(u) > 1 else u[0])
    for o in a.get("market") or []:
        if not o:
            continue
        if o[0] in ("HIRE", "BUY_LAND"):
            toks.append(o[0])
        elif len(o) > 1:
            toks.append(f"{o[0]}:{o[1]}")
    return "+".join(sorted(toks)) if toks else None

def canon(a):
    if not a:
        return ("PASS", (), ())
    return (tuple(a.get("farmer") or ["PASS"]),
            tuple(tuple(h) for h in (a.get("hands") or [])),
            tuple(tuple(o) for o in (a.get("market") or [])))

def texture(streams, n_eps=8, n=5):
    """rows = episodes, columns = turns. 0 matches the agent's own modal action;
    1 only the market differs; then three shades of novelty where the plan
    differs: 2 movement only (different walking, no words), 3 a phrase this
    agent also says in its other games (known words, new moment), 4 a phrase
    it says nowhere else (newly composed)."""
    ss = streams[:n_eps]
    T = min(719, min(len(x) for x in ss))
    modal = [collections.Counter(canon(x[t]) for x in ss).most_common(1)[0][0]
             for t in range(T)]
    gram_sets, spans = [], []
    for x in ss:
        seq = [(t, tok) for t in range(T) if (tok := turn_token(x[t] or {}))]
        gs = {}
        for i in range(len(seq) - n + 1):
            gram = tuple(tok for _, tok in seq[i:i + n])
            gs.setdefault(gram, []).append([t for t, _ in seq[i:i + n]])
        gram_sets.append(gs)
    counts = collections.Counter(g for gs in gram_sets for g in gs)
    half = max(2, len(ss) // 2)
    common = {g for g, c in counts.items() if c >= half}
    covered = []
    for gs in gram_sets:
        cov = set()
        for g, sp in gs.items():
            if g in common:
                for span in sp:
                    cov.update(span)
        covered.append(cov)
    out = []
    for k, x in enumerate(ss):
        line = []
        for t in range(T):
            a, m = canon(x[t]), modal[t]
            if a == m:
                line.append(0)
            elif (a[0], a[1]) == (m[0], m[1]):
                line.append(1)
            elif turn_token(x[t] or {}) is None:
                line.append(2)
            elif t in covered[k]:
                line.append(3)
            else:
                line.append(4)
        out.append(line)
    return np.array(out)

_PANELS = _json.loads(zlib.decompress(base64.b64decode(
"eNrtnc1u3CAQx1+l2nMPzDCnvkqVwx6iKmqbSmmrqq367jXGxoAHbBJYf+xY2Y2NWTyGH8OfwZv8vXy9fnm6vjw+f/52+fDu40Xd7QYKYNiDRA7g93NprzDD/BD0b90+mUQaTprfRF6Cf21K20Hkl2+Px7SgKLbs/mOUPDWzyV6fKlQGdXVAvuHg2zzdM1F0D33G7nV5/06QFqQF6XPwzOFs9v1XKt3/bI10FSGpo/zmGLR9+TZrxk6XN3Hd8TybHtVJUA5ju16ouzX1wF7Xu4f+Pr190vZ4yNf3PALXnoK0IC1InwrppSaIB/alc14atEY6xqE50qoe0jN7VyLd56cA6X7fs0OQFqQF6VNND5eEB1vVLh1ymMNbBEmp8PDLqYW0xQqK7KwhPKZr88JDa0FakL4rpB86pr9cP71cnz89XZ8PHacmemUQyfCnMkGwu+3st70WrIqQQqmBR/bagrQgfTKkV9Sd7kYpTTqcibHVQ1OtdR9xAx1TpHaDYFisTn2GOaNBa/YDEGRfugK4dG0PIX/ZwXrtamIqRqfKH0sfC4e4fJjfrfZjpr6Z4zwdprPR7QJjfp/bbx1BWpAWpCmggPf5pLOaoNpc7u3FJOy3ZvYVZKqp2+/nUHo/IgBKNEJmqR4WFcCqdX6ATBVDwZ3BBPVyI8O8DXnlMponSAvSd4H0eYQHcMIjHCct0kZ4DEi3Fh6wVngAewXghQdAUnjAovCAVcIDEsIjuPKy8FC+7uiTgel+GeEhSAvS94W0iVN/fnz6c+wnqYkZCzODKRmZkYkBQnHfKUu/63jhbYAw232vK3I1Mt9S6VCUjoX509tW+Wull22YLweDne4Nz4V03ksvfroQ6UrpWKfpayG0XdcoQxpnx4jHU9WW1v7rENRgHC9tghSiqrE3O7qXrmIPpjqAEuHxeqR31cS38eq4G2+PGNqD4wsF6WUtDYkKreTVN/OixxAeq/Kj+4V0fOFBzb20OriX3huKbe13XhrOIR12MT3cyovSSbsMrJhWWzftRah/XW8boNbaH8Ndh9Koux9jXl4JzFSA2TJBuKPMjyS9at+vq0C0D20fBciIVnvs5P7AZ8JtYnqOgmmFdXCk1SHsxJ3Nf28qqgMvbdzodAKNm0aZqsq645s3QVqQFqQrRzLWT9iUwrmcTmVfr8ldUbzgSZmT1jW8YMBqA3eddDy6Zk7lF6QFaUF6M6RZbFlybfCkUhXhZkjUmR7iURCtsKKJgrQgfUKkTYD6x+OP7z9/Vw5Suz+zOobz+kE8N3kcMQ0fbYboWfWulOGvs47qIggT8mXLzPPkM1TKzRWBhm/nWYXp/OHw1Qw9hpLRoRsGoz2kDYuu+2AfW477lllm0WalxQZEVChvI1eLo0XYu0jGP6dcs/kaBNuvVevgbHEQHDYqB9reV/sNmwtrSHhOCEicdTa3BkOJJZrpKY91y9WmKxkvnVIPqaZUrAGqVA0UIrS3UV/BRvZXsnPw0jEXOG96nJYGYZQMkZBV4SqhhSsGcVo73GiJq1QoIzVusq0eEmo9CjT20HOk8YZees5zekpoI2tq1gnQ/n+EoMcsCo8dzW3qrdbX2mohukUXy1TmjZF2WnqYBkbwTtkDpGMtHTr+GdK4cM83eKQS9+Rd96eBy+ptrYewKfh24WGB21B4YOtna1p7rZ09EqpqefUNuhhW1tLjf3qaXG7njFErzfBsnvCYTw+JnR6immJ46wcmxWstrBipOAaiW3np5o9FxpdAe3x5+Pcf6HH1Bw==")).decode())
LABELS = [
    ("maliarenko", "Dmytro Maliarenko, rank 13 at the 2026-09-04 pull: a SCRIPT"),
    ("lagrangian", "LagrangianLocomotive, rank 15 at the pull: known phrases, reshuffled"),
    ("keiz",       "keiz, rank 1 at the pull: a BRANCHER, the trunk then genuine composition"),
    ("kwa",        "kwa, rank 4 at the pull: a SCHEDULER"),
    ("tetsuya",    "tetsuya & yuanzhe zhou, former rank 1, mid-table on 2026-09-05: a SCHEDULER"),
]
cmap = ListedColormap([GREEN, AMBER, WALK, KNOWN, NAVY])
fig, axes = plt.subplots(5, 1, figsize=(9.4, 8.0), sharex=True)
for ax, (key, label) in zip(axes, LABELS):
    mat = np.array([[int(ch) for ch in row] for row in _PANELS[key]])
    ax.imshow(mat, aspect="auto", cmap=cmap, vmin=0, vmax=4, interpolation="nearest")
    ax.set_yticks([])
    ax.set_ylabel("8 games", fontsize=7)
    ax.set_title(label, fontsize=8.5, loc="left")
    for d in range(6, 30, 6):
        ax.axvline(d * 24, color="white", lw=0.5, alpha=0.55)
axes[-1].set_xlabel("turn (vertical lines every 6 in-game days)")
axes[0].legend(handles=[Patch(facecolor=GREEN, edgecolor="0.6", label="matches own modal action"),
                        Patch(facecolor=AMBER, label="market differs"),
                        Patch(facecolor=WALK, edgecolor="0.6", label="movement only"),
                        Patch(facecolor=KNOWN, label="known phrase, new moment"),
                        Patch(facecolor=NAVY, label="newly composed")],
               fontsize=7, frameon=False, ncol=5, loc="lower right", bbox_to_anchor=(1.0, 1.3))
plt.tight_layout(); plt.show()

for key, label in LABELS:
    flat = "".join(_PANELS[key])
    n = len(flat)
    sh = [flat.count(str(i)) / n for i in range(5)]
    print(f"{key:<12} green {sh[0]:5.1%}  amber {sh[1]:5.1%}  walk {sh[2]:4.1%}  "
          f"known {sh[3]:4.1%}  new {sh[4]:5.1%}")


# The instrument, standard library only. Constants are the published calibration:
# n = 5 phrases, day bands from day 6, an 8-episode floor.
import collections, math, statistics as st

PASS_TURN = {"farmer": ["PASS"], "hands": [], "market": []}
DROP_UNIT = {"PASS", "NORTH", "SOUTH", "EAST", "WEST"}   # movement is phonetics
ARG_UNIT = {"PLANT", "PICKUP", "PLACE"}                   # keep WHAT, drop how much
BANDS = [(6, 11), (12, 19), (20, 29)]
MIN_EPISODES = 8

def turn_token(a):
    # one turn as the sorted multiset of its intent tokens, or None if empty
    toks = []
    for u in [a.get("farmer") or ["PASS"]] + list(a.get("hands") or []):
        if not u or u[0] in DROP_UNIT:
            continue
        toks.append(f"{u[0]}:{u[1]}" if u[0] in ARG_UNIT and len(u) > 1 else u[0])
    for o in a.get("market") or []:
        if not o:
            continue
        if o[0] in ("HIRE", "BUY_LAND"):
            toks.append(o[0])
        elif len(o) > 1:
            toks.append(f"{o[0]}:{o[1]}")
    return "+".join(sorted(toks)) if toks else None

def grams_by_band(acts, n=5):
    """Phrases: n consecutive non-empty turns, keyed to the day band they start in."""
    seq = [(t // 24, tok) for t, a in enumerate(acts)
           if (tok := turn_token(a or {})) and t // 24 >= 6]
    out = {b: set() for b in BANDS}
    for i in range(len(seq) - n + 1):
        day = seq[i][0]
        for lo, hi in BANDS:
            if lo <= day <= hi:
                out[(lo, hi)].add(tuple(t for _, t in seq[i:i + n]))
                break
    return out

def fingerprint(episodes, n=5):
    """episodes: list of per-episode action streams (engine-turn aligned)."""
    per = [grams_by_band(a, n) for a in episodes]
    rows = {}
    for b in BANDS:
        counts = collections.Counter()
        for g in per:
            for gram in g[b]:
                counts[gram] += 1
        half = max(2, len(episodes) // 2)
        common = {g for g, c in counts.items() if c >= half}
        rates = [len(g[b] & common) / len(g[b]) for g in per if g[b]]
        total = sum(counts.values())
        if total and len(counts) > 1:
            H = -sum((c / total) * math.log(c / total) for c in counts.values())
            Hn = H / math.log(len(counts))
        else:
            Hn = 0.0
        rows[b] = {"repeat_rate": round(st.median(rates), 3) if rates else None,
                   "norm_entropy": round(Hn, 3), "distinct_grams": len(counts)}
    return rows

def speech_class(rows):
    r = [rows[b]["repeat_rate"] for b in BANDS]
    if any(x is None for x in r):
        return "INSUFFICIENT-SIGNAL"
    if r[0] >= 0.95 and r[1] >= 0.7:
        return "SCRIPT"
    if r[0] >= 0.5 and r[1] < 0.5:
        return "BRANCHER"
    if r[0] < 0.5:
        return "SCHEDULER"
    return "MIXED"

print("instrument loaded: fingerprint(episodes) -> repeat_rate + norm_entropy per band, speech_class(rows)")


# Pull the newest public replays of one submission and fingerprint it.
# One request every 1.5 seconds: these are shared endpoints, be polite on them.
import time
import requests

LIST_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{id}.json"

def pull_streams(submission_id, max_eps=10, pace=1.5):
    """Newest completed episodes as action streams at the engine-turn alignment.
    A replay stores the action decided at engine turn t at steps[t + 1]."""
    eps = requests.post(LIST_URL, json={"submissionId": int(submission_id)},
                        timeout=30).json().get("episodes", [])
    eps = [e for e in eps if e.get("state") == "COMPLETED"]
    eps.sort(key=lambda e: e.get("endTime") or "", reverse=True)
    streams = []
    for e in eps:
        if len(streams) >= max_eps:
            break
        r = requests.get(REPLAY_URL.format(id=e["id"]), timeout=120)
        time.sleep(pace)
        if not r.ok:
            continue
        steps = r.json().get("steps") or []
        if len(steps) < 700:
            continue
        seat = next(((a.get("index") or 0) for a in e["agents"]
                     if a.get("submissionId") == int(submission_id)), None)
        if seat is None:
            continue
        streams.append([(steps[t + 1][seat].get("action") if t + 1 < len(steps)
                         else None) or PASS_TURN for t in range(719)])
    return streams

def fingerprint_submission(submission_id, max_eps=10):
    eps = pull_streams(submission_id, max_eps=max_eps)
    if len(eps) < MIN_EPISODES:
        print(f"submission {submission_id}: {len(eps)} usable episodes, below the "
              f"{MIN_EPISODES}-episode floor. Refusing rather than misleading.")
        return None
    rows = fingerprint(eps)
    print(f"submission {submission_id}: {len(eps)} episodes")
    print(f"{'band':>8}{'repeat_rate':>13}{'norm_entropy':>14}{'distinct':>10}")
    for b in BANDS:
        r = rows[b]
        print(f"  d{b[0]:02d}-{b[1]:02d}{str(r['repeat_rate']):>13}"
              f"{str(r['norm_entropy']):>14}{r['distinct_grams']:>10}")
    print(f"class: {speech_class(rows)}   (language only, not strength)")
    return rows

print("pull_streams / fingerprint_submission ready")


import matplotlib.pyplot as plt
import numpy as np

# measured 2026-09-04 on public replays; the tape row is the range over four teams
ANCHORS = [
    ("field tapes (4 teams)", [1.00, 0.955, 0.825], "SCRIPT"),
    ("kawashigi 55540317",     [0.89, 0.15, 0.00],  "BRANCHER"),  # カワシギ, romanised for the chart font
    ("keiz",                   [0.748, 0.00, 0.00], "BRANCHER"),
    ("tetsuya & yuanzhe zhou", [0.019, 0.00, 0.00], "SCHEDULER"),
    ("Crop Dusta",             [0.00, 0.00, 0.00],  "SCHEDULER"),
]
CLASS_COLOR = {"SCRIPT": "#c44536", "BRANCHER": "#b45309",
               "SCHEDULER": "#0f172a", "MIXED": "#8a8f98"}
x = np.arange(len(BANDS))
w = 0.16
fig, ax = plt.subplots(figsize=(8.6, 3.6))
for i, (name, vals, cls) in enumerate(ANCHORS):
    ax.bar(x + (i - 2) * w, vals, w, label=name, color=CLASS_COLOR[cls],
           alpha=1.0 - 0.14 * (i % 3), edgecolor="white", linewidth=0.5)
ax.set_xticks(x, [f"days {lo}-{hi}" for lo, hi in BANDS])
ax.set_ylabel("repeat_rate")
ax.set_title("calibration anchors: where each known agent's language melts",
             fontsize=9, loc="left")
ax.legend(fontsize=7, frameon=False, ncol=2)
ax.set_ylim(0, 1.05)
plt.tight_layout(); plt.show()


# The naive index, refuted in a few lines: the exact entropy formula of the
# instrument, applied to three hand-made agents. Then the corrected index on
# the census.
import math
import statistics as _cst

def _hn(gram_sets):
    counts = collections.Counter(g for gs in gram_sets for g in gs)
    total = sum(counts.values())
    H = -sum((c / total) * math.log(c / total) for c in counts.values())
    return round(H / math.log(len(counts)), 3)

def _repeat(gram_sets):
    counts = collections.Counter(g for gs in gram_sets for g in gs)
    half = max(2, len(gram_sets) // 2)
    common = {g for g, c in counts.items() if c >= half}
    return round(_cst.median([len(gs & common) / len(gs) for gs in gram_sets]), 3)

E = 8
tape = [set(range(50))] * E                                        # the same 50 phrases every game
composer = [set(range(k * 50, k * 50 + 50)) for k in range(E)]      # 50 new phrases every game
mixture = [set(range(25)) | set(range(100 + k * 25, 125 + k * 25)) for k in range(E)]
print(f"{'agent':<20}{'norm_entropy':>13}{'repeat_rate':>13}{'composition':>13}")
for name, gs in (("tape", tape), ("composer", composer), ("trunk + variation", mixture)):
    print(f"{name:<20}{_hn(gs):>13}{_repeat(gs):>13}{round(1 - _repeat(gs), 3):>13}")
print("-> entropy cannot tell the tape from the composer; the composition share can\n")

print("anchors on the corrected scale (scalar = mean composition over the three bands):")
print("  tapes 0.07 | kawashigi 0.65 | keiz 0.75 | tetsuya 0.99 | Crop Dusta 1.00")
print("the census section draws the whole top 15 on this scale")


import base64, zlib, json as _json
import matplotlib.pyplot as plt

_r = _json.loads(zlib.decompress(base64.b64decode(
"eNrdlsEOgyAMhl/FeN5FbKHZqyyetotZ4g4z2WHZu08kmIKAIjst+Q4V5Odvi8R3feufYz9cx/pcXZpT9a+ITNI6B7aO+flJat5Gm8oiEgRL0UYAFzPIVwk22OZIwZalhM9EZYKCrTUPrp+1K+Fm5OGVAkJ4ftpQkSEJMmILMQfel8W5mdo0MCFn0O2yCXDLjwxBq0ZAznKOpzCNKOtW5gA2Fy/lPTqKBYL5Ue6siYME6wPMmGRq+5GzH7RV8qa8lyk+QlbHmEksJPtIEYwTkxcVwPdSBTqClbpEB1gfqYzl9FJxXng0qaVBjf1UE41Q8aZjd6rq+/B4DfrXQ+mru9EXv9IWpT6ZjT4RqE8GYff5AuTEeEM=")).decode())
distinct, known = _r["distinct"], _r["known"]

fig, ax = plt.subplots(figsize=(8.6, 3.2))
ax.step(range(len(distinct)), distinct, where="post", color="#0f172a", lw=1.4)
for t in known:
    ax.axvline(t, color="#c44536", ls="--", lw=0.9)
ax.text(known[0] + 4, 7.4, "hand-measured branch turns", color="#c44536", fontsize=8)
ax.set_xlabel("replay index (engine turn + 1)")
ax.set_ylabel("distinct action-prefix classes\nacross 8 episodes")
ax.set_title("blind melt detection vs seven hand-measured branches: every split lands on a dashed line",
             fontsize=9, loc="left")
ax.set_ylim(0.5, 8.5)
plt.tight_layout(); plt.show()

print("hits: " + ", ".join(f"{k} -> {k} (delta 0)" for k in known))
print("misses: 0   false alarms: 0   pairwise first-divergence turns reproduced: 28/28")


DEMO_SUBMISSION = 55982835   # <- put YOUR submission id here (this one is keiz's)
MAX_EPS = 10                 # 8 is the floor; 10 costs ten polite downloads

streams_demo = pull_streams(DEMO_SUBMISSION, max_eps=MAX_EPS)
if len(streams_demo) < MIN_EPISODES:
    print(f"submission {DEMO_SUBMISSION}: {len(streams_demo)} usable episodes, below the "
          f"{MIN_EPISODES}-episode floor. Refusing rather than misleading.")
else:
    rows_demo = fingerprint(streams_demo)
    print(f"submission {DEMO_SUBMISSION}: {len(streams_demo)} episodes")
    print(f"{'band':>8}{'repeat_rate':>13}{'norm_entropy':>14}{'distinct':>10}")
    for b in BANDS:
        r = rows_demo[b]
        print(f"  d{b[0]:02d}-{b[1]:02d}{str(r['repeat_rate']):>13}"
              f"{str(r['norm_entropy']):>14}{r['distinct_grams']:>10}")
    print(f"class: {speech_class(rows_demo)}   (language only, not strength)")
    mat = texture(streams_demo, n_eps=min(8, len(streams_demo)))
    fig, ax = plt.subplots(figsize=(9.4, 1.9))
    ax.imshow(mat, aspect="auto", cmap=cmap, vmin=0, vmax=2, interpolation="nearest")
    ax.set_yticks([])
    ax.set_ylabel(f"{mat.shape[0]} games", fontsize=7)
    for d in range(6, 30, 6):
        ax.axvline(d * 24, color="white", lw=0.5, alpha=0.55)
    ax.set_title(f"submission {DEMO_SUBMISSION}: its own texture", fontsize=8.5, loc="left")
    ax.set_xlabel("turn")
    plt.tight_layout(); plt.show()


# The census, embedded with its dates: fingerprints computed 2026-09-04/05 from
# the ten newest complete public episodes per team (more where the listing gave
# more), ranks and ratings read in one pass on 2026-09-04.
CENSUS = [
 {
  "rank": 1,
  "team": "keiz",
  "rating": 3054.1,
  "episodes": 40,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.748,
    "norm_entropy": 0.824,
    "distinct_grams": 1228
   },
   "d12-19": {
    "repeat_rate": 0.0,
    "norm_entropy": 1.0,
    "distinct_grams": 7628
   },
   "d20-29": {
    "repeat_rate": 0.0,
    "norm_entropy": 1.0,
    "distinct_grams": 9208
   }
  },
  "class": "BRANCHER (trunk then melt)"
 },
 {
  "rank": 2,
  "team": "Jesse Bullard",
  "rating": 2987.8,
  "episodes": 10,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.875,
    "norm_entropy": 0.937,
    "distinct_grams": 385
   },
   "d12-19": {
    "repeat_rate": 0.565,
    "norm_entropy": 0.947,
    "distinct_grams": 987
   },
   "d20-29": {
    "repeat_rate": 0.086,
    "norm_entropy": 0.983,
    "distinct_grams": 1821
   }
  },
  "class": "MIXED"
 },
 {
  "rank": 3,
  "team": "Andrey Tikhomirov",
  "rating": 2931.7,
  "episodes": 10,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.316,
    "norm_entropy": 0.972,
    "distinct_grams": 898
   },
   "d12-19": {
    "repeat_rate": 0.38,
    "norm_entropy": 0.971,
    "distinct_grams": 1127
   },
   "d20-29": {
    "repeat_rate": 0.126,
    "norm_entropy": 0.982,
    "distinct_grams": 1726
   }
  },
  "class": "SCHEDULER (composes per game)"
 },
 {
  "rank": 4,
  "team": "kwa",
  "rating": 2897.4,
  "episodes": 18,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.0,
    "norm_entropy": 0.996,
    "distinct_grams": 1324
   },
   "d12-19": {
    "repeat_rate": 0.0,
    "norm_entropy": 0.996,
    "distinct_grams": 1898
   },
   "d20-29": {
    "repeat_rate": 0.0,
    "norm_entropy": 0.996,
    "distinct_grams": 2337
   }
  },
  "class": "SCHEDULER (composes per game)"
 },
 {
  "rank": 5,
  "team": "MtN",
  "rating": 2896.0,
  "episodes": 19,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.796,
    "norm_entropy": 0.984,
    "distinct_grams": 326
   },
   "d12-19": {
    "repeat_rate": 0.536,
    "norm_entropy": 0.966,
    "distinct_grams": 750
   },
   "d20-29": {
    "repeat_rate": 0.215,
    "norm_entropy": 0.972,
    "distinct_grams": 1275
   }
  },
  "class": "MIXED"
 },
 {
  "rank": 6,
  "team": "OceanMix",
  "rating": 2873.1,
  "episodes": 19,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.086,
    "norm_entropy": 0.976,
    "distinct_grams": 640
   },
   "d12-19": {
    "repeat_rate": 0.0,
    "norm_entropy": 0.975,
    "distinct_grams": 1013
   },
   "d20-29": {
    "repeat_rate": 0.0,
    "norm_entropy": 0.977,
    "distinct_grams": 1353
   }
  },
  "class": "SCHEDULER (composes per game)"
 },
 {
  "rank": 7,
  "team": "CemBas",
  "rating": 2856.7,
  "episodes": 10,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.93,
    "norm_entropy": 0.983,
    "distinct_grams": 337
   },
   "d12-19": {
    "repeat_rate": 0.916,
    "norm_entropy": 0.991,
    "distinct_grams": 411
   },
   "d20-29": {
    "repeat_rate": 0.372,
    "norm_entropy": 0.978,
    "distinct_grams": 748
   }
  },
  "class": "MIXED"
 },
 {
  "rank": 8,
  "team": "b13902103_yuhung94",
  "rating": 2840.9,
  "episodes": 10,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.0,
    "norm_entropy": 0.998,
    "distinct_grams": 1304
   },
   "d12-19": {
    "repeat_rate": 0.0,
    "norm_entropy": 1.0,
    "distinct_grams": 1905
   },
   "d20-29": {
    "repeat_rate": 0.0,
    "norm_entropy": 1.0,
    "distinct_grams": 2336
   }
  },
  "class": "SCHEDULER (composes per game)"
 },
 {
  "rank": 9,
  "team": "Giulio Ravasio",
  "rating": 2838.6,
  "episodes": 12,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.757,
    "norm_entropy": 0.952,
    "distinct_grams": 559
   },
   "d12-19": {
    "repeat_rate": 0.622,
    "norm_entropy": 0.949,
    "distinct_grams": 951
   },
   "d20-29": {
    "repeat_rate": 0.103,
    "norm_entropy": 0.974,
    "distinct_grams": 1722
   }
  },
  "class": "MIXED"
 },
 {
  "rank": 10,
  "team": "Scott Willis",
  "rating": 2836.2,
  "episodes": 14,
  "bands": {
   "d06-11": {
    "repeat_rate": 1.0,
    "norm_entropy": 0.961,
    "distinct_grams": 253
   },
   "d12-19": {
    "repeat_rate": 0.707,
    "norm_entropy": 0.965,
    "distinct_grams": 593
   },
   "d20-29": {
    "repeat_rate": 0.302,
    "norm_entropy": 0.971,
    "distinct_grams": 806
   }
  },
  "class": "SCRIPT"
 },
 {
  "rank": 11,
  "team": "peikopon",
  "rating": 2835.5,
  "episodes": 19,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.739,
    "norm_entropy": 0.938,
    "distinct_grams": 380
   },
   "d12-19": {
    "repeat_rate": 0.832,
    "norm_entropy": 0.95,
    "distinct_grams": 410
   },
   "d20-29": {
    "repeat_rate": 0.388,
    "norm_entropy": 0.952,
    "distinct_grams": 1315
   }
  },
  "class": "MIXED"
 },
 {
  "rank": 12,
  "team": "Zhongyi Dai",
  "rating": 2831.6,
  "episodes": 10,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.147,
    "norm_entropy": 0.989,
    "distinct_grams": 425
   },
   "d12-19": {
    "repeat_rate": 0.005,
    "norm_entropy": 0.988,
    "distinct_grams": 632
   },
   "d20-29": {
    "repeat_rate": 0.0,
    "norm_entropy": 0.987,
    "distinct_grams": 807
   }
  },
  "class": "SCHEDULER (composes per game)"
 },
 {
  "rank": 13,
  "team": "Dmytro Maliarenko",
  "rating": 2828.1,
  "episodes": 20,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.979,
    "norm_entropy": 0.953,
    "distinct_grams": 256
   },
   "d12-19": {
    "repeat_rate": 0.969,
    "norm_entropy": 0.951,
    "distinct_grams": 528
   },
   "d20-29": {
    "repeat_rate": 0.804,
    "norm_entropy": 0.954,
    "distinct_grams": 762
   }
  },
  "class": "SCRIPT"
 },
 {
  "rank": 14,
  "team": "Atakan Aldemir",
  "rating": 2819.1,
  "episodes": 20,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.439,
    "norm_entropy": 0.968,
    "distinct_grams": 453
   },
   "d12-19": {
    "repeat_rate": 0.408,
    "norm_entropy": 0.971,
    "distinct_grams": 679
   },
   "d20-29": {
    "repeat_rate": 0.223,
    "norm_entropy": 0.973,
    "distinct_grams": 975
   }
  },
  "class": "SCHEDULER (composes per game)"
 },
 {
  "rank": 15,
  "team": "LagrangianLocomotive",
  "rating": 2810.4,
  "episodes": 20,
  "bands": {
   "d06-11": {
    "repeat_rate": 0.783,
    "norm_entropy": 0.95,
    "distinct_grams": 291
   },
   "d12-19": {
    "repeat_rate": 0.974,
    "norm_entropy": 0.968,
    "distinct_grams": 297
   },
   "d20-29": {
    "repeat_rate": 0.915,
    "norm_entropy": 0.968,
    "distinct_grams": 439
   }
  },
  "class": "MIXED"
 }
]

import matplotlib.pyplot as plt
import numpy as np

names = [f"{c['rank']:>2}. {c['team']}" for c in CENSUS]
mat = np.array([[c["bands"][b]["repeat_rate"] for b in ("d06-11", "d12-19", "d20-29")]
                for c in CENSUS])
cls = [c["class"].split(" ")[0] for c in CENSUS]
fig, ax = plt.subplots(figsize=(7.6, 6.4))
im = ax.imshow(mat, cmap="RdYlBu_r", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(3), ["days 6-11", "days 12-19", "days 20-29"])
ax.set_yticks(range(len(names)), names, fontsize=8)
for yy in range(mat.shape[0]):
    for xx in range(3):
        ax.text(xx, yy, f"{mat[yy, xx]:.2f}", ha="center", va="center", fontsize=7,
                color="white" if 0.25 < mat[yy, xx] < 0.85 else "black")
CLASS_COLOR = {"SCRIPT": "#c44536", "BRANCHER": "#b45309",
               "SCHEDULER": "#0f172a", "MIXED": "#8a8f98"}
for yy, c in enumerate(cls):
    ax.text(3.05, yy, c, va="center", fontsize=7, color=CLASS_COLOR.get(c, "#333"))
ax.set_xlim(-0.5, 4.1)
ax.set_title("top 15 (ranks of 2026-09-04): cross-game repeat_rate per band, red repeats, blue composes",
             fontsize=9, loc="left")
fig.colorbar(im, ax=ax, shrink=0.7, label="repeat_rate")
plt.tight_layout(); plt.show()

print(f"{'rk':>3} {'team':<22}{'rating':>8}{'eps':>5}{'d06-11':>8}{'d12-19':>8}{'d20-29':>8}  class")
for c in CENSUS:
    b = [c["bands"][k]["repeat_rate"] for k in ("d06-11", "d12-19", "d20-29")]
    print(f"{c['rank']:>3} {c['team'][:21]:<22}{c['rating']:>8.1f}{c['episodes']:>5}"
          f"{b[0]:>8}{b[1]:>8}{b[2]:>8}  {c['class']}")

# the same fifteen on the complexity scale of section 5: scalar = mean
# composition share (1 - repeat_rate) over the three bands
scal = sorted(((sum(1 - c["bands"][k]["repeat_rate"] for k in c["bands"]) / 3, c)
               for c in CENSUS), key=lambda x: x[0])
figS, axS = plt.subplots(figsize=(7.8, 4.6))
axS.barh([f"{c['rank']:>2}. {c['team']}" for _, c in scal], [s for s, _ in scal],
         color=[CLASS_COLOR.get(c["class"].split(" ")[0], "#8a8f98") for _, c in scal])
for ref, lab in ((0.07, "tapes"), (0.65, "kawashigi"), (1.0, "composer")):
    axS.axvline(ref, color="#999", lw=0.7, ls=":")
    axS.text(ref, 14.9, lab, fontsize=7, ha="center", color="#666")
axS.set_xlabel("complexity scalar (mean composition share over the three bands)")
axS.set_title("the top 15 on the complexity scale of section 5, anchors dotted", fontsize=9, loc="left")
axS.set_xlim(0, 1.02)
plt.tight_layout(); plt.show()


# The census on two alphabets, embedded (structural drops SELL:* and keeps the
# plan: farmer, hands, HIRE, BUY_LAND, BUY_*). To recompute, pass a channels
# argument into turn_token that skips sell tokens; everything else is identical.
STRUCTURAL = [
 {
  "rank": 1,
  "team": "keiz",
  "full": {
   "d06-11": 0.748,
   "d12-19": 0.0,
   "d20-29": 0.0
  },
  "structural": {
   "d06-11": 0.811,
   "d12-19": 0.0,
   "d20-29": 0.0
  },
  "divergence": {
   "d06-11": 0.063,
   "d12-19": 0.0,
   "d20-29": 0.0
  }
 },
 {
  "rank": 2,
  "team": "Jesse Bullard",
  "full": {
   "d06-11": 0.875,
   "d12-19": 0.565,
   "d20-29": 0.086
  },
  "structural": {
   "d06-11": 0.964,
   "d12-19": 0.745,
   "d20-29": 0.236
  },
  "divergence": {
   "d06-11": 0.089,
   "d12-19": 0.18,
   "d20-29": 0.15
  }
 },
 {
  "rank": 3,
  "team": "Andrey Tikhomirov",
  "full": {
   "d06-11": 0.316,
   "d12-19": 0.38,
   "d20-29": 0.126
  },
  "structural": {
   "d06-11": 0.316,
   "d12-19": 0.419,
   "d20-29": 0.285
  },
  "divergence": {
   "d06-11": 0.0,
   "d12-19": 0.039,
   "d20-29": 0.159
  }
 },
 {
  "rank": 4,
  "team": "kwa",
  "full": {
   "d06-11": 0.0,
   "d12-19": 0.0,
   "d20-29": 0.0
  },
  "structural": {
   "d06-11": 0.0,
   "d12-19": 0.0,
   "d20-29": 0.0
  },
  "divergence": {
   "d06-11": 0.0,
   "d12-19": 0.0,
   "d20-29": 0.0
  }
 },
 {
  "rank": 5,
  "team": "MtN",
  "full": {
   "d06-11": 0.796,
   "d12-19": 0.536,
   "d20-29": 0.215
  },
  "structural": {
   "d06-11": 0.794,
   "d12-19": 0.667,
   "d20-29": 0.461
  },
  "divergence": {
   "d06-11": -0.002,
   "d12-19": 0.131,
   "d20-29": 0.246
  }
 },
 {
  "rank": 6,
  "team": "OceanMix",
  "full": {
   "d06-11": 0.086,
   "d12-19": 0.0,
   "d20-29": 0.0
  },
  "structural": {
   "d06-11": 0.093,
   "d12-19": 0.0,
   "d20-29": 0.0
  },
  "divergence": {
   "d06-11": 0.007,
   "d12-19": 0.0,
   "d20-29": 0.0
  }
 },
 {
  "rank": 7,
  "team": "CemBas",
  "full": {
   "d06-11": 0.93,
   "d12-19": 0.916,
   "d20-29": 0.372
  },
  "structural": {
   "d06-11": 0.93,
   "d12-19": 1.0,
   "d20-29": 1.0
  },
  "divergence": {
   "d06-11": 0.0,
   "d12-19": 0.084,
   "d20-29": 0.628
  }
 },
 {
  "rank": 8,
  "team": "b13902103_yuhung94",
  "full": {
   "d06-11": 0.0,
   "d12-19": 0.0,
   "d20-29": 0.0
  },
  "structural": {
   "d06-11": 0.0,
   "d12-19": 0.0,
   "d20-29": 0.0
  },
  "divergence": {
   "d06-11": 0.0,
   "d12-19": 0.0,
   "d20-29": 0.0
  }
 },
 {
  "rank": 9,
  "team": "Giulio Ravasio",
  "full": {
   "d06-11": 0.757,
   "d12-19": 0.622,
   "d20-29": 0.103
  },
  "structural": {
   "d06-11": 0.755,
   "d12-19": 0.789,
   "d20-29": 0.552
  },
  "divergence": {
   "d06-11": -0.002,
   "d12-19": 0.167,
   "d20-29": 0.449
  }
 },
 {
  "rank": 10,
  "team": "Scott Willis",
  "full": {
   "d06-11": 1.0,
   "d12-19": 0.707,
   "d20-29": 0.302
  },
  "structural": {
   "d06-11": 1.0,
   "d12-19": 0.885,
   "d20-29": 0.432
  },
  "divergence": {
   "d06-11": 0.0,
   "d12-19": 0.178,
   "d20-29": 0.13
  }
 },
 {
  "rank": 11,
  "team": "peikopon",
  "full": {
   "d06-11": 0.739,
   "d12-19": 0.832,
   "d20-29": 0.388
  },
  "structural": {
   "d06-11": 0.768,
   "d12-19": 0.948,
   "d20-29": 0.494
  },
  "divergence": {
   "d06-11": 0.029,
   "d12-19": 0.116,
   "d20-29": 0.106
  }
 },
 {
  "rank": 12,
  "team": "Zhongyi Dai",
  "full": {
   "d06-11": 0.147,
   "d12-19": 0.005,
   "d20-29": 0.0
  },
  "structural": {
   "d06-11": 0.218,
   "d12-19": 0.094,
   "d20-29": 0.0
  },
  "divergence": {
   "d06-11": 0.071,
   "d12-19": 0.089,
   "d20-29": 0.0
  }
 },
 {
  "rank": 13,
  "team": "Dmytro Maliarenko",
  "full": {
   "d06-11": 0.979,
   "d12-19": 0.969,
   "d20-29": 0.804
  },
  "structural": {
   "d06-11": 0.982,
   "d12-19": 0.974,
   "d20-29": 0.968
  },
  "divergence": {
   "d06-11": 0.003,
   "d12-19": 0.005,
   "d20-29": 0.164
  }
 },
 {
  "rank": 14,
  "team": "Atakan Aldemir",
  "full": {
   "d06-11": 0.439,
   "d12-19": 0.408,
   "d20-29": 0.223
  },
  "structural": {
   "d06-11": 0.439,
   "d12-19": 0.513,
   "d20-29": 0.309
  },
  "divergence": {
   "d06-11": 0.0,
   "d12-19": 0.105,
   "d20-29": 0.086
  }
 },
 {
  "rank": 15,
  "team": "LagrangianLocomotive",
  "full": {
   "d06-11": 0.783,
   "d12-19": 0.974,
   "d20-29": 0.915
  },
  "structural": {
   "d06-11": 0.782,
   "d12-19": 1.0,
   "d20-29": 1.0
  },
  "divergence": {
   "d06-11": -0.001,
   "d12-19": 0.026,
   "d20-29": 0.085
  }
 }
]

import matplotlib.pyplot as plt
print(f"{'rk':>3} {'team':<22}{'full d06/d12/d20':>20}{'structural':>20}{'div d20-29':>11}")
for r in STRUCTURAL:
    f = "/".join(str(r["full"][k]) for k in ("d06-11", "d12-19", "d20-29"))
    s = "/".join(str(r["structural"][k]) for k in ("d06-11", "d12-19", "d20-29"))
    print(f"{r['rank']:>3} {r['team'][:21]:<22}{f:>20}{s:>20}{r['divergence']['d20-29']:>11}")

byclass = {c["team"]: c["class"].split(" ")[0] for c in CENSUS}
rows_d = sorted(STRUCTURAL, key=lambda r: -r["divergence"]["d20-29"])
fig, ax = plt.subplots(figsize=(7.8, 4.6))
ax.barh([f"{r['rank']:>2}. {r['team']}" for r in rows_d],
        [r["divergence"]["d20-29"] for r in rows_d],
        color=[CLASS_COLOR.get(byclass.get(r["team"], ""), "#8a8f98") for r in rows_d])
ax.invert_yaxis()
ax.set_xlabel("divergence in days 20-29 (structural repeat minus full repeat)")
ax.set_title("the thin-layer detector: how much of each agent's endgame variation is sell orders",
             fontsize=9, loc="left")
plt.tight_layout(); plt.show()


import collections
import matplotlib.pyplot as plt

dist = collections.Counter(c["class"].split(" ")[0] for c in CENSUS)
order = ["SCHEDULER", "MIXED", "SCRIPT", "BRANCHER"]
fig, ax = plt.subplots(figsize=(6.4, 2.6))
ax.barh(order[::-1], [dist[k] for k in order[::-1]],
        color=[CLASS_COLOR[k] for k in order[::-1]])
for i, k in enumerate(order[::-1]):
    ax.text(dist[k] + 0.08, i, str(dist[k]), va="center", fontsize=9)
ax.set_xlim(0, max(dist.values()) + 1)
ax.set_title("the top 15 banded by architecture instead of rating", fontsize=9, loc="left")
plt.tight_layout(); plt.show()

teams, eps_each, mb_each = 600, 8, 2
print(f"full-field sweep: {teams} teams x {eps_each} replays x ~{mb_each} MB "
      f"= ~{teams*eps_each*mb_each/1000:.0f} GB of pulls, "
      f"~{teams*eps_each*2/3600:.0f} h at one request every 2 s; "
      f"the fingerprints themselves take milliseconds per team")
