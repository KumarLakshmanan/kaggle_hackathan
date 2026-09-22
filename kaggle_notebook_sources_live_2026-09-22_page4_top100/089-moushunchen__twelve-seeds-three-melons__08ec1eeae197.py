from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS, CROPS

print("CROPS")
for name, row in CROPS.items():
    kind = "ongoing" if row["ongoing"] else "one-shot"
    print(
        f"  {name:12s} seed=${row['seed']:<4}  first={row['first_yield_day']:<2}  "
        f"max_day={row['max_yield_day']:<2}  max_yield={row['max_yield']}  {kind}"
    )

print("\nANIMALS")
for name, row in ANIMALS.items():
    print(
        f"  {name:12s} ${row['cost']}  {row['structure']:8s}  "
        f"first={row['first_yield_day']}  every {row['interval']}d  → {row['product']}"
    )


from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS

# From kaggle_environments 1.32.7 — HARVEST, abbreviated.
# One-shot crops spawn with yield_units = 1, so this branch is live from hour one.
# If age < first_yield_day, HARVEST returns without removing the plant.
# Your worker still used the turn.

print("melon first_yield_day =", CROPS["MELON"]["first_yield_day"])
print("wheat first_yield_day =", CROPS["WHEAT"]["first_yield_day"])
print("one-shot spawn yield_units = 1")
print("ongoing spawn yield_units = 0")
print()
print("Watering bonus window for one-shot crops starts at ceil(max_yield_day / 2).")
print("melon bonus water: days", (CROPS["MELON"]["max_yield_day"] + 1) // 2, "to", CROPS["MELON"]["max_yield_day"])
print("Do not pull the patch on day 0 because the integer looks ripe.")
