"""Local-only test of per-shop yarn routes instead of the fixed route 9.

The choice uses only the first two shops observed on day 6. It must improve
the 21 known yarn routes by at least two route wins without reversing a win,
then survive fresh-route/reactive validation before promotion to main.py.
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
NAME = "_yarn_shop_base_" + uuid.uuid4().hex
SPEC = importlib.util.spec_from_file_location(NAME, PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load main.py")
BASE = importlib.util.module_from_spec(SPEC)
sys.modules[NAME] = BASE
SPEC.loader.exec_module(BASE)

_PARENT_ROUTER = BASE._IMPL.chassis.router
_PAIR_FILTER = None  # e.g. "ICE_CREAM_SHOP,YARN_STORE" for a narrow screen


def _yarn_router(observation, step, state):
    selected = _PARENT_ROUTER(observation, step, state)
    if 144 <= step < 648:
        shops = tuple((observation.get("town") or {}).get("unlocked_shops", [])[:2])
        if "YARN_STORE" in shops and (
            _PAIR_FILTER is None or ",".join(shops) == _PAIR_FILTER
        ):
            route = BASE._R108_SHOP_ROUTES.get(shops)
            if route in BASE._IMPL.chassis.routes:
                state["route"] = route
                return route
    return selected


BASE._IMPL.chassis.router = _yarn_router


def agent(observation, configuration=None):
    return BASE.agent(observation, configuration)


kaggle_submission_agent = agent
