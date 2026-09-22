"""Offline experiment: V43 farm route plus a reserve-safe WHEAT expert.

This file is a local benchmark candidate only.  It is deliberately separate
from ``main.py`` and is never submitted automatically.
"""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


def _load_base():
    path = Path(__file__).with_name("main_v43_current.py")
    spec = importlib.util.spec_from_file_location("v43_base_for_mm", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
from v24.market_maker import MarketMakerConfig, wrap_market_maker


_MM_CONFIG = MarketMakerConfig(
    enabled=True,
    item="WHEAT",
    feed_item="WHEAT",
    start_step=72,
    stop_entry_step=716,
    max_batch=10,
    minimum_expected_profit=1.0,
    mirror_minimum_expected_profit=1.0,
    minimum_cash_reserve=2500.0,
    feed_days_reserve=2.0,
    investment_horizon=2,
    shed_headroom=15,
    max_hold_steps=4,
    max_orders=10,
)
_POLICY = wrap_market_maker(
    _BASE._V43_POLICY,
    _BASE._V43_ROUTES["default"],
    _MM_CONFIG,
)


def agent(obs, configuration=None):
    return _POLICY(obs, configuration)

