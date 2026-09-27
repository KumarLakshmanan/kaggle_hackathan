"""Re-run the established read-only live-audit code in a fresh output folder."""

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "live_submission_56530281_20260925" / "audit_live.py"
spec = importlib.util.spec_from_file_location("kaggriculture_audit_live_refresh", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
module.HERE = HERE
module.SUBMISSION = 56530281


if __name__ == "__main__":
    sys.argv = [str(SOURCE), "--limit", "40", "--workers", "6"]
    module.main()
