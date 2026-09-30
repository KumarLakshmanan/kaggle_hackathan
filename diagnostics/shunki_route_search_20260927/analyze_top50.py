import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
old = json.loads((ROOT / "diagnostics/top50_refresh_20260927_2303/candidate_top50.json").read_text(encoding="utf8"))
new = json.loads((HERE / "top50.json").read_text(encoding="utf8"))
assert old["summary_sha256"] == new["summary_sha256"]
a, b = ({r["team"]: r for r in panel["rows"]} for panel in (old, new))
assert a.keys() == b.keys() and len(a) == 50
rows = []
for team in sorted(a):
    ga = sorted(a[team]["games"], key=lambda r: r["candidate_seat"])
    gb = sorted(b[team]["games"], key=lambda r: r["candidate_seat"])
    rows.append({"team": team, "old_margins": [r["margin"] for r in ga],
                 "new_margins": [r["margin"] for r in gb],
                 "old_sweep": all(r["margin"] > 0 for r in ga),
                 "new_sweep": all(r["margin"] > 0 for r in gb),
                 "all_done": all(r["candidate_status"] == r["opponent_status"] == "DONE" for r in ga + gb)})
summary = {"old_sweeps": sum(r["old_sweep"] for r in rows), "new_sweeps": sum(r["new_sweep"] for r in rows),
           "seat_wins": sum(m > 0 for r in rows for m in r["new_margins"]),
           "up": [r["team"] for r in rows if r["new_sweep"] and not r["old_sweep"]],
           "down": [r["team"] for r in rows if r["old_sweep"] and not r["new_sweep"]],
           "all_done": all(r["all_done"] for r in rows)}
summary["gate_pass"] = summary["all_done"] and summary["new_sweeps"] > 42 and len(summary["down"]) <= 1
(HERE / "top50_decision.json").write_text(json.dumps({"candidate_sha256": new["candidate_sha256"],
                                                     "summary": summary, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf8")
print(json.dumps(summary, indent=2, ensure_ascii=False))
