import os

# 1. Define and save the competition agent code
agent_code = '''
def agent(obs, config=None):
    """
    Kaggriculture Production Agent
    Returns the required dictionary structure: {"farmer": action, "hands": [], "market": []}
    """
    try:
        player_idx = obs.get("player", 0)
        farms = obs.get("farms", [])
        
        if not farms or len(farms) <= player_idx:
            return {"farmer": "PASS", "hands": [], "market": []}
            
        me = farms[player_idx]
        money = me.get("money", 0)
        grid = me.get("tiles", me.get("grid", []))
        
        # Priority A: Basic grid maintenance (Till empty tiles)
        for r_idx, row in enumerate(grid):
            for c_idx, tile in enumerate(row):
                if tile is None:
                    return {"farmer": f"TILL {c_idx} {r_idx}", "hands": [], "market": []}

        # Priority B: Buy basic seeds if cash permits
        if money >= 20:
            return {"farmer": "PASS", "hands": [], "market": ["BUY_SEED WHEAT 1"]}

        return {"farmer": "PASS", "hands": [], "market": []}

    except Exception:
        return {"farmer": "PASS", "hands": [], "market": []}
'''

# Write agent code directly to main.py file
with open("main.py", "w") as f:
    f.write(agent_code.strip())

# 2. Verify submission file creation
if os.path.exists("main.py"):
    print("SUCCESS: main.py generated successfully!")
    print(f"File Size: {os.path.getsize('main.py')} bytes")
else:
    print("ERROR: File generation failed.")
