"""Diagnostic fixed-project control isolating the new worker scheduler.

Not a submission. It replaces only economic preferences, so work execution
can be tested independently while the forecast module is being verified.
"""

from pathlib import Path
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

CONTROL_PROJECT = "WHEAT"


class ControlEconomics:
    @staticmethod
    def price(item, inventory, overrides=None):
        return engine.market_price(item, inventory, engine._resolve_market_params(overrides))

    @staticmethod
    def investment_values(obs, cfg, planned_counts=None):
        item = CONTROL_PROJECT
        day = int(obs.get("day", 0))
        last = (int(cfg.get("episodeSteps", 720))-2)//int(cfg.get("turnsPerDay", 24))
        cutoff = last-4 if item == "WHEAT" else last-10
        return {item: {"score": 100 if day <= cutoff else -1,
                       "net": 1000, "capital": 10 if item == "WHEAT" else 500,
                       "horizon": 5, "daily_actions": 2, "output": {}}}


_path = Path(__file__).with_name("candidate.py")
_source = _path.read_text(encoding="utf-8")
_begin = _source.index("_ECON_SPEC =")
_end = _source.index("_ECON_SPEC.loader.exec_module(_ECON)", _begin)
_end += len("_ECON_SPEC.loader.exec_module(_ECON)")
_source = _source[:_begin]+"_ECON = ControlEconomics\n"+_source[_end:]
_policy = {"__name__": __name__+"_policy", "__file__": str(_path),
           "ControlEconomics": ControlEconomics}
exec(compile(_source, str(_path), "exec"), _policy)
agent = _policy["agent"]
