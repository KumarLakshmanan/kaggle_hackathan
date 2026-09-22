"""Record one candidate agent's legal action tape on a fixed local duel.

Benchmark utility only.  It never talks to Kaggle and never submits anything.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

from paired_benchmark import run_game


def _wrapper_source(candidate: Path, output: Path) -> str:
    candidate_literal = repr(str(candidate.resolve()))
    output_literal = repr(str(output.resolve()))
    return f'''from __future__ import annotations
import copy as _copy
import importlib.util as _importlib_util
import json as _json
from pathlib import Path as _Path

_SPEC = _importlib_util.spec_from_file_location("recorded_candidate", {candidate_literal})
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load candidate")
_MODULE = _importlib_util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
_ACTIONS = []
_OUTPUT = _Path({output_literal})

def agent(observation, configuration=None):
    action = _copy.deepcopy(_MODULE.agent(observation, configuration))
    _ACTIONS.append(_copy.deepcopy(action))
    if len(_ACTIONS) == 719:
        _OUTPUT.write_text(_json.dumps(_ACTIONS, separators=(",", ":")), encoding="utf-8")
    return action
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
    with tempfile.TemporaryDirectory(prefix="kaggriculture-record-") as temporary:
        wrapper = Path(temporary) / "candidate_wrapper.py"
        wrapper.write_text(
            _wrapper_source(args.candidate, args.output), encoding="utf-8"
        )
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
        raise RuntimeError(f"candidate did not produce 719 actions: {args.output}")
    actions = json.loads(args.output.read_text(encoding="utf-8"))
    digest = hashlib.sha256(
        json.dumps(actions, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    payload = {
        "actions": actions,
        "metadata": {
            "seed": args.seed,
            "candidate_seat": args.candidate_seat,
            "action_sha256": digest,
            "result": result,
        },
    }
    with gzip.open(args.output, "wt", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"))
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "actions": len(actions),
                "action_sha256": digest,
                "result": result,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
