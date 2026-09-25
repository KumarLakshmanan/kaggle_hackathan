"""Local experiment: revisit H6 sale order for observation-detected clones.

The frozen main policy already contains an exact market-order search, but H6
reorders its SELL slots afterwards. This experiment applies that same search
to the final H6 action only under the existing public-state clone gate.
It is not a Kaggle submission or an episode/seed-specific policy.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import uuid


PATH = Path(__file__).with_name("main.py")
EXPECTED_SHA256 = "04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1"
if hashlib.sha256(PATH.read_bytes()).hexdigest() != EXPECTED_SHA256:
    raise RuntimeError("Experiment requires the frozen main.py baseline")

NAME = "_post_h6_clone_base_" + uuid.uuid4().hex
SPEC = importlib.util.spec_from_file_location(NAME, PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load main.py")
BASE = importlib.util.module_from_spec(SPEC)
sys.modules[NAME] = BASE
SPEC.loader.exec_module(BASE)

_STATS = dict(eligible_turns=0, changed_turns=0, errors=0)
_GATE = "strict"


def agent(observation, configuration=None):
    if int(observation.get("step", -1)) == 0:
        _STATS.update(eligible_turns=0, changed_turns=0, errors=0)
    action = BASE.agent(observation, configuration)
    try:
        step = int(observation.get("step", -1))
        if step < 216:
            return action
        if _GATE == "strict":
            eligible = BASE._v44y_clone_gate(observation)
        elif _GATE == "similar":
            eligible = BASE._r37_similarity(observation) >= 0.98
        else:
            eligible = False
        if not eligible:
            return action
        _STATS["eligible_turns"] += 1
        revised = BASE._v44y_reorder(observation, action)
        if revised.get("market") != action.get("market"):
            _STATS["changed_turns"] += 1
        return revised
    except Exception:
        _STATS["errors"] += 1
        return action


agent.telemetry = _STATS
kaggle_submission_agent = agent
