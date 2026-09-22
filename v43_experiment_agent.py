"""Configurable, non-production V43 benchmark wrapper.

This file is only for local replay experiments.  It imports the preserved V43
agent and rebuilds its policy with a selected route/configuration.  It never
uploads or submits anything.
"""

from __future__ import annotations

import os

import main_v43_current as _base
import v43.sparse_router as _router


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return int(default)


_forced = os.environ.get("V43_FORCE_ROUTE", "").strip()
_config = _router.SparseShopRouterConfig(
    yarn_first_start=_int_env("V43_YARN_FIRST_START", 88),
    yarn_second_start=_int_env("V43_YARN_SECOND_START", 153),
    bakery_market_maker=os.environ.get("V43_BAKERY_MM", "0") == "1",
    egg_batch=_int_env("V43_EGG_BATCH", 10),
    egg_cash_reserve=float(os.environ.get("V43_EGG_CASH_RESERVE", 2500.0)),
    shed_headroom=_int_env("V43_SHED_HEADROOM", 15),
)

if _forced in {"default", "yarn_first", "yarn_second"}:
    _router.selected_route = lambda _obs, _config: _forced

_base._V43_CONFIG = _config
_base._V43_POLICY = _router.build_sparse_shop_router(_base._V43_ROUTES, _config)

agent = _base.agent

