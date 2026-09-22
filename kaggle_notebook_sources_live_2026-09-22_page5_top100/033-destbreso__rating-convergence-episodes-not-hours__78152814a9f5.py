import matplotlib.pyplot as plt

PROBES = [('A, warming up', 11, 88, 12.3), ('B, byte-identical', 22, 55, 16.4), ('C, settled', 36, 13, 9.7), ('D, quiet', 10, 3, 4.5)]

labels = [p[0] for p in PROBES]
rate = [p[2] / p[3] for p in PROBES]          # episodes per hour
y = list(range(len(labels)))[::-1]

fig, ax = plt.subplots(figsize=(8.6, 3.0))
ax.barh(y, rate, height=0.6, color="#2f6fb2")
for yy, r, p in zip(y, rate, PROBES):
    ax.annotate(f"{r:.1f}/h   ({p[2]} episodes in {p[3]:.1f} h)",
                (r, yy), xytext=(6, 0), textcoords="offset points",
                va="center", fontsize=9, color="#40484f")
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9)
ax.set_xlim(0, 11)
ax.set_xlabel("episodes played per hour")
ax.set_title("the same wall clock buys very different amounts of evidence",
             fontsize=10)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

import matplotlib.pyplot as plt

WARMING = [(13, 1809.8), (16, 1895.2), (32, 2394.2), (96, 2574.3), (100, 2583.7), (101, 2578.9)]
FALLING = [(80, 2913.7), (89, 2892.9), (91, 2884.0), (92, 2880.3), (93, 2886.4), (129, 2750.6), (134, 2735.5), (135, 2731.9)]
SETTLED = [(80, 2036.6), (88, 2027.7), (89, 2023.2), (92, 2018.1), (93, 2022.6)]

fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.4))
series = [("A: still warming up", WARMING, "#c2571f",
           "+12.0 pts/episode"),
          ("B: falling, byte-identical", FALLING, "#b5486b",
           "-2.11 pts/episode"),
          ("C: settled", SETTLED, "#14724d", "-0.70 pts/episode")]
for ax, (title, s, colour, note) in zip(axes, series):
    xs = [p[0] for p in s]; ys = [p[1] for p in s]
    ax.plot(xs, ys, "-o", ms=4, color=colour)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("episodes played")
    ax.annotate(note, (0.5, 0.06), xycoords="axes fraction", ha="center",
                fontsize=9, color=colour, weight="bold")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
axes[0].set_ylabel("leaderboard rating")
plt.tight_layout(); plt.show()

def convergence(samples, threshold=1.0):
    """samples: list of (episodes_completed, score) for ONE submission,
    in time order. Returns the per-episode drift, the number of sign
    flips, and whether the rating can be read yet."""
    steps = [(s2 - s1) / (n2 - n1)
             for (n1, s1), (n2, s2) in zip(samples, samples[1:])
             if n2 > n1]                       # <- the important filter
    if not steps:
        return None, 0, False
    drift = sum(steps) / len(steps)
    flips = sum(1 for a, b in zip(steps, steps[1:]) if a * b < 0)
    return drift, flips, abs(drift) <= threshold and flips >= 1


for name, s in (("A, warming up", WARMING),
                ("B, byte-identical", FALLING),
                ("C, settled", SETTLED)):
    d, f, ok = convergence(s)
    print(f"{name:20s} drift {d:+6.2f} pts/episode   flips {f}   "
          f"{'READABLE' if ok else 'not readable yet'}")

import matplotlib.pyplot as plt

xs = [p[0] for p in FALLING]; ys = [p[1] for p in FALLING]
fig, ax = plt.subplots(figsize=(9, 3.4))
ax.plot(xs, ys, "-o", ms=5, color="#b5486b")
ax.axhline(ys[0], color="#9aa3ad", ls="--", lw=1)
ax.annotate("first reading, 2,913.7", (xs[0], ys[0]), xytext=(12, 9),
            textcoords="offset points", fontsize=9, color="#40484f")
ax.annotate("last reading, 2,731.9", (xs[-1], ys[-1]), xytext=(-10, 13),
            textcoords="offset points", ha="right", fontsize=9,
            color="#40484f")
ax.annotate("182 points, and not one byte\nof the agent changed",
            (0.24, 0.12), xycoords="axes fraction", ha="center",
            fontsize=10, color="#b5486b", weight="bold")
ax.margins(y=0.18)
ax.set_xlabel("episodes played")
ax.set_ylabel("leaderboard rating")
ax.set_title("the same file, measured against a field that moved",
             fontsize=10)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

import csv
import io
import subprocess
import time


def _csv(args):
    """Run a kaggle CLI command with --csv and parse it properly."""
    out = subprocess.run(["kaggle", *args, "--csv"],
                         capture_output=True, text=True, check=True).stdout
    lines = out.splitlines()
    # (1) some commands print a "Next Page Token = ..." preamble before
    #     the CSV, so find the header rather than assuming line 0.
    start = next((i for i, l in enumerate(lines)
                  if "," in l and not l.startswith("Next Page")), None)
    if start is None:
        return []
    # (2) use the csv module: submission descriptions are quoted and
    #     contain commas, so splitting on "," silently misaligns fields.
    return list(csv.DictReader(io.StringIO("\n".join(lines[start:]))))


def probe(submission_id, competition="kaggriculture"):
    """(ladder episodes completed, public score) for one submission."""
    subs = _csv(["competitions", "submissions", competition])
    row = next((r for r in subs
                if str(r.get("ref")) == str(submission_id)), None)
    score = float(row.get("publicScore") or 0) if row else 0.0

    eps = _csv(["competitions", "episodes", str(submission_id)])
    # (3) PUBLIC only: every submission also plays one VALIDATION
    #     episode against itself, which is not a rated game. It is a
    #     constant +1, so it cancels in a difference and does not change
    #     the drift, but it does change "how many games has this played".
    #     The same filter drops the usage-hint line the CLI appends.
    played = sum(1 for e in eps
                 if "COMPLET" in str(e.get("state", ""))
                 and "PUBLIC" in str(e.get("type", "")))
    return played, score


def sample_until(submission_id, min_new_episodes=8, every=1800,
                 max_probes=12):
    """Probe on a timer until enough NEW episodes have been played."""
    samples, start = [], None
    for _ in range(max_probes):
        n, score = probe(submission_id)
        samples.append((n, score))
        start = n if start is None else start
        drift, flips, readable = convergence(samples)
        print(f"episodes {n:4d}  score {score:8.1f}  "
              f"drift {drift if drift is None else round(drift, 2)}")
        if n - start >= min_new_episodes and readable:
            break
        time.sleep(every)
    return samples