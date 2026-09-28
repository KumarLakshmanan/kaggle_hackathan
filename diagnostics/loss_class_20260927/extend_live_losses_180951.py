"""Extend the 17:47 live-loss trace ledger to the 18:09 cohort."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path

from trace_losses import EXPECTED_MAIN_SHA256, MAIN, trace_one

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OLD = HERE / "live_loss_ledgers_174722.json"
COHORT = ROOT / "diagnostics/new_live_56609430_20260927/cohort_180951.json"
OUT = HERE / "live_loss_ledgers_180951.json"


def main() -> None:
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == EXPECTED_MAIN_SHA256
    old = json.loads(OLD.read_text(encoding="utf-8"))
    raw_cohort = COHORT.read_bytes()
    cohort = json.loads(raw_cohort)
    latest = {
        int(game["episode_id"]): game
        for game in cohort["games"]
        if game["result"] == "loss"
    }
    prior = {int(row["episode_id"]): row for row in old["rows"]}
    assert len(latest) == 30, len(latest)
    assert len(prior) == 26, len(prior)
    assert set(prior) < set(latest)
    new_ids = sorted(set(latest) - set(prior))
    assert len(new_ids) == 4, new_ids

    verified_hashes = []
    for episode_id, game in latest.items():
        source = Path(game["replay_path"])
        replay_bytes = gzip.decompress(source.read_bytes())
        digest = hashlib.sha256(replay_bytes).hexdigest()
        assert digest == game["replay_sha256"], (episode_id, digest)
        replay = json.loads(replay_bytes)
        assert replay["module_version"] == "1.32.7", episode_id
        assert replay["statuses"] == ["DONE", "DONE"] and len(replay["steps"]) == 720
        verified_hashes.append({"episode_id": episode_id, "sha256": digest})

    for episode_id, row in prior.items():
        game = latest[episode_id]
        assert row["margin"] == game["margin"], episode_id
        assert row["opponent"] == game["opponent"], episode_id
        assert row["candidate_reward"] == game["own_cash"], episode_id
        assert row["opponent_reward"] == game["opponent_cash"], episode_id
        assert row["seed"] == game["seed"], episode_id
        assert row["seat"] == game["candidate_seat"], episode_id

    new_games = [latest[episode_id] for episode_id in new_ids]
    with ProcessPoolExecutor(max_workers=3) as pool:
        extra = list(pool.map(trace_one, new_games))
    extra.sort(key=lambda row: row["episode_id"])
    rows = sorted([*old["rows"], *extra], key=lambda row: row["episode_id"])
    output = {
        **old,
        "cohort_sha256": hashlib.sha256(raw_cohort).hexdigest(),
        "cohort_path": str(COHORT.resolve()),
        "cohort_episode_count": len(cohort["games"]),
        "loss_count": len(rows),
        "selection": (
            "All 30 losses in cohort_180951.json; all 26 prior rows were "
            "reconciled by episode, opponent, margin, rewards, seat, and seed; "
            "all 30 raw replay hashes were verified; four new episodes were traced."
        ),
        "verified_raw_replay_hashes": sorted(verified_hashes, key=lambda row: row["episode_id"]),
        "rows": rows,
    }
    OUT.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "output": str(OUT.resolve()),
        "cohort_sha256": output["cohort_sha256"],
        "loss_count": len(rows),
        "old_rows_reconciled": len(prior),
        "all_raw_hashes_verified": len(verified_hashes) == 30,
        "new_rows": [{
            "episode_id": row["episode_id"],
            "opponent": row["opponent"],
            "margin": row["margin"],
            "product_gap": row["product_net_cash_difference"],
            "worker_own_nochange": row["worker_own"]["unchanged"],
            "worker_rival_nochange": row["worker_rival"]["unchanged"],
            "market_failures_own": row["market_failures_own"],
        } for row in extra],
    }, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
