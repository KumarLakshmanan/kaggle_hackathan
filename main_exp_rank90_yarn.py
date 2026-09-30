"""Validation wrapper for the transparent rank-90 early-yarn ablation.

The production ``main.py`` remains unchanged. ``route_panel_benchmark.py`` can
set ``_EARLY_YARN_ENABLED`` to compare the day-11 commitment on and off while
holding this later V52-family policy constant. The separate end-of-game branch
is disabled in both modes so this experiment isolates the day-11 trigger.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
_EARLY_YARN_ENABLED = True
_SPEC = importlib.util.spec_from_file_location("rank90_yarn_base", ROOT / "main.py")
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
if not callable(_NAMESPACE.get("_e350_agent")):
    raise RuntimeError("early-yarn policy entry point is unavailable")


def agent(observation, configuration=None):
    _NAMESPACE["_E343_YX_DAY11"] = bool(_EARLY_YARN_ENABLED)
    _NAMESPACE["_E343_YX_END"] = False
    return _NAMESPACE["_e350_agent"](observation, configuration)


agent.telemetry = _NAMESPACE["_e350_agent"].telemetry
