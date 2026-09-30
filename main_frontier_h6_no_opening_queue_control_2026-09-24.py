"""Diagnostic control: current Frontier H6 candidate with opening rescue disabled."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


_BASE_PATH = Path(__file__).resolve().with_name("main_frontier_h6_candidate_2026-09-24.py")
_SPEC = importlib.util.spec_from_file_location("main_frontier_h6_no_opening_control_base", _BASE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Cannot load base candidate: {_BASE_PATH}")
_BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BASE
_SPEC.loader.exec_module(_BASE)

# This global is consulted only by the opening-queue equality guard. None can
# never equal the candidate's market-order list, so every other strategy branch
# remains exactly the current candidate behavior.
_BASE._H6_OPENING_QUEUE_FROM = None


def agent(observation: Any, configuration: Any = None) -> Any:
    return _BASE.agent(observation, configuration)


agent.telemetry = _BASE.agent.telemetry
kaggle_submission_agent = agent
