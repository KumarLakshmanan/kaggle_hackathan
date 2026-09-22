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


env = make("kaggriculture", debug=True)
cfg = env.configuration
keys = [
    "episodeSteps", "days", "turnsPerDay",
    "townShopUnlockInterval", "townCenterSellInterval",
]
print({k: cfg.get(k) for k in keys})
print("unlock ticks (if interval * turnsPerDay):",
      [int(cfg.get("townShopUnlockInterval", 3)) * int(cfg.get("turnsPerDay", 24)) * i
       for i in range(1, 5)])



NOTES = {
    "CARE": "does not write MILK. Health / yield bonus only.",
    "HARVEST_cow": "writes MILK into the unit inventory, not the shed, not the bank.",
    "EOD_drop": "_drop_inventories_to_shed at end of day. Overflow past shed cap 100 is discarded.",
    "SELL": "only legal cash. Town shops never credit money.",
    "seed_not_in_obs": "episode seed is not given to the agent (host 734743).",
}
print(json.dumps(NOTES, indent=2))

evidence = {
    "engine_min": "1.32.7",
    "cash_path": "HARVEST -> unit inv -> EOD shed -> SELL",
    "not_cash": ["CARE", "town shop visit", "holding straw past cap 100"],
    "shop_unlock_interval_days": 3,
    "submit": False,
}
(WORK / "evidence_cash_path.json").write_text(json.dumps(evidence, indent=2))
print("wrote", WORK / "evidence_cash_path.json")

