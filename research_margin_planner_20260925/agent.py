"""Experimental rival-margin investment policy with the v1 worker executor.

Research dependency file, not a Kaggle submission: it imports the frozen
standalone v1 executor from the adjacent research directory. The production
`main.py` is neither imported nor modified. MODE may be set to `control`,
`terminal_margin`, or `short_cycle` by the local benchmark harness.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


_HERE = Path(__file__).resolve().parent
_EXECUTOR_PATH = _HERE.parent / "research_dynamic_planner_20260925" / "standalone_v1.py"
_SPEC = importlib.util.spec_from_file_location(__name__+"_executor", _EXECUTOR_PATH)
_EXECUTOR = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _EXECUTOR
_SPEC.loader.exec_module(_EXECUTOR)

_MODEL_SPEC = importlib.util.spec_from_file_location(__name__+"_margin_model", _HERE / "margin_model.py")
_MODEL = importlib.util.module_from_spec(_MODEL_SPEC)
sys.modules[_MODEL_SPEC.name] = _MODEL
_MODEL_SPEC.loader.exec_module(_MODEL)

MODE = "terminal_margin"
_ORIGINAL_VALUES = _EXECUTOR.investment_values


def _investment_values(observation, configuration, planned_counts=None):
    if MODE == "control":
        return _ORIGINAL_VALUES(observation, configuration, planned_counts)
    return _MODEL.investment_values(
        observation, configuration, planned_counts, mode=MODE)


_EXECUTOR.investment_values = _investment_values


def agent(observation, configuration=None):
    return _EXECUTOR.agent(observation, configuration)


agent.telemetry = _EXECUTOR.agent.telemetry
