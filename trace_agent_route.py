"""Benchmark-only trace recorder for one local simulator duel."""

from __future__ import annotations

import argparse
import copy
import gzip
import importlib.util
import json
import tempfile
from pathlib import Path

from paired_benchmark import run_game


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path.resolve())
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _farm(farm):
    counts = {}
    for row in farm.get("tiles", []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value:
                    counts[value] = counts.get(value, 0) + 1
                    break
    return {
        "money": round(float(farm.get("money", 0) or 0), 2),
        "hands": len(farm.get("hands", []) or []),
        "land": len(farm.get("unlocked_quadrants", []) or []),
        "counts": counts,
    }


def _compact(obs, action):
    town = obs.get("town", {}) or {}
    market = obs.get("market", {}) or {}
    return {
        "step": int(obs.get("step", -1) or -1),
        "player": int(obs.get("player", 0) or 0),
        "shops": list(town.get("unlocked_shops", []) or []),
        "prices": dict(market.get("prices", {}) or {}),
        "inventory": dict(market.get("inventory", {}) or {}),
        "farms": [_farm(farm) for farm in list(obs.get("farms", []) or [])],
        "action": copy.deepcopy(action),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--opponent", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--candidate-seat", type=int, choices=(0, 1), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    candidate_literal = repr(str(args.candidate.resolve()))
    output_literal = repr(str(args.output.resolve()))
    source = f'''from __future__ import annotations
import copy as _copy
import gzip as _gzip
import importlib.util as _importlib_util
import json as _json
from pathlib import Path as _Path

_SPEC = _importlib_util.spec_from_file_location("traced_candidate", {candidate_literal})
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load candidate")
_MODULE = _importlib_util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
_ROWS = []
_OUTPUT = _Path({output_literal})

def _farm(farm):
    counts = {{}}
    for row in farm.get("tiles", []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value:
                    counts[value] = counts.get(value, 0) + 1
                    break
    return {{"money": round(float(farm.get("money", 0) or 0), 2),
            "hands": len(farm.get("hands", []) or []),
            "land": len(farm.get("unlocked_quadrants", []) or []),
            "counts": counts}}

def _compact(obs, action):
    town = obs.get("town", {{}}) or {{}}
    market = obs.get("market", {{}}) or {{}}
    return {{"step": int(obs.get("step", -1) or -1),
            "player": int(obs.get("player", 0) or 0),
            "shops": list(town.get("unlocked_shops", []) or []),
            "prices": dict(market.get("prices", {{}}) or {{}}),
            "inventory": dict(market.get("inventory", {{}}) or {{}}),
            "farms": [_farm(farm) for farm in list(obs.get("farms", []) or [])],
            "action": _copy.deepcopy(action)}}

def agent(observation, configuration=None):
    action = _MODULE.agent(observation, configuration)
    _ROWS.append(_compact(observation, action))
    if len(_ROWS) == 719:
        _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with _gzip.open(_OUTPUT, "wt", encoding="utf-8") as _handle:
            _json.dump({{"rows": _ROWS}}, _handle, separators=(",", ":"))
    return action
'''
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kaggriculture-trace-") as directory:
        wrapper = Path(directory) / "candidate_wrapper.py"
        wrapper.write_text(source, encoding="utf-8")
        result = run_game(
            candidate=str(wrapper),
            opponent=f"rawroute:{args.opponent.resolve()}",
            seed=args.seed,
            candidate_seat=args.candidate_seat,
            debug=False,
            capture_step=None,
            candidate_overrides={},
        )
    if not args.output.is_file():
        raise RuntimeError(f"candidate did not produce 719 traced calls: {args.output}")
    print(json.dumps({"output": str(args.output.resolve()), "result": result}, sort_keys=True))


if __name__ == "__main__":
    main()
