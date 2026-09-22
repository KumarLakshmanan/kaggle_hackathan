"""Benchmark-only: V43 opening, C14 continuation after shop reveal."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import v43_refined_conditional_experiment as _pre


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_ROOT = Path(__file__).resolve().parent
_post = _load(
    _ROOT / "kaggle_public_code" / "beicicc__kaggriculture-c14-late-crop-weed-recovery" / "kaggriculture-c14-late-crop-weed-recovery.py",
    "hybrid_v43_c14_post",
)


def agent(observation, configuration=None):
    step = int((observation or {}).get("step", -1) or -1)
    pre_action = _pre.agent(observation, configuration)
    post_action = _post.agent(observation, configuration)
    return post_action if step >= 72 else pre_action

