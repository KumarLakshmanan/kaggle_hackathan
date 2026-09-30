"""Build a narrow pure-sale protection candidate from the uploaded main.py."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_mirror_pure_sale_20260926.py"
EXPECTED = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"


def once(source: str, old: str, new: str) -> str:
    assert source.count(old) == 1, (old, source.count(old))
    return source.replace(old, new)


def main() -> None:
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
    source = SOURCE.read_text(encoding="utf8")
    source = once(source, "    plan=[];first=None\n    for off in range(1,max(_ADV_LOOK,_ADV_STRAW_EXTRA)+1):",
                  "    plan=[];first=None;first_step=None\n    for off in range(1,max(_ADV_LOOK,_ADV_STRAW_EXTRA)+1):")
    source = once(source, "            if first is None and off<=_ADV_LOOK:first=o",
                  "            if first is None and off<=_ADV_LOOK:first=o;first_step=t")
    source = once(source,
                  "    protected=first[1] if _ADV_PROTECT and first is not None and first[0]=='SELL' else None",
                  "    first_sale=first is not None and first[0]=='SELL'\n"
                  "    pure_sale_turn=(first_sale and first_step is not None and\n"
                  "                    all(x and x[0]=='SELL' for x in _adv_future(player,first_step)))\n"
                  "    protected=(first[1] if _ADV_PROTECT and first_sale and\n"
                  "               not (_ADV_LOOK==12 and pure_sale_turn) else None)")
    ast.parse(source)
    OUTPUT.write_text(source, encoding="utf8")
    print(json.dumps({"source_sha256": EXPECTED,
                      "candidate_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
                      "output": str(OUTPUT)}, indent=2))


if __name__ == "__main__":
    main()
