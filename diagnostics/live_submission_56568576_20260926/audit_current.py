"""Read-only audit of public games for the newly uploaded 12-turn policy."""

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "live_submission_56530281_20260925" / "audit_live.py"
spec = importlib.util.spec_from_file_location("kaggriculture_audit_current12", SOURCE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
module.HERE = HERE
module.SUBMISSION = 56568576

if __name__ == "__main__":
    sys.argv = [str(SOURCE), "--limit", "40", "--workers", "4"]
    module.main()
