"""Build an isolated physical-mirror strawberry-only 24-turn sale pilot."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_mirror_straw24_20260926.py"
EXPECTED = "08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863"


def once(source: str, old: str, new: str) -> str:
    assert source.count(old) == 1, (old, source.count(old))
    return source.replace(old, new)


def main() -> None:
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    source = SOURCE.read_text(encoding="utf8")
    source = once(source, "_ADV_LOOK=4\n_ADV_FROM=144", "_ADV_LOOK=4\n_ADV_STRAW_EXTRA=0\n_ADV_FROM=144")
    source = once(source, "for off in range(1,_ADV_LOOK+1):\n        t=step+off",
                  "for off in range(1,max(_ADV_LOOK,_ADV_STRAW_EXTRA)+1):\n        t=step+off")
    source = once(source, "if first is None:first=o", "if first is None and off<=_ADV_LOOK:first=o")
    source = once(source, "if o[0]=='SELL' and o[1] in _ADV_ITEMS:\n                try:q=",
                  "if o[0]=='SELL' and o[1] in _ADV_ITEMS:\n                if off>_ADV_LOOK and o[1]!='STRAWBERRY':continue\n                try:q=")
    source = once(source, "def agent(observation, configuration=None):\n    global _ADV_LOOK\n    step = int(observation[\"step\"])",
                  "def agent(observation, configuration=None):\n    global _ADV_LOOK, _ADV_STRAW_EXTRA\n    step = int(observation[\"step\"])")
    source = once(source, "    _ADV_LOOK = 12 if matched else 4\n    before = _ADV_REPORT.get(\"adv_turns\", 0)",
                  "    _ADV_LOOK = 12 if matched else 4\n    _ADV_STRAW_EXTRA = 24 if matched else 0\n    before = _ADV_REPORT.get(\"adv_turns\", 0)")
    ast.parse(source)
    OUTPUT.write_text(source, encoding="utf8")
    print(json.dumps({
        "source_sha256": EXPECTED,
        "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "output": str(OUTPUT),
    }, indent=2))


if __name__ == "__main__":
    main()
