def agent(obs):
    player = obs["player"]
    me = obs["farms"][player]
    private = obs["private"]

    farmer_x, farmer_y = me["farmer"]
    tile = me["tiles"][farmer_y][farmer_x]

    market = []

    # Sell harvested products from shed
    for item, amount in private["shed"].items():
        if amount > 0 and item != "FERTILIZER":
            market.append(["SELL", item, amount])

    # Buy wheat seed if we have none
    if private["seeds"].get("WHEAT", 0) == 0:
        if me["money"] >= 10:
            market.append(["BUY_SEED", "WHEAT", 1])

    # Empty tile -> plant wheat
    if tile is None:
        if private["seeds"].get("WHEAT", 0) > 0:
            return {
                "farmer": ["PLANT", "WHEAT"],
                "hands": [],
                "market": market
            }

        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": market
        }

    # Plant -> water / harvest
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":

        # Water once per day
        if not tile.get("watered_today", False):
            return {
                "farmer": ["WATER"],
                "hands": [],
                "market": market
            }

        # Harvest wheat after 2 days
        age = obs["day"] - tile.get("planted_day", obs["day"])

        if age >= 2:
            return {
                "farmer": ["HARVEST"],
                "hands": [],
                "market": market
            }

    return {
        "farmer": ["PASS"],
        "hands": [],
        "market": market
    }

from kaggle_environments import make

env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 720
    },
    debug=True
)

env.run([agent, "random"])

final = env.steps[-1]

for i, s in enumerate(final):
    print(f"Player {i}: reward={s.reward}, status={s.status}")

print("Game completed!")