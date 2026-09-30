"""Apply the frozen original-seat gate to the half-base stock-sale variant."""

import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
checker_path = HERE.parent / "late_quote_guard_20260926" / "compare.py"
spec = importlib.util.spec_from_file_location("halfbase_stock_shared_compare", checker_path)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)
checker.HERE = HERE
checker.TRIAL = HERE / "halfbase_dev_candidate39.json"
checker.OUTPUT = HERE / "halfbase_dev_comparison.json"
checker.TRIAL_HASH = "e9517daebe5523879c5096839570af04619135fc7f5a7fb7e6446ab1c367ca68"

if __name__ == "__main__":
    checker.main()
