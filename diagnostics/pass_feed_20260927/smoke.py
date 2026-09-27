"""Two-route two-seat native smoke against frozen original cash pairs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from paired_benchmark import run_game  # noqa: E402

CANDIDATE = ROOT / "exp_pass_feed_20260927.py"
EXPECTED_CANDIDATE = "067f28545b20a20178a615715fb6313759a876f2468b367afc72db438335d3f1"
PANEL_DIR = ROOT / "diagnostics" / "top100_refresh_2026-09-26_0708"


def main() -> None:
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == EXPECTED_CANDIDATE
    manifest = json.loads((PANEL_DIR / "main_loss_manifest.json").read_text(encoding="utf8"))
    panel = json.loads((PANEL_DIR / "main_100routes.json").read_text(encoding="utf8"))
    result = []
    for name in ("Boey", "mhw"):
        case = next(c for c in manifest if c["team"] == name)
        baseline = next(r for r in panel["rows"] if r["seed"] == case["seed"]
                        and r["action_sha256"] == case["action_sha256"])
        for seat in (0, 1):
            old = next(g for g in baseline["games"] if g["candidate_seat"] == seat)
            new = run_game(str(CANDIDATE), f"rawroute:{case['opponent_path']}",
                           int(case["seed"]), seat, False, None, {})
            assert new["candidate_status"] == new["opponent_status"] == "DONE"
            row = {"team": name, "seed": case["seed"], "seat": seat,
                   "baseline_own": old["candidate_reward"],
                   "baseline_rival": old["opponent_reward"],
                   "candidate_own": new["candidate_reward"],
                   "candidate_rival": new["opponent_reward"],
                   "delta_own": new["candidate_reward"] - old["candidate_reward"],
                   "delta_rival": new["opponent_reward"] - old["opponent_reward"],
                   "delta_margin": new["margin"] - old["margin"],
                   "telemetry": new["candidate_telemetry"],
                   "candidate_timing": new["candidate_timing"]}
            result.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    output = HERE / "smoke_two_losses.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print(output)


if __name__ == "__main__":
    main()
