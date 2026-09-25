"""Local-only route-cohort counterfactual; not a standalone Kaggle submission.

Uses the frozen main policy but substitutes a compatible precomputed route from
day 6 until the common day-27 terminal route. This does not inspect the replay
opponent or episode and is intended only to screen cohort mix hypotheses.
"""

import importlib.util
import hashlib
from pathlib import Path
import sys
import uuid


_main_path = Path(__file__).with_name("main.py")
_frozen_sha256 = "04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1"
if hashlib.sha256(_main_path.read_bytes()).hexdigest() != _frozen_sha256:
    raise RuntimeError("Route screen requires the frozen main.py baseline")
_module_name = "_exp_route_main_" + uuid.uuid4().hex
_spec = importlib.util.spec_from_file_location(_module_name, _main_path)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Cannot load frozen main policy")
_base = importlib.util.module_from_spec(_spec)
sys.modules[_module_name] = _base
_spec.loader.exec_module(_base)

_EXP_ROUTE = None
_ORIGINAL_ROUTER = _base._IMPL.chassis.router


def _experimental_router(observation, step, state):
    incumbent = _ORIGINAL_ROUTER(observation, step, state)
    if _EXP_ROUTE is None or not 144 <= step < 648:
        return incumbent
    selected = int(_EXP_ROUTE)
    return selected if selected in _base._IMPL.chassis.routes else incumbent


_base._IMPL.chassis.router = _experimental_router


def agent(observation, configuration=None):
    return _base.agent(observation, configuration)


kaggle_submission_agent = agent
