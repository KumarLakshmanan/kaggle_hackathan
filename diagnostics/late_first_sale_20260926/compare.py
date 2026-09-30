"""Apply the frozen original-seat gate using the shared comparison checker."""

import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
checker_path = HERE.parent / "late_quote_guard_20260926" / "compare.py"
spec = importlib.util.spec_from_file_location("late_first_sale_shared_compare", checker_path)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)
checker.HERE = HERE
checker.TRIAL = HERE / "late_first_sale_dev_candidate39.json"
checker.OUTPUT = HERE / "late_first_sale_dev_comparison.json"
checker.TRIAL_HASH = "cf016e23898e17e89660801d1ec57c3e47b3acfff40720e06ed77fd8cc2f934f"

if __name__ == "__main__":
    checker.main()
