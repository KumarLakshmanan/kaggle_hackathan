# The whole winning idea, in 10 lines (conceptual -- not the shipped agent)
RELAY_LEAD = 5                      # sell 5 turns before the scheduled sale, not 3

def should_counter_relay(step):
    # True when our dump lands 2 turns before boatlee's fixed relay
    future_step = step + RELAY_LEAD          # where our sale would land
    return (future_step % 24) == 17          # boatlee's scheduled-sell slot

# Which turns fire? (step 12 with lead 5 -> lands at 17; boatlee dumps at 14)
for step in range(10, 18):
    print(f"step {step:2d} (mod24=={step % 24:2d}): dump={should_counter_relay(step)}")

import matplotlib.pyplot as plt
import numpy as np

# muted palette matching the write-up
INK    = "#111827"
TEAL   = "#0f766e"
SLATE  = "#6b7280"
GREEN  = "#15803d"
RED    = "#b91c1c"
GRID   = "#e5e7eb"
PAGE   = "#ffffff"

plt.rcParams.update({
    "figure.facecolor": PAGE,
    "axes.facecolor": PAGE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": SLATE,
    "ytick.color": SLATE,
    "font.size": 11,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.7,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# --- raw per-game margins (ShiV17 - opponent), verified + reproduced ---
gate_boatlee = [-1253,1609,176,176,176,176,176,176,176,176,176,176,176,176,176,176]
gate_kaito   = [-1216,1646,7930,7930,9633,9633,10065,10065,213,213,213,213,213,213,213,213]

fresh_boatlee = [-1818,2172, 7379,-7063, 870,-514, 176,176, 178,178, 176,176, 176,176, 176,176]
fresh_kaito   = [-1781,2209, 7411,-7034, 9552,8168, 213,213, 215,215, 8895,8895, 6071,6071, 213,213]

print("gate boatlee   :", len(gate_boatlee), "games, mean", round(np.mean(gate_boatlee),1))
print("fresh boatlee  :", len(fresh_boatlee), "games, mean", round(np.mean(fresh_boatlee),1))
print("gate kaito     :", len(gate_kaito), "games, mean", round(np.mean(gate_kaito),1))
print("fresh kaito    :", len(fresh_kaito), "games, mean", round(np.mean(fresh_kaito),1))

# ---- Chart 1: game-level win rate, gate-only vs combined (gate+fresh) ----
labels = ["vs boatlee\n(gate only, 16g)", "vs boatlee\n(combined, 32g)",
          "vs kaitofukami\n(gate only, 16g)", "vs kaitofukami\n(combined, 32g)"]

def win_rate(margins):
    return 100 * sum(1 for m in margins if m > 0) / len(margins)

values = [win_rate(gate_boatlee), win_rate(gate_boatlee + fresh_boatlee),
          win_rate(gate_kaito), win_rate(gate_kaito + fresh_kaito)]
colors = [SLATE, TEAL, SLATE, TEAL]

fig, ax = plt.subplots(figsize=(8.5, 4.5))
bars = ax.bar(labels, values, color=colors, width=0.55)
for bar, v in zip(bars, values):
    ax.annotate(f"{v:.1f}%", (bar.get_x()+bar.get_width()/2, bar.get_height()),
                ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_ylim(0, 105)
ax.set_ylabel("game-level win rate (%)")
ax.set_title("Win rate: original gate-only claim vs corrected combined figure", fontsize=13, fontweight="bold", color=INK, loc="left")
fig.tight_layout()
plt.show()

# ---- Chart 2: per-game margins, all 32 games vs boatlee (gate + fresh) ----
gate_lbls  = [f"g{i+1}" for i in range(16)]
fresh_lbls = [f"f{i+1}" for i in range(16)]
all_lbls = gate_lbls + fresh_lbls
all_margins = gate_boatlee + fresh_boatlee
colors = [GREEN if m > 0 else RED for m in all_margins]

fig, ax = plt.subplots(figsize=(12, 4.5))
ax.bar(np.arange(len(all_margins)), all_margins, color=colors, width=0.7)
ax.axhline(0, color=SLATE, linewidth=1)
ax.axvline(15.5, color=INK, linewidth=1, linestyle="--", alpha=0.4)
ax.text(7.5, ax.get_ylim()[1]*0.85, "gate family", ha="center", fontsize=10, color=SLATE)
ax.text(23.5, ax.get_ylim()[1]*0.85, "fresh seeds", ha="center", fontsize=10, color=SLATE)
ax.set_xticks(np.arange(len(all_lbls)))
ax.set_xticklabels(all_lbls, fontsize=8)
ax.set_ylabel("margin (ShiV17 \u2212 boatlee)")
ax.set_title("All 32 games vs boatlee V16-RC2 \u2014 28W / 4L (87.5%), mean \u0394 +175", fontsize=13, fontweight="bold", color=INK, loc="left")
fig.tight_layout()
plt.show()

# ---- Chart 3: per-game margins, all 32 games vs kaitofukami (gate + fresh) ----
all_margins_k = gate_kaito + fresh_kaito
colors_k = [GREEN if m > 0 else RED for m in all_margins_k]

fig, ax = plt.subplots(figsize=(12, 4.5))
ax.bar(np.arange(len(all_margins_k)), all_margins_k, color=colors_k, width=0.7)
ax.axhline(0, color=SLATE, linewidth=1)
ax.axvline(15.5, color=INK, linewidth=1, linestyle="--", alpha=0.4)
ax.text(7.5, ax.get_ylim()[1]*0.85, "gate family", ha="center", fontsize=10, color=SLATE)
ax.text(23.5, ax.get_ylim()[1]*0.85, "fresh seeds", ha="center", fontsize=10, color=SLATE)
ax.set_xticks(np.arange(len(all_lbls)))
ax.set_xticklabels(all_lbls, fontsize=8)
ax.set_ylabel("margin (ShiV17 \u2212 kaitofukami)")
ax.set_title("All 32 games vs kaitofukami v27 \u2014 29W / 3L (90.6%), mean \u0394 +3,348", fontsize=13, fontweight="bold", color=INK, loc="left")
fig.tight_layout()
plt.show()

import matplotlib.pyplot as plt
import numpy as np

# ShiV17 color palette (keep it consistent)
INDIGO  = "#6d28d9"
VIOLET  = "#8b5cf6"
EMERALD = "#10b981"
CORAL   = "#f43f5e"
AMBER   = "#f59e0b"
SLATE   = "#64748b"
PAGE    = "#f8fafc"

plt.rcParams.update({
    "figure.facecolor": PAGE,
    "axes.facecolor": PAGE,
    "axes.edgecolor": "#cbd5e1",
    "axes.labelcolor": "#1e293b",
    "text.color": "#1e293b",
    "xtick.color": "#475569",
    "ytick.color": "#475569",
    "font.size": 12,
    "axes.grid": True,
    "grid.color": "#e2e8f0",
    "grid.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
})
print("Ship it.")

# ---- Chart 1: win rate, before (V16a) vs after (ShiV17) ----
opponents = ["boatlee V16-RC2", "kaitofukami v27"]
v16a_wr = [0.0, 0.0]                    # 0W / 16L each
shiv17_wr = [93.8, 93.8]                # 15W / 1L each

x = np.arange(len(opponents))
w = 0.34
fig, ax = plt.subplots(figsize=(9, 5))
b1 = ax.bar(x - w/2, v16a_wr, w, label="V16a (before)", color=CORAL, edgecolor="#be123c", linewidth=1)
b2 = ax.bar(x + w/2, shiv17_wr, w, label="ShiV17 (after)", color=EMERALD, edgecolor="#047857", linewidth=1)

for bars in (b1, b2):
    for bar in bars:
        ax.annotate(f"{bar.get_height():.1f}%",
                    (bar.get_x() + bar.get_width()/2, bar.get_height()),
                    ha="center", va="bottom", fontsize=12, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(opponents)
ax.set_ylim(0, 110)
ax.set_ylabel("win rate (%)")
ax.set_title("Win rate vs the tape lords: 0% \u2192 93.8%", fontweight="bold", color=INDIGO, fontsize=15)
ax.legend(frameon=False, loc="upper left")
fig.tight_layout()
plt.show()


# ---- Chart 2: mean delta shift, before vs after ----
opponents = ["vs boatlee V16-RC2", "vs kaitofukami v27"]
v16a_d = [-14735, -13639]
shiv17_d = [176, 3587]

x = np.arange(len(opponents))
w = 0.34
fig, ax = plt.subplots(figsize=(9, 5.2))
b1 = ax.bar(x - w/2, v16a_d, w, label="V16a (before)", color=CORAL, edgecolor="#be123c", linewidth=1)
b2 = ax.bar(x + w/2, shiv17_d, w, label="ShiV17 (after)", color=EMERALD, edgecolor="#047857", linewidth=1)
ax.axhline(0, color="#475569", linewidth=1.1)

for bars in (b1, b2):
    for bar in bars:
        ax.annotate(f"{bar.get_height():+,.0f}",
                    (bar.get_x() + bar.get_width()/2, bar.get_height()),
                    ha="center", va="bottom", fontsize=11, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(opponents)
ax.set_ylabel("mean \u0394 (coins)")
ax.set_title("Mean score delta: from \u221214,735 to +176 / from \u221213,639 to +3,587",
             fontweight="bold", color=INDIGO, fontsize=14)
ax.legend(frameon=False, loc="upper left")
fig.tight_layout()
plt.show()

# The whole winning idea, in 10 lines (conceptual -- not the shipped agent)
RELAY_LEAD = 5                      # sell 5 turns before the scheduled sale, not 3

def should_counter_relay(step):
    # True when our dump lands 2 turns before boatlee's fixed relay
    future_step = step + RELAY_LEAD          # where our sale would land
    return (future_step % 24) == 17          # boatlee's scheduled-sell slot

# Which turns fire? (step 12 with lead 5 -> lands at 17; boatlee dumps at 14)
for step in range(10, 18):
    print(f"step {step:2d} (mod24=={step % 24:2d}): dump={should_counter_relay(step)}")