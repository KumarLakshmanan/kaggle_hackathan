"""Local benchmark wrapper for old-opening/V43-tail splice ablations."""

from __future__ import annotations

import copy
import os

import main_before_v32_submission_backup as _old
import main_v43_current as _base
import v43.sparse_router as _router


try:
    _cut = max(0, min(719, int(os.environ.get("SPLICE_CUT", "0"))))
except (TypeError, ValueError):
    _cut = 0

_old._load_tapes()
_prefix = copy.deepcopy(_old._TAPES["hozuma"])
for _name, _route in list(_base._V43_ROUTES.items()):
    _base._V43_ROUTES[_name] = copy.deepcopy(
        _prefix[:_cut] + _route[_cut:]
    )

_base._V43_POLICY = _router.build_sparse_shop_router(
    _base._V43_ROUTES, _base._V43_CONFIG
)
agent = _base.agent

