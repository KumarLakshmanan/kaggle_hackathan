"""Local-only test: run a recorded top-player route through V43 repair logic."""

from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path

import main_v43_current as _base
import v43.sparse_router as _router


_route_path = Path(__file__).with_name(
    "current_top10_routes_2026-09-21"
) / "episode-109848566-team0.json.gz"
with gzip.open(_route_path, "rt", encoding="utf-8") as _handle:
    _actions = json.load(_handle)["actions"]

_routes = {name: copy.deepcopy(_actions) for name in _base._V43_ROUTES}
_base._V43_POLICY = _router.build_sparse_shop_router(
    _routes, _base._V43_CONFIG
)
agent = _base.agent

