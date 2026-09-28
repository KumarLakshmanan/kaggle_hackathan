"""Extend the live-loss ledger from the frozen 17:25z to 17:47z cohort."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path

from trace_losses import EXPECTED_MAIN_SHA256, MAIN, trace_one

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OLD = HERE / "live_loss_ledgers_172258.json"
COHORT = ROOT / "diagnostics/new_live_56609430_20260927/cohort_174722.json"
OUT = HERE / "live_loss_ledgers_174722.json"


def main() -> None:
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == EXPECTED_MAIN_SHA256
    old = json.loads(OLD.read_text(encoding="utf-8"))
    raw = COHORT.read_bytes()
    cohort = json.loads(raw)
    latest = {int(g["episode_id"]): g for g in cohort["games"] if g["result"] == "loss"}
    prior = {int(r["episode_id"]): r for r in old["rows"]}
    assert len(latest) == 26 and len(prior) == 22
    assert set(prior) < set(latest) and len(set(latest) - set(prior)) == 4
    for episode_id, row in prior.items():
        game = latest[episode_id]
        assert row["margin"] == game["margin"] and row["opponent"] == game["opponent"]
    new_games = [latest[i] for i in sorted(set(latest) - set(prior))]
    with ProcessPoolExecutor(max_workers=3) as pool:
        extra = list(pool.map(trace_one, new_games))
    rows = sorted([*old["rows"], *extra], key=lambda row: row["episode_id"])
    output = {
        **old,
        "cohort_sha256": hashlib.sha256(raw).hexdigest(),
        "cohort_path": str(COHORT.resolve()),
        "cohort_episode_count": len(cohort["games"]),
        "loss_count": len(rows),
        "selection": "All 26 losses in cohort_174722.json; the prior 22 rows were reconciled by episode, opponent, and margin, and four newly added episodes were traced.",
        "rows": rows,
    }
    OUT.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(OUT.resolve()), "new_rows": [
        {"episode_id": r["episode_id"], "opponent": r["opponent"], "margin": r["margin"],
         "product_gap": r["product_net_cash_difference"], "worker_own_nochange": r["worker_own"]["unchanged"],
         "worker_rival_nochange": r["worker_rival"]["unchanged"],
         "market_failures_own": r["market_failures_own"]} for r in extra]},
        indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
