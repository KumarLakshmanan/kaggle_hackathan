"""Native both-seat mechanism smoke for the latched observed-stock rule."""

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402


HERE = Path(__file__).resolve().parent
LIVE = HERE.parent / "live_submission_56572390_20260926"
EPISODE = 113642505
SOURCE = ROOT / "main.py"
CANDIDATE = ROOT / "exp_mirror_stock_frontload_latched_20260927.py"
SOURCE_HASH = "489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b"
CANDIDATE_HASH = "73aa01509f6ab005e527d600b67bae108184302418b00463310d36931e3b28b2"
OUTPUT = HERE / "smoke_latched.json"


def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_HASH
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == CANDIDATE_HASH
    audit = json.loads((LIVE / "audit_latest_100.json").read_text(encoding="utf-8"))["episodes"]
    routes = json.loads((LIVE / "mirror_dev_routes" / "summary.json").read_text(encoding="utf-8"))
    live = next(row for row in audit if row["episode_id"] == EPISODE)
    route = next(row for row in routes if row["episode_id"] == EPISODE)
    rows = []
    for seat in (0, 1):
        control = run_game(str(SOURCE), f"rawroute:{route['path']}", live["seed"], seat, False, None, {})
        candidate = run_game(str(CANDIDATE), f"rawroute:{route['path']}", live["seed"], seat, False, None, {})
        if seat == live["our_seat"]:
            assert (control["candidate_reward"], control["opponent_reward"]) == (live["our_cash"], live["rival_cash"])
        rows.append({"seat": seat, "control": control, "candidate": candidate})
    output = {"episode_id": EPISODE, "team": live["opponent"], "seed": live["seed"], "rows": rows}
    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    for row in rows:
        a, b = row["control"], row["candidate"]
        print(row["seat"], "control", a["margin"], "candidate", b["margin"],
              "cash", b["candidate_reward"], b["opponent_reward"],
              "status", b["candidate_status"], b["opponent_status"],
              "telemetry", b["candidate_telemetry"])


if __name__ == "__main__":
    main()
