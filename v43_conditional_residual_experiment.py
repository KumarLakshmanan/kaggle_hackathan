"""Local-only conditional residual overlay ablation."""

from __future__ import annotations

import copy

import kaggle_public_v58_agent as _kaito
import main_v43_current as _v43


_RESIDUAL = _kaito._v51_build_policy(
    copy.deepcopy(_v43._V43_ROUTES["default"]), _kaito._V54_CONFIG
)


def agent(obs, configuration=None):
    base = _v43.agent(obs, configuration)
    residual = _RESIDUAL(obs, configuration)
    step = int((obs or {}).get("step", 0) or 0)
    town = (obs or {}).get("town", {}) or {}
    shops = list(town.get("unlocked_shops", []) or [])
    if step >= 72 and shops and str(shops[0]) == "PIZZA_SHOP":
        return residual
    return base

