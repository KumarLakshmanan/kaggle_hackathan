
# Install the latest Kaggle environments package
# !pip install -U kaggle-environments

from kaggle_environments import make

# Create the environment!
env = make("kaggriculture", debug=True)
print("Environment created successfully!")



# Get the initial observation from the environment
initial_state = env.reset()
obs = initial_state[0].observation

player_index = obs["player"]
my_farm = obs["farms"][player_index]

print(f"I am player: {player_index}")
print(f"My starting money: ${my_farm['money']}")
print(f"Initial WHEAT price: ${obs['market']['prices']['WHEAT']}")



def handle_market(private_info, my_farm):
    orders = []
    # If we have no wheat seeds and enough money, buy 1 seed
    if private_info["seeds"].get("WHEAT", 0) == 0 and my_farm["money"] >= 10:
        orders.append(["BUY_SEED", "WHEAT", 1])
    
    # If we have harvested wheat in our shed, sell it!
    wheat_in_shed = private_info["shed"].get("WHEAT", 0)
    if wheat_in_shed > 0:
        orders.append(["SELL", "WHEAT", wheat_in_shed])
        
    return orders



def handle_planting(tile, private_info):
    # If the tile is empty and we have a seed, plant it!
    if tile is None and private_info["seeds"].get("WHEAT", 0) > 0:
        return ["PLANT", "WHEAT"]
    return None



def handle_plant_care(tile, current_day):
    # Check if the tile has a plant
    if isinstance(tile, dict) and tile.get("kind") == "PLANT":
        crop_age = current_day - tile["planted_day"]
        
        if crop_age >= 2:  # Wheat is fully grown after 2 days
            return ["HARVEST"]
        if not tile["watered_today"]:
            return ["WATER"]
            
    return None



def my_wheat_farmer(obs):
    p = obs["player"]
    my_farm = obs["farms"][p]
    priv = obs["private"]
    
    fx, fy = my_farm["farmer"]
    tile = my_farm["tiles"][fy][fx]
    
    orders = handle_market(priv, my_farm)
    action = handle_planting(tile, priv)
    
    if action is None:
        action = handle_plant_care(tile, obs["day"])
    if action is None:
        action = ["PASS"]
        
    return {"farmer": action, "hands": [], "market": orders}



print("Running a full season...")
# We run our farmer as Player 1, and the built-in "random" agent as Player 2
my_player_index = 0
env.run([my_wheat_farmer, "random"])

final_rewards = [s.reward for s in env.steps[-1]]
print(f"Game finished! Our reward (money): ${final_rewards[my_player_index]}")
print(f"Opponent reward (money): ${final_rewards[1 - my_player_index]}")



print(f"{'Turn':<6} | {'Day':<4} | {'My Money':<10} | {'Wheat in Shed':<15}")
print("-" * 45)

for step_idx in range(0, len(env.steps), 120):
    # Dynamically reference our player's state based on our assigned index
    my_step_data = env.steps[step_idx][my_player_index]
    
    if my_step_data.observation and "farms" in my_step_data.observation:
        obs_at_step = my_step_data.observation
        p_idx = obs_at_step["player"]
        
        my_money = obs_at_step["farms"][p_idx]["money"]
        day = obs_at_step["day"]
        
        try:
            my_wheat = obs_at_step["private"]["shed"].get("WHEAT", 0)
            wheat_str = str(my_wheat)
        except KeyError as e:
            wheat_str = f"(Error: {e} not found)"
            
        print(f"{step_idx:<6} | {day:<4} | ${my_money:<9.1f} | {wheat_str:<15}")
