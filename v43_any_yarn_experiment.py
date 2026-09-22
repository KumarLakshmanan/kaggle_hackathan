"""Local-only V43 suffix selector ablation using any public YARN position."""

from __future__ import annotations

import copy

import main_v43_current as _base
import v43.sparse_router as _router
from v23.state_encoder import get as _get


_original = _router.selected_route


def _selected_route(obs, config):
    step = int(_get(obs, "step", 0) or 0)
    town = _get(obs, "town", {}) or {}
    shops = [str(x) for x in (_get(town, "unlocked_shops", []) or [])]
    # Preserve the validated first/second-shop decisions exactly.
    base = _original(obs, config)
    if base != "default":
        return base
    if "YARN_STORE" not in shops:
        return "default"

    first = shops.index("YARN_STORE")
    # Later YARN unlocks are not covered by the original router.  These
    # thresholds are deliberately conservative and only select after the
    # public shop appears.
    if first >= 2:
        first_step = (first + 1) * 72
        if step < first_step:
            return "default"
        if first_step >= 400:
            return "yarn_first"
        if first_step <= 150 and shops and shops[0] == "ICE_CREAM_SHOP":
            return "yarn_first"
        return "yarn_second"
    return "default"


_router.selected_route = _selected_route
_base._V43_POLICY = _router.build_sparse_shop_router(
    copy.deepcopy(_base._V43_ROUTES), _base._V43_CONFIG
)
agent = _base.agent

