"""Local-only market-overlay ablation for the V45 candidate.

Both public agents are advanced on every observation.  V45 remains the
physical controller; the Haideptry proposal can replace only the market list
when all farmer/hand commands are identical.  This prevents an overlay from
silently invalidating a route's worker positions or opening tape.
"""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


_ROOT = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BASE = _load(
    "_v45_market_base",
    _ROOT / "kaggle_extracted_agents_2026-09-21" / "aurax7_v7.py",
)
_ALT = _load(
    "_v45_market_alt",
    _ROOT / "kaggle_extracted_agents_2026-09-21" / "haideptry_master_2965.py",
)

# Benchmark override.  Keep the default conservative while testing.
MARKET_FROM_STEP = 144
MAX_ORDERS = 10


def _physical(action):
    return (
        list(action.get("farmer") or ["PASS"]),
        [list(x) for x in (action.get("hands") or [])],
    )


def agent(observation, configuration=None):
    base = _BASE.agent(observation, configuration)
    alt = _ALT.agent(observation, configuration)
    step = int((observation or {}).get("step", -1) or -1)
    if step < MARKET_FROM_STEP:
        return base
    if _physical(base) != _physical(alt):
        return base
    proposal = alt.get("market")
    if not isinstance(proposal, list):
        return base
    result = copy.deepcopy(base)
    result["market"] = copy.deepcopy(proposal[:MAX_ORDERS])
    return result
