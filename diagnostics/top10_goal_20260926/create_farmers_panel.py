"""Freeze double-Farmers-Market tomato pilot and contrasting control routes."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "diagnostics" / "top100_current_2026-09-25"
OUT = Path(__file__).resolve().parent
TARGETS = ("Arda Ceylan", "Artem The Farmer 🍅", "THUNDER THUNDER")
CONTROLS = ("Boey", "AI是我的豆包", "3정훈")


def main() -> None:
    rows = json.loads((SOURCE / "summary.json").read_text(encoding="utf-8"))
    probe = json.loads((SOURCE / "shop_pair_probe.json").read_text(encoding="utf-8"))
    shops = {(p["action_sha256"], int(p["seed"])): p["shops"] for p in probe}
    selected = [r for r in rows if r["team"] in (*TARGETS, *CONTROLS)]
    assert len(selected) == 6
    for r in selected:
        pair = shops[r["action_sha256"], int(r["seed"])]
        if r["team"] in TARGETS:
            assert pair == ["FARMERS_MARKET", "FARMERS_MARKET"]
        else:
            assert pair != ["FARMERS_MARKET", "FARMERS_MARKET"]
    out = OUT / "farmers_tomato_6routes_summary.json"
    out.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", out)
    for r in selected:
        print(r["team"], r["seed"], shops[r["action_sha256"], int(r["seed"])])


if __name__ == "__main__":
    main()
