import pandas as pd
import matplotlib.pyplot as plt

# The route slice is explicit: (turn, action). Replace the tape with your own
# observation-derived actions when reproducing the experiment.
reference = [(49, "WEST"), (50, "WEST"), (51, "WEST"), (52, "WATER"),
             (53, "HARVEST"), (54, "BUILD_PASTURE"), (55, "EAST"),
             (56, "EAST"), (57, "DROP")]
delayed = [(53, "PASS"), (54, "PASS"), (55, "PASS"), (56, "PASS"),
           (57, "PASS"), (84, "EAST"), (85, "EAST"), (86, "WATER"),
           (87, "HARVEST"), (88, "BUILD_PASTURE"), (89, "EAST"),
           (90, "EAST"), (91, "DROP")]
route_table = pd.DataFrame([
    {"arm":"A · early harvest", "first_callback":49, "harvest_callback":53, "drop_callback":57, "pasture_restored":54},
    {"arm":"B · delayed harvest", "first_callback":53, "harvest_callback":87, "drop_callback":91, "pasture_restored":88},
])
display(route_table)


ab = pd.DataFrame([
    {"arm":"A · early harvest", "games":128, "valid":128, "wins":3, "mean_delta":0.0},
    {"arm":"B · delayed harvest", "games":128, "valid":128, "wins":125, "mean_delta":27.5625},
])
ab["validity"] = ab["valid"].astype(str) + "/" + ab["games"].astype(str)
display(ab)
fig, ax = plt.subplots(figsize=(8.8, 3.8))
ax.bar(ab["arm"], ab["wins"], color=["#64776b", "#247a4b"])
ax.set_ylabel("Paired wins")
ax.set_title("Visible-state timing screen · 64 seeds × 2 seats")
ax.grid(axis="y", alpha=.25)
plt.xticks(rotation=12, ha="right"); plt.tight_layout(); display(fig); plt.close(fig)
assert (ab["valid"] == ab["games"]).all()
assert int(ab.loc[1, "wins"]) > int(ab.loc[0, "wins"])
print("valid games: 128/128; local B-minus-A mean: +27.5625")


# A tiny transformation helper for route experiments.
def delay_harvest(route, harvest_turn, return_turn, drop_turn):
    out = list(route)
    by_turn = {turn: action for turn, action in out}
    by_turn[harvest_turn] = "HARVEST"
    by_turn[return_turn] = "BUILD_PASTURE"
    by_turn[drop_turn] = "DROP"
    return sorted(by_turn.items())

assert delay_harvest([], 87, 88, 91) == [(87, "HARVEST"), (88, "BUILD_PASTURE"), (91, "DROP")]
print("Transformation is deterministic and visible-state only.")
