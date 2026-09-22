"""Local benchmark wrapper for a V43-opening/pre-V32-tail splice."""

from __future__ import annotations

import copy
import os

import main_before_v32_submission_backup as _old
import main_v43_current as _base
import v43.sparse_router as _router


try:
    _cut = max(0, min(719, int(os.environ.get("SPLICE_CUT", "719"))))
except (TypeError, ValueError):
    _cut = 719

_old._load_tapes()
_tail = copy.deepcopy(_old._TAPES["hozuma"])
for _name, _route in list(_base._V43_ROUTES.items()):
    _base._V43_ROUTES[_name] = copy.deepcopy(
        _route[:_cut] + _tail[_cut:]
    )

_base._V43_POLICY = _router.build_sparse_shop_router(
    _base._V43_ROUTES, _base._V43_CONFIG
)
agent = _base.agent

