"""Validation-only wrapper for the embedded Rank-41 base policy.

Unlike ``main_exp_rank90_yarn.py``, this calls the embedded source's raw
``agent`` entry point and does not run its later E343/EXP350 wrapper stack.
Production ``main.py`` is left unchanged.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("rank41_raw_base", ROOT / "main.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("could not load main.py")
_BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BASE
try:
    _SPEC.loader.exec_module(_BASE)
except Exception:
    sys.modules.pop(_SPEC.name, None)
    raise
sys.modules.pop(_SPEC.name, None)

_NAMESPACE = getattr(_BASE, "_V52_RANK41_NAMESPACE", None)
if not isinstance(_NAMESPACE, dict):
    raise RuntimeError("V52 experiment namespace is unavailable")
_RAW_AGENT = _NAMESPACE.get("agent")
if not callable(_RAW_AGENT):
    raise RuntimeError("raw embedded Rank-41 entry point is unavailable")


def agent(observation, configuration=None):
    return _RAW_AGENT(observation, configuration)


agent.telemetry = getattr(_RAW_AGENT, "telemetry", {})
