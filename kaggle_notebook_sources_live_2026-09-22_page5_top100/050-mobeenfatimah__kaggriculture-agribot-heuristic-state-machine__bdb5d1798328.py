import os
import glob
import re
import warnings
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

warnings.filterwarnings('ignore')
pio.renderers.default = "iframe"

# Locate Markdown environment documentation files dynamically
comp_files = glob.glob('/kaggle/input/**/*', recursive=True) or glob.glob('./**/*', recursive=True)
md_files = [f for f in comp_files if f.endswith('.md')]

print(f"Detected {len(md_files)} Simulation Documentation Files:")
for f in md_files:
    print(f" -> {os.path.basename(f)}")

# Parse AGENTS.md or README.md if available
readme_content = ""
for md_path in md_files:
    with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
        readme_content += f"\n--- {os.path.basename(md_path)} ---\n" + f.read()

print(f"\nRules Ingested Successfully ({len(readme_content)} characters). Engine initialized.")

# Simulation Sandbox State Engine for Kaggriculture Tactics
class KaggricultureSimulator:
    def __init__(self, grid_size=10, turns=100):
        self.grid_size = grid_size
        self.turns = turns

    def run_simulation(self, strategy="greedy_harvest"):
        np.random.seed(42)
        grid = np.random.randint(10, 100, size=(self.grid_size, self.grid_size))
        water_levels = np.random.randint(20, 80, size=(self.grid_size, self.grid_size))
        
        agent_pos = [self.grid_size // 2, self.grid_size // 2]
        score = 0
        history = []

        for turn in range(self.turns):
            x, y = agent_pos
            current_yield = grid[x, y]
            current_water = water_levels[x, y]

            if strategy == "greedy_harvest":
                action = "HARVEST" if current_yield > 40 else "MOVE"
            elif strategy == "balanced_irrigation":
                action = "WATER" if current_water < 30 else ("HARVEST" if current_yield > 50 else "MOVE")
            else:
                action = np.random.choice(["HARVEST", "WATER", "MOVE"])

            if action == "HARVEST":
                score += current_yield
                grid[x, y] = max(0, current_yield - 30)
            elif action == "WATER":
                water_levels[x, y] += 25
                grid[x, y] += 10
            elif action == "MOVE":
                dx, dy = np.random.choice([-1, 0, 1]), np.random.choice([-1, 0, 1])
                agent_pos[0] = np.clip(agent_pos[0] + dx, 0, self.grid_size - 1)
                agent_pos[1] = np.clip(agent_pos[1] + dy, 0, self.grid_size - 1)

            history.append({
                "turn": turn,
                "x": agent_pos[0],
                "y": agent_pos[1],
                "action": action,
                "score": score,
                "remaining_yield": grid.sum()
            })

        return pd.DataFrame(history)

sim = KaggricultureSimulator(grid_size=12, turns=150)
df_greedy = sim.run_simulation("greedy_harvest")
df_balanced = sim.run_simulation("balanced_irrigation")

# Interactive Multi-Strategy Score Comparison
fig_score = go.Figure()
fig_score.add_trace(go.Scatter(x=df_greedy['turn'], y=df_greedy['score'], mode='lines', name='Greedy Harvest Strategy', line=dict(color='#84cc16', width=3)))
fig_score.add_trace(go.Scatter(x=df_balanced['turn'], y=df_balanced['score'], mode='lines', name='Balanced Irrigation Strategy', line=dict(color='#06b6d4', width=3)))

fig_score.update_layout(
    title='<b>Section 2: Simulated Strategy Trajectory (Score Accumulation over Turns)</b>',
    xaxis_title='Simulation Turn',
    yaxis_title='Accumulated Score / Yield',
    template='plotly_dark',
    height=450
)
fig_score.show()

# 1. Action Breakdown across Simulation Strategies
df_greedy['strategy'] = 'Greedy Harvest'
df_balanced['strategy'] = 'Balanced Irrigation'
df_combined = pd.concat([df_greedy, df_balanced])

fig_actions = px.histogram(
    df_combined,
    x='action',
    color='strategy',
    barmode='group',
    color_discrete_sequence=['#84cc16', '#06b6d4'],
    title='<b>Section 3: Action Distribution Matrix across Agent Strategies</b>',
    template='plotly_dark',
    height=400
)
fig_actions.show()


# 2. Interactive Spatial Position Path Density Heatmap
fig_path = px.density_heatmap(
    df_balanced,
    x='x',
    y='y',
    title='<b>Agent Field Trajectory & Grid Density Map (Balanced Strategy)</b>',
    template='plotly_dark',
    color_continuous_scale=['#051f15', '#14532d', '#15803d', '#84cc16', '#ecfdf5'],
    height=450
)
fig_path.show()

# Derive Policy Optimization Signals
df_features = df_combined.copy()

df_features['score_velocity'] = df_features.groupby('strategy')['score'].diff().fillna(0)
df_features['turn_efficiency'] = df_features['score'] / (df_features['turn'] + 1)

# Action Encoding
df_features['action_code'] = pd.factorize(df_features['action'])[0]

print("State Feature Engineering Complete.")
df_features[['turn', 'strategy', 'action', 'score_velocity', 'turn_efficiency']].head(5)

# Generate standard submission executable file for Kaggle Simulation Competition
agent_code = '''
import numpy as np

# Kaggriculture Autonomous Agent Strategy
def agent(observation, configuration):
    """
    Autonomous Kaggriculture Agent function executed every simulation turn.
    """
    # Parse state vector
    turn = observation.get("step", 0)
    grid = np.array(observation.get("field", []))
    
    # Default Rule Policy Logic
    if turn < 10:
        return "WATER"
    
    # Heuristic decision trigger
    if np.random.rand() > 0.3:
        return "HARVEST"
    else:
        return "MOVE"
'''

with open("submission_agent.py", "w") as f:
    f.write(agent_code.strip())

print("Section 5: Submission File Generated Successfully!")
print(f"File Path: {os.path.abspath('submission_agent.py')}")
print(f"File Size: {os.path.getsize('submission_agent.py')} bytes")

# Verify local execution of the agent script
import submission_agent

mock_observation = {"step": 1, "field": [[10, 20], [30, 40]]}
mock_configuration = {}

test_action = submission_agent.agent(mock_observation, mock_configuration)
print(f"Section 6: Agent Function Smoke Test Passed.")
print(f"Input Step: {mock_observation['step']} | Agent Decision Output: '{test_action}'")