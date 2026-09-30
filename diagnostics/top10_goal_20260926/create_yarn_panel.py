"""Freeze the September 25 yarn route screen and unrelated controls."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "diagnostics" / "top100_current_2026-09-25"
OUT = Path(__file__).resolve().parent


def main() -> None:
    entries = json.loads((SOURCE / "summary.json").read_text(encoding="utf-8"))
    captures = json.loads((SOURCE / "shop_pair_probe.json").read_text(encoding="utf-8"))
    by_episode: dict[int, dict[int, list[str]]] = {}
    for capture in captures:
        by_episode.setdefault(int(capture["episode_id"]), {})[int(capture["seat"])] = list(capture["shops"])

    yarn: list[dict] = []
    others: list[dict] = []
    for entry in entries:
        shops = by_episode[int(entry["episode_id"])]
        assert set(shops) == {0, 1}, entry["episode_id"]
        (yarn if any("YARN_STORE" in pair for pair in shops.values()) else others).append(entry)

    # Six deterministic controls spread across the source order. They exercise
    # distinct non-yarn paths while the intervention should remain inactive.
    controls = [others[round(i * (len(others) - 1) / 5)] for i in range(6)]
    selected = yarn + controls
    assert len(yarn) == 22 and len(selected) == 28
    assert len({(e["action_sha256"], e["seed"], e["source_seat"]) for e in selected}) == 28
    (OUT / "yarn22_controls6_summary.json").write_text(
        json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"wrote {len(yarn)} yarn routes and {len(controls)} controls")


if __name__ == "__main__":
    main()
