"""Local, observation-legal route-mapping probe; not a Kaggle submission.

The first two public shop unlocks choose a day-6 route in the unchanged
main.py chassis.  This experiment substitutes one existing route for the
ICE_CREAM_SHOP/BAKERY opening to test whether the current route is a poor
portfolio fit.  It does not inspect seeds, opponent names, or future shops.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


_BASE_PATH = Path(__file__).resolve().with_name("main.py")
_BASE_SHA256 = "04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1"
if hashlib.sha256(_BASE_PATH.read_bytes()).hexdigest() != _BASE_SHA256:
    raise RuntimeError("Route probe requires the frozen current main.py")
_SPEC = importlib.util.spec_from_file_location("_route_probe_main_20260924", _BASE_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("Cannot load baseline")
_BASE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _BASE
_SPEC.loader.exec_module(_BASE)

_TEST_ROUTE_ID = 105
_PAIR = ("ICE_CREAM_SHOP", "BAKERY")
_ORIGINAL_ROUTE = _BASE._R108_SHOP_ROUTES[_PAIR]


def agent(observation, configuration=None):
    if not isinstance(observation, dict):
        return _BASE.agent(observation, configuration)
    if int(observation.get("step", -1)) == 0:
        if _TEST_ROUTE_ID not in _BASE._IMPL.chassis.routes:
            raise ValueError(f"Unknown route: {_TEST_ROUTE_ID}")
        _BASE._R108_SHOP_ROUTES[_PAIR] = _TEST_ROUTE_ID
    return _BASE.agent(observation, configuration)


agent.original_route = _ORIGINAL_ROUTE
