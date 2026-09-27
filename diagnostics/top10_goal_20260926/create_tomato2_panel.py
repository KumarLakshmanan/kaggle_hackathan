"""Freeze a six-route pilot before testing the two-shop tomato bundle gate."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
TOP100 = ROOT / "diagnostics" / "top100_current_2026-09-25" / "summary.json"
TOP20 = ROOT / "diagnostics" / "top20_refresh_2026-09-26" / "summary.json"
SELECTION = (
    (TOP100, 113208346, "Boey", "older high-rank loss; exactly two tomato-demand shops at step 432"),
    (TOP100, 113207763, "Arda Ceylan", "large loss; exactly two tomato-demand shops at step 432"),
    (TOP20, 113448969, "Boey", "fresh high-rank loss; exactly two tomato-demand shops at step 432"),
    (TOP100, 113213818, "THUNDER THUNDER", "winning control with at least three demand shops"),
    (TOP100, 113214301, "Ghost Rule", "winning control on another opening"),
    (TOP100, 113210369, "Dmytro Maliarenko", "winning control on another opening"),
)


def main() -> None:
    rows = []
    sources = {}
    for path, episode, team, reason in SELECTION:
        source = path.read_bytes()
        sources[str(path)] = hashlib.sha256(source).hexdigest()
        found = [row for row in json.loads(source)
                 if row["episode_id"] == episode and row["team"] == team]
        assert len(found) == 1
        rows.append({**found[0], "pilot_reason": reason})
    path = OUT / "tomato2_6routes_summary.json"
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "tomato2_6routes_sources.json").write_text(
        json.dumps({"source_sha256": sources, "candidate": "exp_v219_tomato2_20260926.py",
                    "promotion_gate": "At least one saved loss flips with positive own-cash delta, no winning-control reversal, all DONE; then full top-100 and fresh reactive checks."},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    print(path, len(rows), hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
