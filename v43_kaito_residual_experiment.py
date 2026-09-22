"""Local-only experiment: apply Kaito's public residual controller to V43."""

from __future__ import annotations

import copy

import kaggle_public_v58_agent as _kaito
import main_v43_current as _v43


_POLICY = _kaito._v51_build_policy(
    copy.deepcopy(_v43._V43_ROUTES["default"]), _kaito._V54_CONFIG
)


def agent(obs, configuration=None):
    return _POLICY(obs, configuration)

