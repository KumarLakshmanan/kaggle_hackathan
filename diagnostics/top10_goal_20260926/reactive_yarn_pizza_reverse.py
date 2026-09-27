"""Native matched A/B for complete route 100 under Yarn then Pizza shops."""

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

BASE = ROOT / "main.py"
CANDIDATE = ROOT / "exp_yarn_pizza_route100_20260926.py"
SEED_FILE = HERE / "native_yarn_pizza_reverse_seeds.json"
OUTPUT = HERE / "reactive_yarn_pizza_reverse.json"


def play(job):
    arm, seed, seat = job
    row = run_game(str(BASE if arm == "control" else CANDIDATE),
                   str(BASE), seed, seat, False, None, {})
    row["arm"] = arm
    return row


def main():
    selection = json.loads(SEED_FILE.read_text(encoding="utf8"))
    seeds = tuple(int(s) for s in selection["selected"])
    assert len(seeds) == 8 and len(set(seeds)) == 8
    base_sha = hashlib.sha256(BASE.read_bytes()).hexdigest()
    assert base_sha == selection["main_sha256"]
    jobs = [(arm, seed, seat) for arm in ("control", "treatment")
            for seed in seeds for seat in (0, 1)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    assert len(rows) == 32
    assert all(r["candidate_status"] == r["opponent_status"] == "DONE" for r in rows)
    groups = {arm: {(r["seed"], r["candidate_seat"]): r for r in rows if r["arm"] == arm}
              for arm in ("control", "treatment")}
    assert set(groups["control"]) == set(groups["treatment"])
    comparisons = []
    for key in sorted(groups["control"]):
        a, b = groups["control"][key], groups["treatment"][key]
        comparisons.append({
            "seed": key[0], "seat": key[1],
            "control_margin": a["margin"], "treatment_margin": b["margin"],
            "own_cash_delta": b["candidate_reward"] - a["candidate_reward"],
            "rival_cash_delta": b["opponent_reward"] - a["opponent_reward"],
        })
    summary = {
        arm: {
            "wins": sum(r["margin"] > 0 for r in games.values()),
            "margin_sum": sum(r["margin"] for r in games.values()),
            "own_cash_sum": sum(r["candidate_reward"] for r in games.values()),
            "rival_cash_sum": sum(r["opponent_reward"] for r in games.values()),
            "max_candidate_call_ms": max(r["candidate_timing"]["max_ms"]
                                         for r in games.values()),
        } for arm, games in groups.items()
    }
    OUTPUT.write_text(json.dumps({
        "base_sha256": base_sha,
        "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "seed_selection": selection,
        "summary": summary, "comparisons": comparisons, "rows": rows,
    }, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps(summary, indent=2))
    print("margin delta", sum(r["treatment_margin"] - r["control_margin"]
                              for r in comparisons))
    print(OUTPUT)


if __name__ == "__main__":
    main()
