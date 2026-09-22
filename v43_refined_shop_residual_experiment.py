"""Local-only V43 refined selector with a configurable Kaito residual.

Set ``V43_RESIDUAL_SHOP`` to a first unlocked shop name while benchmarking.
No upload/submission behavior is present.
"""

from __future__ import annotations

import copy
import os

import kaggle_public_v58_agent as _kaito
import v43_refined_adaptive_experiment as _adaptive


_RESIDUAL = _kaito._v51_build_policy(
    copy.deepcopy(_adaptive._v43._V43_ROUTES["default"]),
    _kaito._V54_CONFIG,
)
_SHOP = str(os.environ.get("V43_RESIDUAL_SHOP", "")).strip().upper()


def agent(obs, configuration=None):
    base = _adaptive.agent(obs, configuration)
    residual = _RESIDUAL(obs, configuration)
    step = int((obs or {}).get("step", 0) or 0)
    shops = list(((obs or {}).get("town", {}) or {}).get("unlocked_shops", []) or [])
    if _SHOP and step >= 72 and shops and str(shops[0]).upper() == _SHOP:
        return residual
    return base
