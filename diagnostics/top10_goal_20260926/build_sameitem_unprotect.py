"""Build a pilot allowing same-item front-loading of a protected future sale."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = ROOT / "main.py"
OUT = ROOT / "exp_sale_sameitem_unprotect_20260926.py"
EXPECTED_BASE = "6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076"
OLD = "protected=first[1] if _ADV_PROTECT and first is not None and first[0]=='SELL' else None"
NEW = (
    "protected=first[1] if _ADV_PROTECT and first is not None and first[0]=='SELL' "
    "and not any(len(o)>1 and o[0]=='SELL' and o[1]==first[1] "
    "for o in (action.get('market') or [])) else None"
)
EPISODES = (
    113363691, 113394363, 113386304, 113342041,
    113321656, 113381219, 113361461,
)


def main() -> None:
    original = BASE.read_bytes()
    assert hashlib.sha256(original).hexdigest() == EXPECTED_BASE
    source = original.decode("utf-8")
    assert source.count(OLD) == 1
    amended = source.replace(OLD, NEW, 1).encode("utf-8")
    compile(amended, str(OUT), "exec")
    OUT.write_bytes(amended)
    all_routes = json.loads((ROOT / "diagnostics/live_refresh_56530281_20260926/summary.json")
                            .read_text(encoding="utf-8"))
    selected = [r for r in all_routes if int(r["episode_id"]) in EPISODES]
    assert len(selected) == len(EPISODES)
    summary = HERE / "sameitem_7routes_summary.json"
    summary.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")
    print(OUT, hashlib.sha256(amended).hexdigest())
    print(summary, hashlib.sha256(summary.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
