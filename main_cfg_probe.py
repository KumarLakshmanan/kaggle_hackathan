"""Read-only benchmark wrapper for testing V46 chassis layer combinations.

This module is deliberately not the Kaggle submission.  ``PROFILE`` is injected
by ``targeted_pair_benchmark.py`` after import, then applied once to the live
V46 chassis before the first action.  Keeping the probe separate prevents an
unverified toggle from changing ``main.py``.
"""

from __future__ import annotations

import main as _base


PROFILE = {}
_APPLIED = False


def agent(observation, configuration=None):
    global _APPLIED
    if not _APPLIED:
        _APPLIED = True
        if isinstance(PROFILE, dict):
            _base._IMPL.chassis.cfg.update(PROFILE)
    return _base.agent(observation, configuration)

