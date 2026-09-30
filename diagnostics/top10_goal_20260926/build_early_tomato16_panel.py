"""Freeze top tomato-gap losses and high-rank wins for a day-16 V219 pilot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "diagnostics/top100_refresh_2026-09-26_0708"
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "early_tomato16_panel20.json"
META = HERE / "early_tomato16_panel20_meta.json"


def main() -> None:
    ledgers = json.loads((PANEL / "all34_loss_ledgers_s0.json").read_text(encoding="utf8"))["rows"]
    targets = sorted(ledgers, key=lambda row: (row["net_item_differences"].get("TOMATO", 0),
                                               row["rank"]))[:12]
    top10 = json.loads((PANEL / "main_panel_analysis.json").read_text(encoding="utf8"))["top10"]
    controls = [row for row in top10 if 2 <= row["rank"] <= 9 and row["paired_margin"] > 0]
    assert len(targets) == 12 and len(controls) == 8
    wanted = {row["action_sha256"] for row in targets + controls}
    routes = json.loads((PANEL / "routes/summary.json").read_text(encoding="utf8"))
    selected = [row for row in routes if row["action_sha256"] in wanted]
    assert len(selected) == len(wanted) == 20
    OUTPUT.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf8")
    meta = {"targets": [{"rank": row["rank"], "team": row["team"],
                         "tomato_net_cash_gap": row["net_item_differences"].get("TOMATO", 0),
                         "action_sha256": row["action_sha256"]} for row in targets],
            "controls": [{"rank": row["rank"], "team": row["team"],
                          "paired_margin": row["paired_margin"],
                          "action_sha256": row["action_sha256"]} for row in controls],
            "summary_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf8")
    print("targets", len(targets), "controls", len(controls),
          "distinct hashes", len(wanted), "summary sha256", meta["summary_sha256"])
    print(OUTPUT)


if __name__ == "__main__":
    main()
