import json, math, os, subprocess, sys
from pathlib import Path

def ensure_env(min_ver=(1, 32, 7)):
    try:
        from importlib.metadata import version
        inst = version("kaggle-environments")
    except Exception:
        inst = "0"
    parts = []
    for p in inst.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    while len(parts) < 3:
        parts.append(0)
    if tuple(parts[:3]) < min_ver:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U", "kaggle-environments>=1.32.7"])
    import kaggle_environments
    print("kaggle-environments", kaggle_environments.__version__)
    return kaggle_environments

ke = ensure_env()
from kaggle_environments import make
WORK = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path.cwd()
WORK.mkdir(exist_ok=True)
print("work", WORK)


card = {
    "cells": {
        "A_seed21_hold62421": {
            "channel": "HARVEST/SELL milk",
            "tick_window": [624, 672],
            "milk_648": "0 vs 8",
            "remainder_force": "all L",
            "overlay_ATE": 0,
        },
        "B_seed13_hold48465": {
            "channel": "market wool/straw",
            "tick": 649,
            "wool_648": "4 vs 12",
            "plan_at_649": "equal PICKUP WHEAT 6",
            "remainder_force": "all L; 8c breaks kaito 101",
        },
    },
    "fresh_donor": {
        "episode": 94121252,
        "bank": 102964,
        "vs_r53_8c": {"market": 193, "plan": None, "farmer": 347},
        "legal": "market-only from 193",
    },
    "submit": False,
    "disposition": "NO_SUBMIT",
}
(WORK / "evidence_two_fail_cells.json").write_text(json.dumps(card, indent=2))
print(json.dumps(card, indent=2))

