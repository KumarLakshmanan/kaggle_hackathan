import pandas as pd
from IPython.display import display, HTML

evolution = [
    {"Approach": "Reactive / Greedy", "Main Idea": "Hardcoded heuristics and immediate harvesting.", "Expected Benefit": "Rapid execution; highly responsive to local state.", "Actual Result": "High standalone yield, but flooded market.", "Lesson": "Execution speed is necessary but insufficient without market awareness."},
    {"Approach": "Global LP Optimization", "Main Idea": "Solve farm allocation mathematically across all tiles.", "Expected Benefit": "Perfect resource allocation.", "Actual Result": "Ignored spatial constraints. Overloaded workers (care lapses).", "Lesson": "Optimization models must respect immediate physical limitations."},
    {"Approach": "Fixed Hiring Schedules", "Main Idea": "Hire on predefined days (e.g., heavily on day 0).", "Expected Benefit": "Predictable wage overhead.", "Actual Result": "Over-hired during quiet periods; severely under-hired during mass harvests.", "Lesson": "Labor must scale dynamically with pending task volume."},
    {"Approach": "Two-Timescale Architecture", "Main Idea": "Decouple market forecasting from turn-by-turn routing.", "Expected Benefit": "Best of both worlds: smart economy, safe routing.", "Actual Result": "Achieved ~550 LB score.", "Lesson": "Strategic and operational decisions require different update frequencies."}
]

display(HTML(pd.DataFrame(evolution).to_html(index=False)))


import matplotlib.pyplot as plt

# Verified snapshot of submission_ledger.csv rows
ledger_snapshot = [
    {"phase": "Phase 3", "score": 600.0, "status": "Baseline"},
    {"phase": "Phase 4b (1)", "score": 330.9, "status": "Failed"},
    {"phase": "Phase 4b (2)", "score": 348.0, "status": "Failed"},
    {"phase": "Phase 6 (Opp Cost)", "score": 504.7, "status": "Validated"},
    {"phase": "Phase 9 (Real Opt)", "score": 0.0, "status": "Failed"},
    {"phase": "Phase 12 (Portfolio)", "score": 0.0, "status": "Failed"}
]

scores = [entry["score"] for entry in ledger_snapshot]
labels = [entry["phase"] for entry in ledger_snapshot]
colors = []

for entry in ledger_snapshot:
    if entry["status"] == "Validated": colors.append('#2ecc71') # Green
    elif entry["status"] == "Failed": colors.append('#e74c3c') # Red
    else: colors.append('#3498db') # Blue

plt.figure(figsize=(12, 5))
plt.plot(range(len(scores)), scores, color='#95a5a6', alpha=0.5, zorder=1)
plt.scatter(range(len(scores)), scores, color=colors, s=100, edgecolor='white', zorder=2)

for i, (label, score) in enumerate(zip(labels, scores)):
    plt.annotate(label, (i, score), textcoords="offset points", xytext=(0,10), 
                 ha='center', fontsize=10, rotation=0, alpha=0.9, fontweight='bold')

plt.title('Agent Architecture Evolution (Verified Ledger Snapshot)', pad=20, fontsize=14, fontweight='bold')
plt.ylabel('Recorded Score (LB / Local Win Rate Proxy)')
plt.xticks([])
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.show()

print("🟢 Hypothesis Validated  |  🔴 Operational Failure  |  🔵 Baseline")


import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(1, 2, figsize=(14, 5))

c_fail = '#ffeaa7'
c_edge = '#2d3436'
c_success = '#55efc4'

# Before
ax[0].axis('off')
ax[0].set_title("BEFORE: The Fragile Monolith", fontsize=12, fontweight='bold')
b1 = patches.Rectangle((0.1, 0.7), 0.8, 0.2, facecolor=c_fail, edgecolor=c_edge, lw=2)
b2 = patches.Rectangle((0.1, 0.4), 0.8, 0.2, facecolor=c_fail, edgecolor=c_edge, lw=2)
b3 = patches.Rectangle((0.1, 0.1), 0.8, 0.2, facecolor='#ff7675', edgecolor=c_edge, lw=2)
ax[0].add_patch(b1); ax[0].text(0.5, 0.8, "Mathematical Economic Model", ha='center', va='center', fontweight='bold')
ax[0].add_patch(b2); ax[0].text(0.5, 0.5, "Direct Specific Actions\n(e.g., 'Harvest at 4,5')", ha='center', va='center')
ax[0].add_patch(b3); ax[0].text(0.5, 0.2, "Execution Failure on\nUnexpected State Shift", ha='center', va='center')
ax[0].annotate('', xy=(0.5, 0.6), xytext=(0.5, 0.7), arrowprops=dict(facecolor=c_edge, shrink=0))
ax[0].annotate('', xy=(0.5, 0.3), xytext=(0.5, 0.4), arrowprops=dict(facecolor=c_edge, shrink=0))

# After
ax[1].axis('off')
ax[1].set_title("AFTER: Precondition-Safe Routing", fontsize=12, fontweight='bold')
a1 = patches.Rectangle((0.1, 0.75), 0.8, 0.15, facecolor=c_success, edgecolor=c_edge, lw=2)
a2 = patches.Rectangle((0.1, 0.55), 0.8, 0.15, facecolor=c_success, edgecolor=c_edge, lw=2)
a3 = patches.Rectangle((0.1, 0.35), 0.8, 0.15, facecolor=c_success, edgecolor=c_edge, lw=2)
a4 = patches.Rectangle((0.1, 0.15), 0.8, 0.15, facecolor='#74b9ff', edgecolor=c_edge, lw=2)
ax[1].add_patch(a1); ax[1].text(0.5, 0.825, "Strategic Model (Generates Targets)", ha='center', va='center', fontweight='bold')
ax[1].add_patch(a2); ax[1].text(0.5, 0.625, "Precondition Checks", ha='center', va='center')
ax[1].add_patch(a3); ax[1].text(0.5, 0.425, "Turn-Level Dynamic Task Router", ha='center', va='center')
ax[1].add_patch(a4); ax[1].text(0.5, 0.225, "Safe Action Execution", ha='center', va='center', fontweight='bold')
ax[1].annotate('', xy=(0.5, 0.7), xytext=(0.5, 0.75), arrowprops=dict(facecolor=c_edge, shrink=0))
ax[1].annotate('', xy=(0.5, 0.5), xytext=(0.5, 0.55), arrowprops=dict(facecolor=c_edge, shrink=0))
ax[1].annotate('', xy=(0.5, 0.3), xytext=(0.5, 0.35), arrowprops=dict(facecolor=c_edge, shrink=0))

plt.tight_layout()
plt.show()


import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(12, 3))
ax.axis('off')

# Base timeline line
ax.plot([0, 10], [1, 1], color='#b2bec3', lw=3, zorder=1)

# Strategic Ticks (Every 3 Days)
for x in [1, 5, 9]:
    ax.scatter(x, 1.5, color='#0984e3', s=200, zorder=3, edgecolors='white', lw=2)
    ax.plot([x, x], [1, 1.5], color='#0984e3', lw=2, linestyle='--', zorder=2)
    ax.text(x, 1.8, f"Day {int(x-1)}\nStrategic Update", ha='center', va='center', fontsize=9, fontweight='bold', color='#0984e3')

# Execution Ticks (Every Hour)
import numpy as np
for x in np.linspace(0.2, 9.8, 30):
    ax.scatter(x, 1, color='#d63031', s=30, zorder=3)

ax.text(5, 0.6, "Execution Layer: Constant Precondition-Safe Routing (Every Tick)", ha='center', va='center', fontsize=10, color='#d63031', fontweight='bold')

plt.title("Diagram 2: The Two-Timescale Rhythm", fontsize=12, fontweight='bold', pad=10)
plt.ylim(0, 2.5)
plt.show()


import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(7, 4))
ax.axis('off')

# Draw Grid
for x in range(7):
    for y in range(4):
        rect = patches.Rectangle((x, y), 1, 1, fill=False, edgecolor='#b2bec3')
        ax.add_patch(rect)

# Draw Entities
# Worker
ax.add_patch(patches.Circle((1.5, 1.5), 0.3, facecolor='#0984e3'))
ax.text(1.5, 1.5, "W", ha='center', va='center', color='white', fontweight='bold')

# Dying Crop (Adjacent)
ax.add_patch(patches.Rectangle((1.1, 2.1), 0.8, 0.8, facecolor='#fab1a0'))
ax.text(1.5, 2.5, "Dying\nWheat\n(Low Val)", ha='center', va='center', fontsize=8)

# Ripe Crop (Distant)
ax.add_patch(patches.Rectangle((5.1, 1.1), 0.8, 0.8, facecolor='#55efc4'))
ax.text(5.5, 1.5, "Ripe\nMelon\n(High Val)", ha='center', va='center', fontsize=8)

# Draw the bad path
ax.annotate('', xy=(5, 1.5), xytext=(1.8, 1.5), arrowprops=dict(facecolor='#d63031', shrink=0, width=2, headwidth=10))
ax.text(3.5, 1.2, "Solver ignores urgent\nadjacent care for distant cash", ha='center', va='center', color='#d63031', fontsize=9, fontweight='bold')

plt.title("Diagram 3: Distance Penalty Interference", fontsize=12, fontweight='bold')
plt.xlim(0, 7)
plt.ylim(0, 4)
plt.show()
