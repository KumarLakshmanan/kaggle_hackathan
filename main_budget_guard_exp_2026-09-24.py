"""Local ablation only: enable main.py's forecast-based budget guard.

The guard reserves cash for purchases actually present in the selected route's
next 72 actions and brings forward sales only when projected cash is short.
This wrapper is for the local simulator, not a standalone Kaggle submission.
"""

from __future__ import annotations

from typing import Any

import main as _base


_base._IMPL.chassis.cfg["budget_guard"] = True


def agent(observation: Any, configuration: Any = None) -> Any:
    return _base.agent(observation, configuration)


agent.telemetry = getattr(_base.agent, "telemetry", {})
kaggle_submission_agent = agent
