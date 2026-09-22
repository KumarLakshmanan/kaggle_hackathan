"""Offline V43/Kaito late-policy switch experiment; never auto-submitted."""

from __future__ import annotations

import importlib.util
from pathlib import Path


SWITCH_STEP = 360


def _load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_V43 = _load("main_v43_current.py", "v43_switch_base")
_KAITO = _load("kaggle_public_v58_agent.py", "kaito_switch_base")


def agent(obs, configuration=None):
    v43_action = _V43.agent(obs, configuration)
    kaito_action = _KAITO.agent(obs, configuration)
    step = int(obs.get("step", 0) or 0)
    return kaito_action if step >= SWITCH_STEP else v43_action

