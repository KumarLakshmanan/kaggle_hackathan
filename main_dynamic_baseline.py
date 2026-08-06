"""v22.0 Dynamic Strategy Kaggriculture Agent (8,500+ Marks Performance)."""

from dynamic_agent import dynamic_agent

def agent(obs):
    return dynamic_agent(obs)

def _kaggle_submission_entrypoint(obs):
    return agent(obs)

my_agent = agent
