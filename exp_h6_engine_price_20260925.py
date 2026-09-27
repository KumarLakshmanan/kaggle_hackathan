"""Local-only H6 price-model correction; not a Kaggle submission.

The simulator's carrot, tomato, and egg scarcity curves are ``hinge`` curves.
The frozen main.py H6 scorer still approximates them as log/linear curves.
This candidate changes only H6's *ranking estimate*, never farm actions or
the market's actual execution. Promote only after paired and reactive checks.
"""

from __future__ import annotations

import hashlib
import importlib.util
import math
from pathlib import Path
import sys
import uuid


PATH = Path(__file__).with_name("main.py")
EXPECTED_SHA256 = "04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1"
if hashlib.sha256(PATH.read_bytes()).hexdigest() != EXPECTED_SHA256:
    raise RuntimeError("Experiment requires the frozen main.py baseline")
NAME = "_h6_engine_price_base_" + uuid.uuid4().hex
SPEC = importlib.util.spec_from_file_location(NAME, PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load main.py")
BASE = importlib.util.module_from_spec(SPEC)
sys.modules[NAME] = BASE
SPEC.loader.exec_module(BASE)


BASE._H6_MARKET_PARAMS.update({
    "CARROT": (35, 10000, 450, "hinge", 1.0, "sqrt", 0.7),
    "TOMATO": (60, 10000, 200, "hinge", 0.4, "sqrt", 0.6),
    "EGG": (50, 10000, 332, "hinge", 0.4, "log", 0.2),
})


def _shape(name: str, x: float, scale: float) -> float:
    x = max(0.0, x)
    if name == "linear":
        return x
    if name == "sq":
        return x * x
    if name == "sqrt":
        return math.sqrt(x)
    if name == "log":
        return math.log1p(x)
    if name == "log10":
        return math.log10(1.0 + x)
    if name == "hinge":
        u = x / scale
        return u + 8.0 * max(0.0, u - 1.0) ** 2
    raise ValueError(name)


def _market_price(item: str, inventory: int) -> int:
    base, equilibrium, scale, below_name, below_target, above_name, above_target = BASE._H6_MARKET_PARAMS[item]
    if inventory < equilibrium:
        amp = below_target * base / _shape(below_name, scale, scale)
        quote = base + amp * _shape(below_name, equilibrium - inventory, scale)
    else:
        amp = above_target * base / _shape(above_name, scale, scale)
        quote = base - amp * _shape(above_name, inventory - equilibrium, scale)
    return max(1, int(round(quote)))


BASE._h6_market_price = _market_price


def agent(observation, configuration=None):
    return BASE.agent(observation, configuration)


kaggle_submission_agent = agent
