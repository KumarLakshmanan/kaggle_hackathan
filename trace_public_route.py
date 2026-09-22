"""Trace compact public observations while playing one local route."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import tempfile
from pathlib import Path

from paired_benchmark import run_game


def _source(candidate: Path, output: Path) -> str:
    return f'''import atexit as _atexit
import copy as _copy
import importlib.util as _util
import json as _json
from pathlib import Path as _Path
from paired_benchmark import _capture_public as _capture

_spec = _util.spec_from_file_location("trace_candidate", {str(candidate.resolve())!r})
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load candidate")
_module = _util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
_trace = []
_output = _Path({str(output.resolve())!r})

def _summary(obs):
    farms = []
    for farm in list(obs.get("farms", []) or []):
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
        farms.append({{
            "money": round(float(farm.get("money", 0) or 0), 3),
            "hands": len(farm.get("hands", []) or []),
            "land": len(farm.get("unlocked_quadrants", []) or []),
            "counts": dict(sorted(counts.items())),
        }})
    market = obs.get("market", {{}}) or {{}}
    return {{
        "step": int(obs.get("step", -1) or -1),
        "player": int(obs.get("player", 0) or 0),
        "shops": list((obs.get("town", {{}}) or {{}}).get("unlocked_shops", []) or []),
        "prices": dict(market.get("prices", {{}}) or {{}}),
        "farms": farms,
    }}

def agent(obs, configuration=None):
    try:
        _trace.append(_capture(_copy.deepcopy(obs)))
    except Exception as _error:
        _trace.append({{"capture_error": repr(_error)}})
    action = _module.agent(obs, configuration)
    if len(_trace) >= 719:
        _flush()
    return action

def _flush():
    if _trace:
        _output.write_text(_json.dumps(_trace, separators=(",", ":")), encoding="utf-8")

_atexit.register(_flush)
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--opponent", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--candidate-seat", type=int, choices=(0, 1), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kaggriculture-trace-") as temporary:
        wrapper = Path(temporary) / "trace_wrapper.py"
        wrapper.write_text(_source(args.candidate, args.output), encoding="utf-8")
        # The wrapper flushes after the final callback; run_game completes the
        # engine even though the returned row is only diagnostic here.
        result = run_game(
            candidate=str(wrapper),
            opponent=f"rawroute:{args.opponent.resolve()}",
            seed=args.seed,
            candidate_seat=args.candidate_seat,
            debug=False,
            capture_step=None,
            candidate_overrides={},
        )
    print(json.dumps({"run": result, "exists": args.output.exists(), "size": args.output.stat().st_size if args.output.exists() else 0}, sort_keys=True))
    if not args.output.exists():
        raise RuntimeError("trace wrapper did not write an output")
    print(json.dumps({"output": str(args.output.resolve()), "frames": len(json.loads(args.output.read_text(encoding="utf-8"))), "result": result}, sort_keys=True))


if __name__ == "__main__":
    main()
