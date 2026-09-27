"""Fresh native reactive A/B for the eight-turn sale-advance horizon."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game  # noqa: E402


OUT = Path(__file__).resolve().parent
BASE = ROOT / "main.py"
CANDIDATE = ROOT / "exp_sale_look8_20260926.py"
SEEDS = tuple(range(2609200, 2609208))


def play(job: tuple[str, int, int]) -> dict:
    arm, seed, seat = job
    row = run_game(
        candidate=str(BASE if arm == "control" else CANDIDATE),
        opponent=str(BASE), seed=seed, candidate_seat=seat,
        debug=False, capture_step=144, candidate_overrides={},
    )
    row["arm"] = arm
    return row


def main() -> None:
    identity = json.loads((OUT / "look8_identity_seed2609200.json").read_text(encoding="utf-8"))
    selfplay = json.loads((OUT / "main_selfplay_seed2609200.json").read_text(encoding="utf-8"))
    for a, b in zip(identity["rows"], selfplay["rows"]):
        assert (a["candidate_reward"], a["opponent_reward"], a["candidate_status"], a["opponent_status"]) == (
            b["candidate_reward"], b["opponent_reward"], b["candidate_status"], b["opponent_status"]
        )
    jobs = [(arm, seed, seat) for arm in ("control", "treatment") for seed in SEEDS for seat in (0, 1)]
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(play, job): job for job in jobs}
        for future in concurrent.futures.as_completed(futures):
            row = future.result()
            rows.append(row)
            print(f"{row['arm']} seed={row['seed']} seat={row['candidate_seat']} "
                  f"margin={row['margin']:+.0f} "
                  f"adv={row['candidate_telemetry'].get('adv_turns', 0)}", flush=True)
    rows.sort(key=lambda r: (r["arm"], r["seed"], r["candidate_seat"]))
    assert all(r["candidate_status"] == r["opponent_status"] == "DONE" for r in rows)
    control = {(r["seed"], r["candidate_seat"]): r for r in rows if r["arm"] == "control"}
    treatment = {(r["seed"], r["candidate_seat"]): r for r in rows if r["arm"] == "treatment"}
    assert len(control) == len(treatment) == 2 * len(SEEDS)
    comparisons = []
    for key in sorted(control):
        a, b = control[key], treatment[key]
        comparisons.append({"seed": key[0], "seat": key[1],
                            "control_margin": a["margin"], "treatment_margin": b["margin"],
                            "own_cash_delta": b["candidate_reward"] - a["candidate_reward"],
                            "rival_cash_delta": b["opponent_reward"] - a["opponent_reward"],
                            "adv_turns": b["candidate_telemetry"].get("adv_turns", 0)})
    payload = {"base_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
               "candidate_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
               "seeds": SEEDS, "rows": rows, "comparisons": comparisons}
    (OUT / "reactive_look8_native.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("control wins", sum(r["margin"] > 0 for r in control.values()))
    print("treatment wins", sum(r["margin"] > 0 for r in treatment.values()))
    print("own cash delta", sum(c["own_cash_delta"] for c in comparisons))
    print("rival cash delta", sum(c["rival_cash_delta"] for c in comparisons))
    print("adv turns", sum(c["adv_turns"] for c in comparisons))


if __name__ == "__main__":
    main()
