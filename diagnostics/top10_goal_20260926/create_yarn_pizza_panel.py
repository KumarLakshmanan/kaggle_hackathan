"""Freeze three new losses and two old wins for Yarn then Pizza shops."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCES = (
    ROOT / "diagnostics/top100_current_2026-09-25/summary.json",
    ROOT / "diagnostics/top100_refresh_2026-09-26/summary.json",
)
TARGETS = {
    ("Lucas Boesen", 113534433),
    ("YumeNeko", 113533879),
    ("mtmr_s1", 113531953),
    ("RS Turley", 113212730),
    ("吃白饭的大肥鱼", 113211945),
}
rows = [r for path in SOURCES for r in json.loads(path.read_text(encoding="utf8"))
        if (r["team"], r["episode_id"]) in TARGETS]
assert len(rows) == len(TARGETS)
assert {(r["team"], r["episode_id"]) for r in rows} == TARGETS
dest = HERE / "yarn_pizza_5routes_summary.json"
dest.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf8")
print(dest)
