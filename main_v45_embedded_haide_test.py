"""Local test of executing the selected Kaggle source in an isolated namespace."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BASE = _load("_embedded_test_base", _ROOT / "kaggle_extracted_agents_2026-09-21" / "aurax7_v7.py")
_HAIDE_NS = {"__name__": "_embedded_haide_test", "__file__": str(_ROOT / "haideptry_master_2965.py")}
exec((_ROOT / "kaggle_extracted_agents_2026-09-21" / "haideptry_master_2965.py").read_text(encoding="utf-8"), _HAIDE_NS, _HAIDE_NS)
_HAIDE_AGENT = _HAIDE_NS["agent"]


def agent(observation, configuration=None):
    return _HAIDE_AGENT(observation, configuration)

