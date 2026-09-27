"""Both-seat development test for every saved ICE/BRUNCH route."""
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game

CANDIDATE = ROOT / "exp_shunki_ice_schedule_20260927.py"


def play(job):
    target, seat = job
    r = run_game(str(CANDIDATE), "rawroute:" + target["opponent_path"],
                 target["seed"], seat, False, 144, {})
    return {"team": target["team"], "seed": target["seed"], "seat": seat,
            "own_cash": r["candidate_reward"], "rival_cash": r["opponent_reward"],
            "margin": r["margin"], "original_margin": target["seat_margins"][str(seat)]["candidate"],
            "statuses": [r["candidate_status"], r["opponent_status"]],
            "shops": r["candidate_capture"]["shops"][:2]}


def main():
    build = json.loads((HERE / "build_manifest.json").read_text(encoding="utf8"))
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == build["candidate_sha256"]
    targets = json.loads((HERE / "development_routes.json").read_text(encoding="utf8"))
    with ProcessPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(play, [(r, s) for r in targets for s in (0, 1)]))
    paired = []
    for target in targets:
        pair = [r for r in rows if r["team"] == target["team"]]
        paired.append({"team": target["team"], "original_margin": sum(r["original_margin"] for r in pair),
                       "new_margin": sum(r["margin"] for r in pair)})
    all_done = all(r["statuses"] == ["DONE", "DONE"] for r in rows)
    flips_up = sum(r["original_margin"] <= 0 and r["new_margin"] > 0 for r in paired)
    flips_down = sum(r["original_margin"] > 0 and r["new_margin"] <= 0 for r in paired)
    summary = {"all_done": all_done, "flips_up": flips_up, "flips_down": flips_down,
               "gate_pass": all_done and flips_up >= 1 and flips_down == 0}
    (HERE / "development.json").write_text(json.dumps({"candidate_sha256": build["candidate_sha256"],
                                                       "summary": summary, "paired": paired, "rows": rows}, indent=2), encoding="utf8")
    print(json.dumps({"summary": summary, "paired": paired}, indent=2), flush=True)


if __name__ == "__main__":
    main()
