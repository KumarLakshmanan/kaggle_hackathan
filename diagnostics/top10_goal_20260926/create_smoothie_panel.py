"""Freeze one fresh top-20 target, two same-opening controls, and other shops."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def main() -> None:
    fresh = json.loads((ROOT / "diagnostics/top20_refresh_2026-09-26/summary.json").read_text(encoding="utf-8"))
    older = json.loads((ROOT / "diagnostics/top100_current_2026-09-25/summary.json").read_text(encoding="utf-8"))
    selected = [r for r in fresh if r["team"] in ("吃白饭的大肥鱼", "Boey", "TheEggman", "Otter Vibe")]
    selected.extend(r for r in older if r["team"] in ("Gatswei", "WarRusher"))
    assert len(selected) == 6
    assert len({r["action_sha256"] for r in selected}) == 6
    out = OUT / "smoothie_straw_6routes_summary.json"
    out.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", out)
    print([(r["team"], r["seed"]) for r in selected])


if __name__ == "__main__":
    main()
