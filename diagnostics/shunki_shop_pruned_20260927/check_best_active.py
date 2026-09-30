"""Conditional, prospectively frozen comparison with active submission 56590642."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.shunki_route_search_20260927 import confirm_native as runner

runner.HERE = HERE
runner.OUT = HERE / "best_active"
runner.NEW = ROOT / "exp_shunki_shop_pruned_20260927.py"
runner.RIVALS = {"best1f": (ROOT / "exp_shunki_visible_repair_20260927.py", 2650000)}
runner.BRANCHES = [key for key in runner.BRANCHES if key != "BAKERY|PET_CAFE"]
runner.NEEDED = 4
runner.MAX_SCAN = 2048
runner.__file__ = __file__


def summarize(rows, panels):
    summary = {}
    for arm in ("old", "new"):
        games = [r for r in rows if r["arm"] == arm]
        summary[arm] = {"games": len(games), "wins": sum(r["points"] == 1 for r in games),
                        "draws": sum(r["points"] == .5 for r in games),
                        "paired_points": sum(r["points"] for r in games)/2,
                        "activated_seats": sum(bool((r["telemetry"] or {}).get("optimized_turns")) for r in games)}
    checks = {"all_48_games": len(rows) == 48,
              "all_done": all(r["statuses"] == ["DONE", "DONE"] for r in rows),
              "complete_coverage": all(len(panels["best1f"][branch]) == 4 for branch in runner.BRANCHES),
              "no_regression": summary["new"]["paired_points"] >= summary["old"]["paired_points"],
              "at_least_8_of_12_points": summary["new"]["paired_points"] >= 8}
    return {"candidate_sha256": runner.sha(runner.NEW), "summary": summary, "checks": checks,
            "gate_pass": all(checks.values()), "rows": rows}


runner.summarize = summarize


if __name__ == "__main__":
    native = HERE / "native/confirmation.json"
    if not native.exists():
        raise SystemExit("Primary native confirmation is not finished; do not run this conditional stage yet.")
    prior = json.loads(native.read_text(encoding="utf8"))
    assert prior["gate_pass"], "Primary native gate rejected the candidate"
    assert prior["candidate_sha256"] == runner.sha(runner.NEW)
    assert runner.sha(runner.RIVALS["best1f"][0]) == "1f22192297821ab5205b8cdcbd22bd1fab30d546860f3c61e8096a2a4355446b"
    runner.OUT.mkdir(exist_ok=True)
    frozen = {"gate_plan_sha256": runner.sha(HERE / "BEST_ACTIVE_GATE.md"),
              "primary_confirmation_sha256": runner.sha(native),
              "reused_harness_sha256": runner.sha(ROOT / "diagnostics/shunki_route_search_20260927/confirm_native.py")}
    provenance = runner.OUT / "provenance.json"
    if provenance.exists():
        assert json.loads(provenance.read_text(encoding="utf8")) == frozen
    else:
        provenance.write_text(json.dumps(frozen, indent=2), encoding="utf8")
    runner.main()
