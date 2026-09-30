"""Add losses appearing in the 17:25Z cohort to the frozen 17:12Z ledger."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path

from trace_losses import EXPECTED_MAIN_SHA256, MAIN, trace_one

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OLD = HERE / "live_loss_ledgers.json"
COHORT = ROOT / "diagnostics/new_live_56609430_20260927/cohort_172258.json"
OUT = HERE / "live_loss_ledgers_172258.json"


def main() -> None:
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == EXPECTED_MAIN_SHA256
    old = json.loads(OLD.read_text(encoding="utf-8"))
    raw = COHORT.read_bytes()
    cohort = json.loads(raw)
    latest = {int(g["episode_id"]): g for g in cohort["games"] if g["result"] == "loss"}
    prior = {int(r["episode_id"]): r for r in old["rows"]}
    assert len(latest) == 22 and len(prior) == 21
    assert set(prior) < set(latest)
    assert len(set(latest) - set(prior)) == 1
    for episode_id, row in prior.items():
        game = latest[episode_id]
        assert row["margin"] == game["margin"]
        assert row["opponent"] == game["opponent"]
    new_game = latest[next(iter(set(latest) - set(prior)))]
    with ProcessPoolExecutor(max_workers=1) as pool:
        extra = pool.submit(trace_one, new_game).result()
    rows = sorted([*old["rows"], extra], key=lambda row: row["episode_id"])
    output = {
        **old,
        "cohort_sha256": hashlib.sha256(raw).hexdigest(),
        "cohort_path": str(COHORT.resolve()),
        "cohort_episode_count": len(cohort["games"]),
        "loss_count": len(rows),
        "selection": "All 22 losses in cohort_172258.json; the 21 prior rows were hash/cash checked against the new cohort and episode 114271958 was newly traced.",
        "rows": rows,
    }
    OUT.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(OUT.resolve()), "new_episode": extra["episode_id"],
                      "new_opponent": extra["opponent"], "margin": extra["margin"],
                      "product_gap": extra["product_net_cash_difference"],
                      "own_worker": extra["worker_own"], "rival_worker": extra["worker_rival"]},
                     indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
