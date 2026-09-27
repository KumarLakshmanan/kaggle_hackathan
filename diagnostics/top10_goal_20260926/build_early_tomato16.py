"""Build isolated day-16 complete V219 tomato investment pilot."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_early_tomato16_20260926.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"


def once(source: str, old: str, new: str) -> str:
    assert source.count(old) == 1, (old, source.count(old))
    return source.replace(old, new)


def main() -> None:
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    source = SOURCE.read_text(encoding="utf8")
    changes = (
        ("if sum(s in ('PIZZA_SHOP','FARMERS_MARKET') for s in obs['town']['unlocked_shops']) < 3:",
         "if sum(s in ('PIZZA_SHOP','FARMERS_MARKET') for s in obs['town']['unlocked_shops']) < 2:"),
        ("for a in tape[432:719]:", "for a in tape[384:719]:"),
        ("if not state.get('committed') and day!=18:return action",
         "if not state.get('committed') and day!=16:return action"),
        ("elif day==18 and not tomato:", "elif day==16 and not tomato:"),
        ("if step==432:state['eligible']=_v219_qualifies(observation,native)",
         "if step==384:state['eligible']=_v219_qualifies(observation,native)"),
        ("if not state.get('eligible') or day<18:return action",
         "if not state.get('eligible') or day<16:return action"),
        ("    _CLONE_REPORT.update(getattr(_CLONE_PARENT, \"telemetry\", {}))\n    return action",
         "    _CLONE_REPORT.update(getattr(_CLONE_PARENT, \"telemetry\", {}))\n"
         "    _CLONE_REPORT.update({\"v219_\"+k: v for k, v in _V219_REPORT.items()\n"
         "                          if isinstance(v, (int, float, bool, str))})\n"
         "    return action"),
    )
    for old, new in changes:
        source = once(source, old, new)
    ast.parse(source)
    OUTPUT.write_text(source, encoding="utf8")
    print(json.dumps({"source_sha256": EXPECTED,
                      "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
                      "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
