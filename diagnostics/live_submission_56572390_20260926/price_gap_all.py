"""Run the exact sale-timing decomposition on all 29 frozen live losses."""

import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
source = HERE / "price_gap_cases.py"
spec = importlib.util.spec_from_file_location("price_gap_cases_all", source)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
audit = json.loads((HERE / "audit_latest_100.json").read_text(encoding="utf-8"))
module.EPISODES = tuple(row["episode_id"] for row in audit["episodes"] if row["outcome"] == "loss")
assert len(module.EPISODES) == 29

if __name__ == "__main__":
    module.main()
