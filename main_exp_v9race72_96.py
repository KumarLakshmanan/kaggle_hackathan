"""Validation-only V9 sale-race window ablation.

This wrapper loads a fresh copy of ``main.py`` and changes only the two V9
RACE window constants in the embedded Haide namespace. Production ``main.py``
is not modified.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("v9race72_96_base", ROOT / "main.py")
if spec is None or spec.loader is None:
    raise RuntimeError("could not load main.py")
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)

namespace = getattr(base, "_V51_HAIDE_NAMESPACE", None)
if not isinstance(namespace, dict):
    raise RuntimeError("V51 Haide namespace is unavailable")
if namespace.get("V9_RACE_DEFAULT") != 40 or namespace.get("V9_RACE_MAX") != 48:
    raise RuntimeError("unexpected V9 RACE constants; refusing an invalid ablation")
namespace["V9_RACE_DEFAULT"] = 72
namespace["V9_RACE_MAX"] = 96

agent = base.agent

