"""Fresh matched reactive test of same-item sale-protection exception."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402

HERE = Path(__file__).resolve().parent
BASE = ROOT / "main.py"
CANDIDATE = ROOT / "exp_sale_sameitem_unprotect_20260926.py"
SEEDS = tuple(range(2610100, 2610108))


def play(job: tuple[str, int, int]) -> dict:
    arm, seed, seat = job
    row = run_game(
        candidate=str(BASE if arm == "control" else CANDIDATE),
        opponent=str(BASE), seed=seed, candidate_seat=seat,
        debug=False, capture_step=None, candidate_overrides={},
    )
    row["arm"] = arm
    return row


def main() -> None:
    jobs = [(arm, seed, seat) for arm in ("control", "treatment")
            for seed in SEEDS for seat in (0, 1)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    rows.sort(key=lambda r: (r["arm"], r["seed"], r["candidate_seat"]))
    assert len(rows) == 32
    assert all(r["candidate_status"] == r["opponent_status"] == "DONE" for r in rows)
    groups = {
        arm: {(r["seed"], r["candidate_seat"]): r for r in rows if r["arm"] == arm}
        for arm in ("control", "treatment")
    }
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
    output = HERE / "reactive_sameitem_fresh.json"
    output.write_text(json.dumps({
        "base_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
        "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "seeds": SEEDS, "summary": summary,
        "comparisons": comparisons, "rows": rows,
    }, indent=2, ensure_ascii=False), encoding="utf8")
    print(json.dumps(summary, indent=2))
    print("own cash delta", sum(r["own_cash_delta"] for r in comparisons))
    print("rival cash delta", sum(r["rival_cash_delta"] for r in comparisons))
    print(output)


if __name__ == "__main__":
    main()
