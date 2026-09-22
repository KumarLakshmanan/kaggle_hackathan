"""Local-only V43 adaptive-branch plus selective residual experiment."""

from __future__ import annotations

import copy

import kaggle_public_v58_agent as _kaito
import v43_adaptive_branch_experiment as _adaptive


_RESIDUAL = _kaito._v51_build_policy(
    copy.deepcopy(_adaptive._v43._V43_ROUTES["default"]),
    _kaito._V54_CONFIG,
)


def agent(obs, configuration=None):
    base = _adaptive.agent(obs, configuration)
    residual = _RESIDUAL(obs, configuration)
    step = int((obs or {}).get("step", 0) or 0)
    town = (obs or {}).get("town", {}) or {}
    shops = list(town.get("unlocked_shops", []) or [])
    if step >= 72 and shops and str(shops[0]) == "PIZZA_SHOP":
        return residual
    return base

