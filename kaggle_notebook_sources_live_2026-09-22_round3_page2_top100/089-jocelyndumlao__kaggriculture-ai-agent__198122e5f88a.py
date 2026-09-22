# 1. ENVIRONMENT & REPOSITORY SETUP

from pathlib import Path
import sys
import os
import json
import re
import ast
import math
import shutil
import subprocess
from collections import Counter, defaultdict

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from IPython.display import display, Markdown

print("🌾 KAGGRICULTURE AI AGENT")
print("=" * 75)

# Detect Kaggle

IS_KAGGLE = Path("/kaggle/working").exists()

print(f"💻 Kaggle environment: {IS_KAGGLE}")
print(f"🐍 Python executable: {sys.executable}")

# Project root

PROJECT_ROOT = Path("/kaggle/working/Kaggriculture-AI-Agent")
if not PROJECT_ROOT.exists():
    !git clone https://github.com/jcdumlao14/Kaggriculture-AI-Agent.git {PROJECT_ROOT}

# Add project to Python path

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SRC_DIR = PROJECT_ROOT / "src"

print(f"📦 src/ exists: {SRC_DIR.exists()}")

if not SRC_DIR.exists():
    raise FileNotFoundError(
        f"src directory was not found: {SRC_DIR}"
    )

print("✅ Environment setup complete.")

from pathlib import Path

# Find the Kaggriculture project and market.py automatically
working = Path("/kaggle/working")

matches = list(working.rglob("market.py"))

print(f"Found {len(matches)} market.py file(s):")

for p in matches:
    print(" -", p)

if not matches:
    raise FileNotFoundError(
        "market.py was not found under /kaggle/working. "
        "Please run the repository clone/download cell first."
    )

# Check every market.py found
for p in matches:
    data = p.read_bytes()

    print(f"\nChecking: {p}")
    print("BOM:", data.startswith(b"\xef\xbb\xbf"))
    print("First bytes:", data[:20])

# 2. REPOSITORY VERIFICATION

print("📦 KAGGRICULTURE AI AGENT — REPOSITORY")
print("=" * 75)

for item in sorted(PROJECT_ROOT.iterdir()):
    if item.name == ".git":
        print("📁 .git/")
    elif item.is_dir():
        print(f"📁 {item.name}/")
    else:
        print(f"📄 {item.name}")

print("\n✅ Repository verification complete.")

# 2B. VERIFY GIT REPOSITORY STATE

def run_git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

stdout, stderr, code = run_git("status", "--short")

print("🔎 Git status:")
print(stdout if stdout else "Working tree clean.")

stdout, stderr, code = run_git(
    "log",
    "-1",
    "--oneline"
)

print("\n📝 Latest commit:")
print(stdout)

print("\n✅ Git repository verified.")

# 3. GAME CONFIGURATION

TOTAL_DAYS = 30
TURNS_PER_DAY = 24
TOTAL_TURNS = TOTAL_DAYS * TURNS_PER_DAY

STARTING_MONEY = 3000
BOARD_SIZE = 10

print("🎮 KAGGRICULTURE GAME CONFIGURATION")
print("=" * 75)

print(f"📅 Season length: {TOTAL_DAYS} days")
print(f"⏱️ Turns per day: {TURNS_PER_DAY}")
print(f"🎯 Total turns: {TOTAL_TURNS}")
print(f"💰 Starting money: ${STARTING_MONEY:,}")
print(f"🗺️ Board size: {BOARD_SIZE} × {BOARD_SIZE}")

assert TOTAL_TURNS == 720

print("\n✅ Configuration verified.")

# 4. CROP PRODUCTION & PROFITABILITY

CROPS = {
    "WHEAT": {
        "seed_cost": 10,
        "selling_price": 25,
        "first_yield_day": 2,
        "max_yield_day": 4,
        "interval": None,
        "max_yield": 6,
        "ongoing": False,
    },

    "CARROT": {
        "seed_cost": 20,
        "selling_price": 35,
        "first_yield_day": 2,
        "max_yield_day": 3,
        "interval": None,
        "max_yield": 4,
        "ongoing": False,
    },

    "TOMATO": {
        "seed_cost": 50,
        "selling_price": 60,
        "first_yield_day": 8,
        "max_yield_day": 8,
        "interval": 1,
        "max_yield": 4,
        "ongoing": True,
    },

    "STRAWBERRY": {
        "seed_cost": 100,
        "selling_price": 120,
        "first_yield_day": 10,
        "max_yield_day": 10,
        "interval": 2,
        "max_yield": 4,
        "ongoing": True,
    },

    "MELON": {
        "seed_cost": 80,
        "selling_price": 250,
        "first_yield_day": 10,
        "max_yield_day": 12,
        "interval": None,
        "max_yield": 6,
        "ongoing": False,
    },
}

crop_rows = []

for crop, info in CROPS.items():

    gross_revenue = (
        info["selling_price"] * info["max_yield"]
    )

    gross_margin = gross_revenue - info["seed_cost"]

    crop_rows.append({
        "Crop": crop,
        "Seed Cost": info["seed_cost"],
        "Selling Price": info["selling_price"],
        "First Yield Day": info["first_yield_day"],
        "Max Yield Day": info["max_yield_day"],
        "Max Yield": info["max_yield"],
        "Gross Revenue": gross_revenue,
        "Gross Margin": gross_margin,
        "Margin / Production Day": (
            gross_margin / info["max_yield_day"]
        ),
    })

crop_df = pd.DataFrame(crop_rows)

display(
    crop_df.sort_values(
        "Gross Margin",
        ascending=False
    ).reset_index(drop=True)
)

# 4B. CROP PROFITABILITY VISUALIZATION

plot_df = crop_df.sort_values(
    "Gross Margin",
    ascending=False
)

plt.figure(figsize=(10, 5))

plt.bar(
    plot_df["Crop"],
    plot_df["Gross Margin"]
)

plt.title("Crop Gross Margin Comparison")
plt.xlabel("Crop")
plt.ylabel("Gross Margin")

plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

# 5. ANIMAL PRODUCTION & MANAGEMENT

ANIMALS = {
    "GOOSE": {
        "product": "EGG",
        "purchase_cost": 300,
        "selling_price": 50,
        "first_yield_day": 4,
        "production_interval": 1,
        "max_held": 4,
        "structure": "COOP",
    },

    "COW": {
        "product": "MILK",
        "purchase_cost": 400,
        "selling_price": 160,
        "first_yield_day": 8,
        "production_interval": 2,
        "max_held": 6,
        "structure": "PASTURE",
    },

    "SHEEP": {
        "product": "WOOL",
        "purchase_cost": 500,
        "selling_price": 200,
        "first_yield_day": 6,
        "production_interval": 3,
        "max_held": 6,
        "structure": "PASTURE",
    },
}

animal_rows = []

for animal, info in ANIMALS.items():

    available_days = (
        TOTAL_DAYS - info["first_yield_day"]
    )

    production_events = (
        1
        + available_days // info["production_interval"]
    )

    gross_revenue = (
        production_events
        * info["selling_price"]
    )

    gross_margin_before_feed = (
        gross_revenue
        - info["purchase_cost"]
    )

    animal_rows.append({
        "Animal": animal,
        "Product": info["product"],
        "Purchase Cost": info["purchase_cost"],
        "Selling Price": info["selling_price"],
        "First Yield Day": info["first_yield_day"],
        "Production Interval": info["production_interval"],
        "30-Day Production Events": production_events,
        "Gross Revenue": gross_revenue,
        "Gross Margin Before Feed": gross_margin_before_feed,
        "Structure": info["structure"],
    })

animal_df = pd.DataFrame(animal_rows)

display(
    animal_df.sort_values(
        "Gross Margin Before Feed",
        ascending=False
    ).reset_index(drop=True)
)

# 5B. DETECT FEED / ANIMAL ECONOMICS FROM SOURCE

animal_source_records = []

for path in SRC_DIR.rglob("*.py"):

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    except Exception:
        continue

    lower = text.lower()

    if (
        "feed" in lower
        or "wheat" in lower
        or "animal" in lower
    ):
        animal_source_records.append(
            str(path.relative_to(PROJECT_ROOT))
        )

print(
    f"🐄 Source files containing animal/feed logic: "
    f"{len(set(animal_source_records))}"
)

for path in sorted(set(animal_source_records)):
    print(" •", path)

# 5C. ANIMAL 30-DAY PRODUCTION

animal_plot = animal_df.copy()

plt.figure(figsize=(10, 5))

plt.bar(
    animal_plot["Animal"],
    animal_plot["30-Day Production Events"]
)

plt.title(
    "Estimated Animal Production Events Over 30 Days"
)

plt.xlabel("Animal")
plt.ylabel("Production Events")

plt.tight_layout()
plt.show()

# 5D. ANIMAL GROSS REVENUE

plt.figure(figsize=(10, 5))

plt.bar(
    animal_plot["Animal"],
    animal_plot["Gross Revenue"]
)

plt.title(
    "Animal Gross Revenue Over 30-Day Production Horizon"
)

plt.xlabel("Animal")
plt.ylabel("Gross Revenue")

plt.tight_layout()
plt.show()

best_revenue = animal_df.loc[
    animal_df["Gross Revenue"].idxmax()
]

best_margin = animal_df.loc[
    animal_df["Gross Margin Before Feed"].idxmax()
]

print("🐄 ANIMAL ECONOMIC SUMMARY")
print("=" * 70)

print(
    f"Highest gross revenue: "
    f"{best_revenue['Animal']} "
    f"(${best_revenue['Gross Revenue']:,.0f})"
)

print(
    f"Highest gross margin before feed: "
    f"{best_margin['Animal']} "
    f"(${best_margin['Gross Margin Before Feed']:,.0f})"
)

print(
    "\n⚠️ These figures exclude daily wheat feed cost and "
    "labor/action costs."
)
print(
    "The final profitability analysis should therefore "
    "use observed simulation data where available."
)

# 6. ACTION INVENTORY

print("🤖 KAGGRICULTURE AI AGENT — ACTION INVENTORY")
print("=" * 75)

ACTION_KEYWORDS = [
    "NORTH",
    "SOUTH",
    "EAST",
    "WEST",
    "PASS",
    "WATER",
    "HARVEST",
    "FEED",
    "CARE",
    "FERTILIZE",
    "COLLECT_FERTILIZER",
    "DIG",
    "PLANT",
    "SELL",
    "BUY_PRODUCT",
    "BUY_SEED",
    "BUY_ANIMAL",
    "BUY_LAND",
    "HIRE",
    "PLACE",
    "BUILD_PASTURE",
    "BUILD_COOP",
    "DROP",
    "PICKUP",
]

action_records = []

for path in SRC_DIR.rglob("*.py"):

    try:
        lines = path.read_text(
            encoding="utf-8",
            errors="ignore"
        ).splitlines()
    except Exception:
        continue

    for line_number, line in enumerate(
        lines,
        start=1
    ):

        upper = line.upper()

        matched = [
            action
            for action in ACTION_KEYWORDS
            if action in upper
        ]

        for action in matched:

            action_records.append({
                "Action": action,
                "File": str(
                    path.relative_to(PROJECT_ROOT)
                ),
                "Line": line_number,
                "Code": line.strip(),
            })

action_df = pd.DataFrame(action_records)

print(
    f"🤖 Action-related references found: "
    f"{len(action_df):,}"
)

display(action_df.head(50))

# 6B. ACTION FREQUENCY

action_frequency = (
    action_df["Action"]
    .value_counts()
    .rename_axis("Action")
    .reset_index(name="References")
)

display(action_frequency)

# 6C. ACTION FREQUENCY VISUALIZATION

plot_actions = action_frequency.head(15)

plt.figure(figsize=(12, 6))

plt.bar(
    plot_actions["Action"],
    plot_actions["References"]
)

plt.title("Most Frequently Referenced Actions")
plt.xlabel("Action")
plt.ylabel("Source-Code References")

plt.xticks(
    rotation=60,
    ha="right"
)

plt.tight_layout()
plt.show()

# 6D. ACTION CATEGORIES

ACTION_CATEGORIES = {
    "Movement": {
        "NORTH", "SOUTH", "EAST", "WEST"
    },

    "Crop Production": {
        "DIG", "PLANT", "WATER", "HARVEST",
        "FERTILIZE"
    },

    "Animal Management": {
        "FEED", "CARE", "COLLECT_FERTILIZER"
    },

    "Economics": {
        "SELL", "BUY_PRODUCT", "BUY_SEED",
        "BUY_ANIMAL", "BUY_LAND"
    },

    "Labor": {
        "HIRE"
    },

    "Infrastructure": {
        "BUILD_PASTURE", "BUILD_COOP"
    },

    "Inventory": {
        "PLACE", "DROP", "PICKUP"
    },

    "Control": {
        "PASS"
    },
}

category_records = []

for category, actions in ACTION_CATEGORIES.items():

    count = action_df[
        action_df["Action"].isin(actions)
    ].shape[0]

    category_records.append({
        "Category": category,
        "References": count,
    })

category_df = pd.DataFrame(
    category_records
).sort_values(
    "References",
    ascending=False
)

display(category_df)

# 7. AGENT ARCHITECTURE — MODULE INVENTORY

print("🧠 KAGGRICULTURE AI AGENT — ARCHITECTURE")
print("=" * 75)

python_files = sorted(
    SRC_DIR.rglob("*.py")
)

module_records = []

for path in python_files:

    relative = path.relative_to(PROJECT_ROOT)

    try:
        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    except Exception:
        continue

    module_records.append({
        "Module": str(relative),
        "Lines": len(text.splitlines()),
        "Bytes": path.stat().st_size,
    })

module_df = pd.DataFrame(module_records)

display(
    module_df.sort_values(
        "Lines",
        ascending=False
    ).reset_index(drop=True)
)

# 7B. CLASSES & FUNCTIONS

class_records = []
function_records = []

for path in SRC_DIR.rglob("*.py"):

    try:
        source = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        tree = ast.parse(source)

    except Exception:
        continue

    relative = str(
        path.relative_to(PROJECT_ROOT)
    )

    for node in ast.walk(tree):

        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            function_records.append({
                "File": relative,
                "Function": node.name,
                "Line": node.lineno,
            })

        elif isinstance(
            node,
            ast.ClassDef
        ):
            class_records.append({
                "File": relative,
                "Class": node.name,
                "Line": node.lineno,
            })

classes_df = pd.DataFrame(
    class_records
)

functions_df = pd.DataFrame(
    function_records
)

print(
    f"🏗️ Classes detected: "
    f"{len(classes_df)}"
)

print(
    f"⚙️ Functions detected: "
    f"{len(functions_df)}"
)

print("\nClasses:")
display(classes_df)

print("\nFunctions:")
display(
    functions_df.head(100)
)

# 8. ANIMAL IMPLEMENTATION VERIFICATION

print("🐄 KAGGRICULTURE AI AGENT — ANIMAL VERIFICATION")
print("=" * 75)

ANIMAL_KEYWORDS = [
    "animal",
    "feed",
    "care",
    "milk",
    "egg",
    "meat",
    "wool",
    "livestock",
    "chicken",
    "cow",
    "pig",
    "sheep",
    "goat",
    "goose",
]

animal_records = []

for path in SRC_DIR.rglob("*.py"):

    try:
        lines = path.read_text(
            encoding="utf-8",
            errors="ignore"
        ).splitlines()

    except Exception:
        continue

    for line_number, line in enumerate(
        lines,
        start=1
    ):

        line_lower = line.lower()

        matched_keywords = [
            keyword
            for keyword in ANIMAL_KEYWORDS
            if keyword in line_lower
        ]

        if matched_keywords:

            animal_records.append({
                "File": str(
                    path.relative_to(PROJECT_ROOT)
                ),
                "Line": line_number,
                "Keywords": ", ".join(
                    sorted(
                        set(matched_keywords)
                    )
                ),
                "Code": line.strip(),
            })

animal_analysis = pd.DataFrame(
    animal_records
)

if animal_analysis.empty:

    print(
        "⚠️ No animal-related implementation "
        "was detected."
    )

else:

    print(
        f"🐄 Animal-related code references found: "
        f"{len(animal_analysis):,}"
    )

    display(
        animal_analysis.head(50)
    )

# 8B. ANIMAL REFERENCES BY FILE

if not animal_analysis.empty:

    animal_by_file = (
        animal_analysis
        .groupby("File")
        .size()
        .reset_index(
            name="Animal References"
        )
        .sort_values(
            "Animal References",
            ascending=False
        )
    )

    display(animal_by_file)

# 8C. ANIMAL REFERENCES BY FILE

top_animal_files = animal_by_file.head(15)

plt.figure(figsize=(12, 7))

plt.barh(
    top_animal_files["File"][::-1],
    top_animal_files["Animal References"][::-1]
)

plt.title(
    "Top Source Files by Animal-Related References"
)

plt.xlabel("References")
plt.ylabel("Source File")

plt.tight_layout()
plt.show()

# 9. KAGGRICULTURE SIMULATION AVAILABILITY

print("🚜 KAGGRICULTURE — SIMULATION CHECK")
print("=" * 75)

try:
    from kaggle_environments import make

    HAVE_KAGGLE_ENV = True

    print(
        "✅ kaggle_environments is available."
    )

except ModuleNotFoundError:

    HAVE_KAGGLE_ENV = False

    print(
        "⚠️ kaggle_environments is not installed."
    )

print(
    f"Environment available: "
    f"{HAVE_KAGGLE_ENV}"
)

# 9B. MAIN AGENT INTERFACE

from pathlib import Path

MAIN_PATH = PROJECT_ROOT / "main.py"

print("🔧 Fixing main.py")
print("=" * 70)

main_code = '''from __future__ import annotations

from src.agent import Agent


# ============================================================
# KAGGRICULTURE AI AGENT
# ============================================================

_agent = Agent()


def agent(obs, config=None):
    """
    Kaggriculture AI Agent entry point.

    Parameters
    ----------
    obs : dict
        Current Kaggriculture game observation.

    config : optional
        Kaggle environment configuration.

    Returns
    -------
    dict
        Action generated by the Kaggriculture agent.
    """

    return _agent.act(obs)
'''

MAIN_PATH.write_text(
    main_code,
    encoding="utf-8"
)

print(f"✅ main.py updated:")
print(f"   {MAIN_PATH}")
print()
print(main_code)

# 9B. VERIFY MAIN AGENT

import re

main_source = MAIN_PATH.read_text(
    encoding="utf-8",
    errors="ignore"
)

print("📄 Main agent:")
print(MAIN_PATH)

print(f"\n📏 Lines: {len(main_source.splitlines()):,}")
print(f"📦 Size: {MAIN_PATH.stat().st_size:,} bytes")

print(
    "\n🔎 agent() detected:",
    bool(
        re.search(
            r"\bdef\s+agent\s*\(",
            main_source
        )
    )
)

print(
    "🔎 Agent imported:",
    "from src.agent import Agent" in main_source
)

# 9C. IMPORT AGENT

import importlib.util
import sys

print("🤖 Loading Kaggriculture AI Agent")
print("=" * 70)

# Make sure project root is available
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load main.py
spec = importlib.util.spec_from_file_location(
    "kaggriculture_main",
    MAIN_PATH
)

if spec is None or spec.loader is None:
    raise ImportError(
        f"Unable to create import specification for {MAIN_PATH}"
    )

agent_module = importlib.util.module_from_spec(spec)

spec.loader.exec_module(agent_module)

# Verify Kaggle entry point
if not hasattr(agent_module, "agent"):
    raise AttributeError(
        "main.py does not expose agent()."
    )

agent_function = agent_module.agent

print("✅ Agent successfully loaded!")
print()
print("Agent function:")
print(agent_function)

# 9D. REAL KAGGRICULTURE ENVIRONMENT TEST


print("🚜 Testing agent with a real Kaggriculture observation")
print("=" * 70)

try:
    from kaggle_environments import make

    print("✅ kaggle_environments imported")

except ModuleNotFoundError as e:
    print("❌ kaggle_environments is not installed.")
    raise e


# Create real Kaggriculture environment


env = make(
    "kaggriculture",
    configuration={
        "episodeSteps": 720,
        "seed": 42,
    },
    debug=False,
)

print("✅ Kaggriculture environment created")


# Inspect initial observation


# Reset environment
env.reset()

print("\n🔎 Environment reset successfully")

print("\nEnvironment object:")
print(type(env))


# Try to obtain the initial observation
try:
    initial_obs = env.state[0].observation

except Exception:
    initial_obs = None


if initial_obs is None:

    print(
        "\n⚠️ Initial observation was not directly available "
        "from env.state."
    )

    print(
        "We will inspect the environment state instead."
    )

    print("\nEnvironment state:")
    print(env.state)

else:

    print("\n✅ Initial observation obtained")

    print(
        "\nObservation keys:"
    )

    for key in sorted(initial_obs.keys()):
        print(f"   • {key}")


    # Verify required fields
    

    print("\n🔎 Required game-state fields:")
    
    required_fields = [
        "step",
        "day",
        "hour",
        "player",
        "farms",
        "private",
        "market",
        "town",
    ]

    for field in required_fields:

        print(
            f"   {'✅' if field in initial_obs else '❌'} "
            f"{field}"
        )

# 9D. CREATE KAGGRICULTURE EPISODE

episode = None

if HAVE_KAGGLE_ENV:

    print(
        "🚜 Creating Kaggriculture simulation..."
    )

    env = make(
        "kaggriculture",
        configuration={
            "episodeSteps": 720,
            "seed": 42,
        },
        debug=False,
    )

    print(
        "✅ Kaggriculture environment created."
    )

else:

    print(
        "⚠️ Simulation skipped because "
        "kaggle_environments is unavailable."
    )

# 9E. RUN CONTROLLED EPISODE

replay = None

if HAVE_KAGGLE_ENV:

    print(
        "🎮 Running 720-turn simulation..."
    )

    env.run([
        agent_function,
        "random",
    ])

    replay = env.toJSON()

    print("✅ Episode completed.")

    print(
        "Rewards:",
        replay.get("rewards")
    )

    print(
        "Steps:",
        len(replay.get("steps", []))
    )

# 9F. REPLAY ANALYSIS

if replay is not None:

    steps = replay.get(
        "steps",
        []
    )

    print(
        f"🎮 Total replay steps: "
        f"{len(steps)}"
    )

    if replay.get("rewards") is not None:

        print(
            "🏆 Rewards:",
            replay["rewards"]
        )

# 9G. GAMEPLAY ACTION ANALYSIS

gameplay_actions = []

if replay is not None:

    for step_index, step_data in enumerate(
        replay.get("steps", [])
    ):

        for player_id, player_data in enumerate(
            step_data
        ):

            action = player_data.get(
                "action"
            )

            if not action:
                continue

            farmer_action = action.get(
                "farmer"
            )

            if farmer_action:
                gameplay_actions.append({
                    "Step": step_index,
                    "Player": player_id,
                    "Action": farmer_action[0],
                })

            for hand_action in (
                action.get("hands", [])
                or []
            ):

                if hand_action:
                    gameplay_actions.append({
                        "Step": step_index,
                        "Player": player_id,
                        "Action": hand_action[0],
                    })

gameplay_action_df = pd.DataFrame(
    gameplay_actions
)

if not gameplay_action_df.empty:

    print(
        f"🎮 Gameplay action records: "
        f"{len(gameplay_action_df):,}"
    )

    display(
        gameplay_action_df.head(30)
    )

    gameplay_frequency = (
        gameplay_action_df["Action"]
        .value_counts()
        .reset_index()
    )

    gameplay_frequency.columns = [
        "Action",
        "Count"
    ]

    display(
        gameplay_frequency
    )

# 10. PERFORMANCE DASHBOARD

print("📊 KAGGRICULTURE AI AGENT — PERFORMANCE DASHBOARD")
print("=" * 75)

dashboard = {
    "Repository Python Files": len(python_files),
    "Detected Classes": len(classes_df),
    "Detected Functions": len(functions_df),
    "Action References": len(action_df),
    "Animal References": (
        len(animal_analysis)
        if not animal_analysis.empty
        else 0
    ),
    "Simulation Available": HAVE_KAGGLE_ENV,
    "Simulation Steps": (
        len(replay.get("steps", []))
        if replay is not None
        else 0
    ),
}

dashboard_df = pd.DataFrame(
    dashboard.items(),
    columns=["Metric", "Value"]
)

display(dashboard_df)

# 10B. SOURCE-CODE DASHBOARD

dashboard_plot = pd.DataFrame({
    "Metric": [
        "Python Files",
        "Classes",
        "Functions",
        "Action References",
        "Animal References",
    ],

    "Count": [
        len(python_files),
        len(classes_df),
        len(functions_df),
        len(action_df),
        len(animal_analysis)
        if not animal_analysis.empty
        else 0,
    ]
})

plt.figure(figsize=(10, 6))

plt.bar(
    dashboard_plot["Metric"],
    dashboard_plot["Count"]
)

plt.title(
    "Kaggriculture AI Agent — Project Analysis Dashboard"
)

plt.ylabel("Count")

plt.xticks(
    rotation=30,
    ha="right"
)

plt.tight_layout()
plt.show()

# 11. KEY FINDINGS

print("🏆 KAGGRICULTURE AI AGENT — KEY FINDINGS")
print("=" * 75)

print("""
🌾 PROJECT
The Kaggriculture AI Agent is designed for a two-player farming
simulation where agents manage crops, livestock, labor, movement,
inventory and market transactions over a 30-day season.

🎮 GAME
The simulation consists of 30 days and 720 turns.

🌱 CROPS
The environment contains Wheat, Carrot, Tomato, Strawberry and Melon.
Each crop has different seed costs, production timing, yields and
market values.

🐄 ANIMALS
The livestock system contains:
    • Goose → Egg
    • Cow → Milk
    • Sheep → Wool

Animals require daily feeding and can receive CARE actions that
affect production.

🤖 ACTIONS
The source-code analysis identifies the project's action vocabulary
and measures how frequently each action is referenced.

🧠 AGENT ARCHITECTURE
The project separates game behavior into reusable source modules,
classes and functions.

📊 ECONOMICS
Animal and crop profitability should be evaluated using production,
market prices, feed/seed costs, labor and the remaining season horizon.

🚜 SIMULATION
A controlled Kaggriculture episode provides an additional validation
layer beyond static source-code analysis.
""")

# 12. CREATE DEPENDENCY-SAFE KAGGLE SUBMISSION

from pathlib import Path
import ast
import re
import shutil
import textwrap

SUBMISSION_PATH = Path(
    "/kaggle/working/submission.py"
)

print("📦 BUILDING DEPENDENCY-SAFE KAGGLE SUBMISSION")
print("=" * 80)

# 12A. PROJECT PATHS

PROJECT_ROOT = Path(
    "/kaggle/working/Kaggriculture-AI-Agent"
)

SRC_DIR = PROJECT_ROOT / "src"
MAIN_PATH = PROJECT_ROOT / "main.py"

if not PROJECT_ROOT.exists():
    raise FileNotFoundError(
        f"Project directory not found: {PROJECT_ROOT}"
    )

if not SRC_DIR.exists():
    raise FileNotFoundError(
        f"src directory not found: {SRC_DIR}"
    )

if not MAIN_PATH.exists():
    raise FileNotFoundError(
        f"main.py not found: {MAIN_PATH}"
    )

print(f"📁 Project root : {PROJECT_ROOT}")
print(f"📁 Source dir   : {SRC_DIR}")
print(f"📄 Main file    : {MAIN_PATH}")
print()

# 12B. READ MAIN.PY

main_source = MAIN_PATH.read_text(
    encoding="utf-8",
    errors="ignore"
)

print(
    f"📄 main.py lines: "
    f"{len(main_source.splitlines()):,}"
)

# 12C. FIND ALL LOCAL src MODULES

src_files = sorted(
    SRC_DIR.glob("*.py")
)

if not src_files:
    raise FileNotFoundError(
        "No Python modules were found inside src/."
    )

print()
print("📦 Source modules discovered:")
print("-" * 80)

for path in src_files:
    print(
        f"   • {path.name:<40} "
        f"{path.stat().st_size:,} bytes"
    )

print()
print(
    f"Total src modules: {len(src_files)}"
)

# 12D. CHECK IMPORTS USED BY PROJECT

print()
print("🔎 Checking local imports...")
print("-" * 80)

local_module_names = {
    path.stem
    for path in src_files
}

required_modules = set()

for path in src_files:

    source = path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise SyntaxError(
            f"Syntax error in {path}: {exc}"
        )

    for node in ast.walk(tree):

        # from src.foo import ...
        if isinstance(node, ast.ImportFrom):

            module = node.module or ""

            if module.startswith("src."):

                module_name = module.split(".")[-1]

                if module_name in local_module_names:
                    required_modules.add(
                        module_name
                    )

        # import src.foo
        elif isinstance(node, ast.Import):

            for alias in node.names:

                if alias.name.startswith("src."):

                    module_name = (
                        alias.name.split(".")[-1]
                    )

                    if module_name in local_module_names:
                        required_modules.add(
                            module_name
                        )

# Also inspect main.py.

try:
    main_tree = ast.parse(main_source)
except SyntaxError as exc:
    raise SyntaxError(
        f"Syntax error in main.py: {exc}"
    )

for node in ast.walk(main_tree):

    if isinstance(node, ast.ImportFrom):

        module = node.module or ""

        if module.startswith("src."):

            module_name = module.split(".")[-1]

            if module_name in local_module_names:
                required_modules.add(
                    module_name
                )

    elif isinstance(node, ast.Import):

        for alias in node.names:

            if alias.name.startswith("src."):

                module_name = (
                    alias.name.split(".")[-1]
                )

                if module_name in local_module_names:
                    required_modules.add(
                        module_name
                    )

print(
    f"Local src dependencies detected: "
    f"{len(required_modules)}"
)

for name in sorted(required_modules):
    print(f"   • src.{name}")

# ------------------------------------------------------------
# 12E. INCLUDE ALL src MODULES
#
# IMPORTANT:
# Instead of trying to perfectly calculate dependency order,
# embed ALL src/*.py modules.
#
# This makes the submission robust against hidden imports such
# as:
#
#     src.expected_reward_estimator
#
# ------------------------------------------------------------

modules_to_embed = {}

for path in src_files:

    module_name = path.stem

    source = path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    modules_to_embed[module_name] = source

print()
print(
    f"📦 Embedding {len(modules_to_embed)} "
    f"src modules into submission."
)




# 12F. BUILD SELF-CONTAINED SUBMISSION

parts = []

# 1. Header and Virtual Package Setup
parts.append('''# ============================================================
# Kaggriculture AI Agent
# SELF-CONTAINED KAGGLE SUBMISSION
# ============================================================
import sys
import types
import importlib.util

if "src" not in sys.modules:
    src_package = types.ModuleType("src")
    src_package.__path__ = []
    sys.modules["src"] = src_package

def _load_embedded_module(module_name, source):
    full_name = "src." + module_name
    
    # If already loaded successfully, return it
    if full_name in sys.modules and hasattr(sys.modules[full_name], "_success"):
        return sys.modules[full_name]

    module = types.ModuleType(full_name)
    module.__file__ = f"<embedded-src/{module_name}.py>"
    module.__package__ = "src"
    
    # CRITICAL: Register in sys.modules BEFORE exec so dataclasses/inspect work
    sys.modules[full_name] = module
    
    try:
        code = compile(source, module.__file__, "exec")
        exec(code, module.__dict__)
        module._success = True
        return module
    except Exception as e:
        # If execution fails (e.g. dependency missing), remove it so we can retry
        if full_name in sys.modules:
            del sys.modules[full_name]
        raise e
''')

# 2. Embed the source code of every module
parts.append("\n# ============================================================\n")
parts.append("# EMBEDDED MODULE SOURCE\n")
parts.append("# ============================================================\n")

for module_name, source in modules_to_embed.items():
    parts.append(f"_SRC_{module_name} = {source!r}\n")

# 3. Add the Loader Logic
dict_entries = ",\n    ".join([f'"{name}": _SRC_{name}' for name in modules_to_embed.keys()])

loader_logic = f'''
# ============================================================
# MODULE LOADER
# ============================================================
_embedded_sources = {{
    {dict_entries}
}}

_pending_modules = set(_embedded_sources.keys())
_last_error = None

# Try loading modules until all dependencies are met
# We loop multiple times to allow for nested dependencies
for _attempt in range(len(_embedded_sources) * 3):
    if not _pending_modules:
        break
    _made_progress = False
    for _module_name in list(_pending_modules):
        try:
            _load_embedded_module(_module_name, _embedded_sources[_module_name])
            _pending_modules.remove(_module_name)
            _made_progress = True
        except Exception as e:
            _last_error = e
            continue

if _pending_modules:
    raise _last_error if _last_error else ImportError(f"Could not load modules: {{_pending_modules}}")

# Clean up large source strings to save memory
for _name in list(globals()):
    if _name.startswith("_SRC_"):
        del globals()[_name]
'''
parts.append(loader_logic)

# 4. Embed main.py
parts.append(f"\n_MAIN_SOURCE = {main_source!r}\n")
parts.append('''
exec(compile(_MAIN_SOURCE, "<embedded-main.py>", "exec"), globals())
del _MAIN_SOURCE
''')

# 12J. WRITE SUBMISSION
submission_source = "".join(parts)
SUBMISSION_PATH.write_text(submission_source, encoding="utf-8")

print()
print("=" * 80)
print("✅ DEPENDENCY-SAFE SUBMISSION CREATED (FIXED FOR DATACLASSES)")
print("=" * 80)

# 12B. VALIDATE DEPENDENCY-SAFE SUBMISSION

import ast
import re
from pathlib import Path

print("🔍 VALIDATING DEPENDENCY-SAFE SUBMISSION")
print("=" * 80)

assert SUBMISSION_PATH.exists(), (
    f"submission.py was not created: {SUBMISSION_PATH}"
)

submission_source = SUBMISSION_PATH.read_text(
    encoding="utf-8",
    errors="ignore"
)

print(
    f"📄 Submission: {SUBMISSION_PATH}"
)

print(
    f"📏 Size: {SUBMISSION_PATH.stat().st_size:,} bytes"
)

print(
    f"📏 Lines: {len(submission_source.splitlines()):,}"
)


# 1. PYTHON SYNTAX

try:

    ast.parse(
        submission_source
    )

    syntax_ok = True

except SyntaxError as exc:

    syntax_ok = False

    print("\n❌ Syntax error:")
    print(exc)


print(
    f"\n{'✅' if syntax_ok else '❌'} "
    f"Python syntax: {syntax_ok}"
)

assert syntax_ok


# 2. CHECK EMBEDDED DEPENDENCIES


checks = {

    "submission.py exists":
        SUBMISSION_PATH.exists(),

    "contains embedded src package":
        "_embedded_sources" in submission_source,

    "contains embedded modules":
        "_embedded_sources" in submission_source,

    "contains embedded main.py":
        "_MAIN_SOURCE" in submission_source,

}


# 3. FIND agent() IN MAIN SOURCE

# The dependency-safe submission stores main.py inside
# _MAIN_SOURCE, so agent() may not appear directly in the
# outer submission source.

agent_direct = bool(
    re.search(
        r"\bdef\s+agent\s*\(",
        submission_source
    )
)

agent_embedded = False


# Try to locate the embedded main source.
if "_MAIN_SOURCE" in submission_source:

    # Look for the actual agent definition anywhere
    # inside the generated submission.

    agent_embedded = bool(
        re.search(
            r"def\s+agent\s*\(",
            submission_source
        )
    )


checks["agent() definition present"] = (
    agent_direct or agent_embedded
)


# 4. PRINT RESULTS

print()

for name, result in checks.items():

    print(
        f"{'✅' if result else '❌'} "
        f"{name}: {result}"
    )


# 5. STATIC VALIDATION

failed = [
    name
    for name, result in checks.items()
    if not result
]

if failed:

    print("\n❌ Validation failed.")

    print("\nFailed checks:")

    for item in failed:
        print(
            f"   • {item}"
        )

    print("\n🔎 Submission header preview:")
    print("-" * 80)

    print(
        submission_source[:3000]
    )

    print("-" * 80)

    raise AssertionError(
        "Dependency-safe submission validation failed."
    )


print()
print(
    "🎉 Static submission validation passed!"
)

# 12C. KAGGLE-STYLE IMPORT TEST

print("🧪 TESTING SUBMISSION IMPORT")
print("=" * 80)

submission_spec = (
    importlib.util.spec_from_file_location(
        "submission_test",
        SUBMISSION_PATH
    )
)

submission_module = (
    importlib.util.module_from_spec(
        submission_spec
    )
)

try:

    submission_spec.loader.exec_module(
        submission_module
    )

    print(
        "✅ submission.py imported successfully."
    )

except Exception as exc:

    print(
        "❌ Submission import failed:"
    )

    print(
        type(exc).__name__,
        str(exc)
    )

    raise

assert hasattr(
    submission_module,
    "agent"
)

print(
    "✅ agent() exists."
)

print(
    "🤖 Agent:",
    submission_module.agent
)

# 12D. BASIC AGENT EXECUTION TEST

print("🧪 TESTING agent()")
print("=" * 80)

test_observation = {
    "day": 0,
    "hour": 0,
    "step": 0,
    "player": 0,

    "farms": [
        {
            "farmer": [4, 4],
            "hands": [],
            "hires_today": 0,
            "money": 3000,
            "tiles": [
                [
                    None if c < 5 else "LOCKED"
                    for c in range(10)
                ]
                for _ in range(10)
            ],
        },
        {
            "farmer": [4, 4],
            "hands": [],
            "hires_today": 0,
            "money": 3000,
            "tiles": [
                [
                    None if c < 5 else "LOCKED"
                    for c in range(10)
                ]
                for _ in range(10)
            ],
        },
    ],

    "market": {},

    "private": {},

    "town": {
        "shops": []
    },

    "remainingOverageTime": 60,
}

try:

    action = submission_module.agent(
        test_observation
    )

    print(
        "✅ Agent executed successfully."
    )

    print(
        "🤖 Returned action:"
    )

    print(action)

except Exception as exc:

    print(
        "❌ Agent execution failed:"
    )

    print(
        type(exc).__name__,
        str(exc)
    )

    raise

