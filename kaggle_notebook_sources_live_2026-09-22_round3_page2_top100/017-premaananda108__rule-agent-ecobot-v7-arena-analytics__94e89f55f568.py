!pip install -q -U kaggle-environments

import shutil
from pathlib import Path

# Automatically find the dataset directory by locating arena.py
dataset_dir = next(Path("/kaggle/input").rglob("arena.py")).parent
print(f"Found dataset at: {dataset_dir}")

# Copy bots folder and evaluation scripts into /kaggle/working
shutil.copytree(dataset_dir / "bots", "bots", dirs_exist_ok=True)
for py_file in dataset_dir.glob("*.py"):
    shutil.copy2(py_file, py_file.name)

print("Files successfully copied:")
!ls -la


!python bots/eco7Lite/bundle.py
!mv bots/eco7Lite/submission.py ./submission.py

import ast

with open("submission.py") as f:
    tree = ast.parse(f.read())

has_agent = any(isinstance(n, ast.FunctionDef) and n.name == "agent" for n in tree.body)
assert has_agent, "submission.py must define a top-level `agent` function"
print("OK: submission.py defines `agent()` and parses cleanly without syntax errors.")


from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 48}, debug=True)
env.run(["submission.py", "random"])

final = env.steps[-1]
for i, s in enumerate(final):
    print(f"Player {i}: reward={s.reward}, status={s.status}")


!python arena.py --bots submission.py starter --games 2 --workers 4 --seed 42 --save-replays both

!python bot_pnl.py "replays/*.json" --bot submission

!find /kaggle/working -type d -name "__pycache__" -exec rm -rf {} +
!find /kaggle/working -type f -name "*.pyc" -delete