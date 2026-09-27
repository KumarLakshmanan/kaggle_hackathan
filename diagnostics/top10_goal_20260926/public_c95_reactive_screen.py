"""Predeclared native reactive screen of a public C95 artifact versus local main."""

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
CANDIDATE = ROOT / "diagnostics" / "public_rayk_top_meta" / "public_c95_main.py"
SEEDS = tuple(range(2609900, 2609908))
EXPECTED_C95 = "489f5d197527f107027626cce79d850fd2ca90edd43d94384b849b6511e27bdb"


def play(job: tuple[int, int]) -> dict:
    seed, seat = job
    return run_game(
        candidate=str(CANDIDATE), opponent=str(BASE),
        seed=seed, candidate_seat=seat, debug=False,
        capture_step=144, candidate_overrides={},
    )


def main() -> None:
    assert hashlib.sha256(CANDIDATE.read_bytes()).hexdigest() == EXPECTED_C95
    jobs = [(seed, seat) for seed in SEEDS for seat in (0, 1)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(play, jobs))
    rows.sort(key=lambda r: (r["seed"], r["candidate_seat"]))
    assert len(rows) == 16
    assert all(r["candidate_status"] == r["opponent_status"] == "DONE" for r in rows)
    pairs = []
    for seed in SEEDS:
        games = [r for r in rows if r["seed"] == seed]
        pairs.append({"seed": seed, "seat_margins": [r["margin"] for r in games],
                      "pair_margin": sum(r["margin"] for r in games)})
    payload = {
        "source_notebook": "raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta",
        "candidate_sha256": EXPECTED_C95,
        "base_sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
        "seeds": SEEDS,
        "rows": rows,
        "pairs": pairs,
    }
    (OUT / "public_c95_vs_main_8native.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("paired wins", sum(p["pair_margin"] > 0 for p in pairs), "/", len(pairs))
    print("seat wins", sum(r["margin"] > 0 for r in rows), "/", len(rows))
    print("mean margin", sum(r["margin"] for r in rows) / len(rows))
    print("max call ms", max(r["candidate_timing"]["max_ms"] for r in rows))
    for pair in pairs:
        print(pair)


if __name__ == "__main__":
    main()
