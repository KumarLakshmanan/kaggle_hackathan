"""Local-only H6 sale-order experiment around the production main.py agent.

This file is used only by the replay benchmark harness. It leaves main.py
untouched and never submits anything to Kaggle.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


_ROOT = Path(__file__).resolve().parent


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Give the production module a per-benchmark-game name so persistent module
# state cannot leak from one route to the next in a worker process.
_MAIN = _load_module(_ROOT / "main.py", f"production_main_for_{__name__}")

# Reuse the already-tested plaintext H6 market/demand scorer, without calling
# its frontier-agent wrapper.
_H6_PATH = _ROOT / "ablation_frontier_adapter_2026-09-23.py"
_H6_HELPER_NAME = "h6_demand_rank_helper_for_main_benchmark"
_H6 = sys.modules.get(_H6_HELPER_NAME)
if _H6 is None:
    _H6 = _load_module(_H6_PATH, _H6_HELPER_NAME)


def agent(observation: Any, configuration: Any = None) -> Any:
    step = int(observation.get("step", -1))
    if step == 0:
        for key in _H6._DIAGNOSTICS:
            _H6._DIAGNOSTICS[key] = 0
    action = _MAIN.agent(observation, configuration)
    action = _H6._h6_rank_sell_slots(observation, action, configuration)
    if step >= 719:
        sys.modules.pop(_MAIN.__name__, None)
    return action


agent.telemetry = _H6._DIAGNOSTICS
kaggle_submission_agent = agent
