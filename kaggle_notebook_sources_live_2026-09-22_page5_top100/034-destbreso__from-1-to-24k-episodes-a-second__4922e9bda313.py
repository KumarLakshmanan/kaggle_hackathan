# The guard both benchmark scripts now open with
import os

def require_idle(max_load=1.5):
    load = os.getloadavg()[0]
    if load > max_load:
        raise SystemExit(
            f"load average {load:.2f} is above {max_load}: throughput "
            f"measured here is not a property of the code")
    return load

print(f"load average on this Kaggle worker: {os.getloadavg()[0]:.2f}")

import matplotlib.pyplot as plt

SAMPLES = {'orig_pristine': [202.8, 203.9, 204.1, 204.2, 204.3, 204.7, 205.1, 206.0, 209.9], 'ours_before': [203.2, 203.4, 203.4, 203.6, 204.9, 204.9, 205.1, 205.5, 217.1], 'ours_after': [110.4, 110.7, 110.9, 111.0, 111.0, 111.2, 111.5, 112.4, 116.8]}

labels = ["A  pristine port\n(1.32.6)", "B  patched to 1.32.7\n(before)",
          "C  after this iteration"]
keys = ["orig_pristine", "ours_before", "ours_after"]
colours = ["#9aa3ad", "#2f6fb2", "#14724d"]

fig, ax = plt.subplots(figsize=(9.5, 4.0))
for i, (k, c) in enumerate(zip(keys, colours)):
    v = sorted(SAMPLES[k])
    med = v[len(v) // 2]
    ax.plot([i, i], [v[0], v[-1]], "-", color=c, lw=1.2, alpha=0.45)
    ax.plot([i + (j - len(v) / 2) * 0.045 for j in range(len(v))], v, "o",
            ms=5.5, color=c, alpha=0.6)
    ax.plot([i - 0.2, i + 0.2], [med, med], "-", color=c, lw=3)
    top = max(max(s) for s in SAMPLES.values())
    ax.annotate(f"median {med:.1f} us\n{1e6 / med:,.0f} eps/sec\n"
                f"9 runs: {v[0]:.1f} to {v[-1]:.1f}",
                (i, top * 1.045), fontsize=8.5, color=c, ha="center",
                va="bottom", weight="bold")
ax.set_xticks(range(3)); ax.set_xticklabels(labels, fontsize=9)
ax.set_xlim(-0.5, 2.5)
ax.set_ylim(min(min(s) for s in SAMPLES.values()) * 0.97,
            max(max(s) for s in SAMPLES.values()) * 1.16)
ax.set_ylabel("microseconds per episode\n(lower is better)")
ax.set_title("every repetition plotted, interleaved in one process, "
             "single thread", fontsize=10)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

import matplotlib.pyplot as plt

ROWS = [(1, 4139, 1.0, 10.8, [3814, 4124, 4155, 4262]), (2, 8201, 1.98, 1.6, [8112, 8184, 8217, 8243]), (4, 15109, 3.65, 2.0, [14910, 15088, 15129, 15219]), (8, 21696, 5.24, 7.6, [20352, 21449, 21943, 21998]), (0, 24442, 5.9, 15.6, [21624, 24254, 24629, 25439])]
REAL_EPS = 1.022

labels = ["1", "2", "4", "8", "all\ncores"]
med = [r[1] for r in ROWS]
ideal = [med[0] * n for n in (1, 2, 4, 8, 10)]

fig, ax = plt.subplots(figsize=(9.5, 4.0))
ax.plot(range(5), ideal, "--", color="#c9ced4", lw=1.4,
        label="perfect scaling")
for i, r in enumerate(ROWS):
    ax.plot([i] * len(r[4]), r[4], "o", ms=5, color="#2f6fb2", alpha=0.45)
ax.plot(range(5), med, "-", color="#2f6fb2", lw=2, label="median")
for i, (r, m) in enumerate(zip(ROWS, med)):
    ax.annotate(f"{m:,}\n{r[2]:.1f}x", (i, max(r[4])), xytext=(0, 11),
                textcoords="offset points", ha="center", fontsize=9)
ax.axhline(REAL_EPS, color="#b5486b", lw=1.2)
ax.annotate(f"the official environment: {REAL_EPS:.2f}/sec",
            (0.02, REAL_EPS), xytext=(4, 8), textcoords="offset points",
            fontsize=9, color="#b5486b")
ax.set_xticks(range(5)); ax.set_xticklabels(labels)
ax.set_xlabel("worker threads")
ax.set_ylabel("episodes per second")
ax.set_ylim(0, max(ideal) * 1.08)
ax.set_title("what one line of parallelism was worth, all repetitions shown",
             fontsize=10)
ax.legend(frameon=False, fontsize=9, loc="upper left")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
plt.tight_layout(); plt.show()

import matplotlib.pyplot as plt

PAIRS = [(159.9, 110.8), (160.4, 112.7), (161.6, 113.5), (162.1, 112.8), (159.8, 112.4), (161.9, 113.3), (159.1, 111.7), (158.6, 111.0), (158.9, 112.7)]

before = [p[0] for p in PAIRS]
after = [p[1] for p in PAIRS]
ratios = sorted(b / a for b, a in PAIRS)
med = ratios[len(ratios) // 2]

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10, 3.8),
                              gridspec_kw={"width_ratios": [1.4, 1]})
for b, a in PAIRS:
    ax.plot([0, 1], [b, a], "-", color="#c9ced4", lw=1)
ax.plot([0] * len(before), before, "o", ms=6, color="#2f6fb2", alpha=0.65,
        label="before")
ax.plot([1] * len(after), after, "o", ms=6, color="#14724d", alpha=0.65,
        label="after")
ax.set_xticks([0, 1]); ax.set_xticklabels(["before", "after"])
ax.set_xlim(-0.3, 1.3)
ax.set_ylabel("microseconds per episode")
ax.set_title("paired A/B: each line is one repetition\nthat measured both builds",
             fontsize=10)
ax.legend(frameon=False, fontsize=9)

ax2.plot(ratios, range(1, len(ratios) + 1), "o-", ms=5, color="#c2571f")
ax2.axvline(1.0, color="#9aa3ad", ls="--", lw=1)
ax2.set_xlabel("within-pair speedup")
ax2.set_ylabel("repetition (sorted)")
ax2.set_title(f"every pair above 1.0\nmedian {med:.3f}x, "
              f"range {ratios[0]:.3f} to {ratios[-1]:.3f}", fontsize=10)
for a_ in (ax, ax2):
    for s in ("top", "right"):
        a_.spines[s].set_visible(False)
plt.tight_layout(); plt.show()