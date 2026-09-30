"""Freeze five original-shop routes for a complete mixed-herd schedule pilot."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "diagnostics/top100_current_2026-09-25/summary.json"
NEW = ROOT / "diagnostics/top100_refresh_2026-09-26/summary.json"
OUT = Path(__file__).with_name("egg_yarn_5routes_summary.json")

# The four older routes have Brunch Spot/Yarn Store as their first two
# original shops (verified in the old shop_pair_probe.json). DSM has the same
# observed pair in the exact trace saved in the new panel.
TARGETS = {
    ("Gleb Tumanov", 113211854),
    ("Matin Urdu", 113216149),  # winning control
    ("ShunkiKyoya", 113216162),
    ("keiz", 113211910),
    ("DSM", 113531265),
}

rows = json.loads(OLD.read_text(encoding="utf8")) + json.loads(NEW.read_text(encoding="utf8"))
selected = [r for r in rows if (r["team"], r["episode_id"]) in TARGETS]
assert {(r["team"], r["episode_id"]) for r in selected} == TARGETS
assert len(selected) == len(TARGETS)
OUT.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf8")
print(OUT)
