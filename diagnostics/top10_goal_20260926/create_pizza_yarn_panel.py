"""Freeze fresh Boey and both current-top-100 PIZZA,YARN route controls."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def main() -> None:
    fresh = json.loads((ROOT / "diagnostics/top20_refresh_2026-09-26/summary.json").read_text(encoding="utf-8"))
    current = json.loads((ROOT / "diagnostics/top100_current_2026-09-25/summary.json").read_text(encoding="utf-8"))
    selected = [r for r in fresh if r["team"] == "Boey"]
    names = ("Fourth Quadrant", "Ghost Rule", "Dmytro Maliarenko", "吃白饭的大肥鱼")
    selected.extend(r for r in current if r["team"] in names)
    assert len(selected) == 5
    assert len({r["action_sha256"] for r in selected}) == 5
    out = OUT / "pizza_yarn_5routes_summary.json"
    out.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", out)
    print([(r["team"], r["seed"]) for r in selected])


if __name__ == "__main__":
    main()
