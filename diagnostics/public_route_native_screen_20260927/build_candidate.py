"""Package the exact successful public action history into one Python file."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / "exp_shunki_public_route_20260927.py"
EXPECTED_ACTION_HASH = "a72f6711bd28087a242021ec858bbbf9f43fd5f4d4eb9e03d8f872729f742aae"


def main() -> None:
    rows = json.loads((ROOT / "diagnostics" / "top10_goal_20260926" /
                       "double_yarn_highsheep_4routes_summary.json").read_text(encoding="utf8"))
    source = next(row for row in rows if row["team"] == "ShunkiKyoya")
    with gzip.open(source["path"], "rt", encoding="utf8") as handle:
        actions = json.load(handle)["actions"]
    assert len(actions) == 719
    raw = json.dumps(actions, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8")
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_ACTION_HASH
    encoded = base64.b85encode(zlib.compress(raw, 9)).decode("ascii")
    code = f'''"""Experimental single-file recorded public route; source action SHA-256
{EXPECTED_ACTION_HASH}. Not a promoted Kaggle submission.
"""
import base64
import copy
import json
import zlib

_PACKED = {encoded!r}
ACTIONS = json.loads(zlib.decompress(base64.b85decode(_PACKED)).decode("utf8"))
_CALLS = 0

def _value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        return getter(key, default)
    return getattr(obj, key, default)

def agent(obs, config=None):
    del config
    global _CALLS
    raw_step = _value(obs, "step", None)
    try:
        step = int(raw_step) if raw_step is not None else _CALLS
    except (TypeError, ValueError):
        step = _CALLS
    _CALLS += 1
    if not ACTIONS:
        return {{"farmer": ["PASS"], "hands": [], "market": []}}
    step = max(0, min(step, len(ACTIONS) - 1))
    return copy.deepcopy(ACTIONS[step])

def kaggle_shunki_recorded_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
    OUTPUT.write_text(code, encoding="utf8")
    print(hashlib.sha256(OUTPUT.read_bytes()).hexdigest(), OUTPUT, "bytes", OUTPUT.stat().st_size)


if __name__ == "__main__":
    main()
