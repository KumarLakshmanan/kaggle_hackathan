"""Apply the frozen original-seat gate to the latched stock-sale candidate."""

import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
checker_path = HERE.parent / "late_quote_guard_20260926" / "compare.py"
spec = importlib.util.spec_from_file_location("latched_stock_shared_compare", checker_path)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)
checker.HERE = HERE
checker.TRIAL = HERE / "latched_dev_candidate39.json"
checker.OUTPUT = HERE / "latched_dev_comparison.json"
checker.TRIAL_HASH = "73aa01509f6ab005e527d600b67bae108184302418b00463310d36931e3b28b2"

if __name__ == "__main__":
    checker.main()
