"""Read-only collection of public games absent from the frozen 100-game audit."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from diagnostics.live_submission_56530281_20260925 import audit_live

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "live_submission_56572390_20260926" / "audit_latest_100.json"
SUBMISSION = 56572390
FROZEN_NEW_IDS = (
    113839041, 113833626, 113831232, 113832028, 113824143,
    113823702, 113823808, 113816809, 113812534, 113811794,
    113808640, 113800419, 113792858, 113789521, 113783438,
    113783439, 113781680,
)


def main() -> None:
    audit_live.HERE = HERE
    audit_live.SUBMISSION = SUBMISSION
    old = json.loads(OLD.read_text(encoding="utf8"))
    assert old["submission"] == SUBMISSION and len(old["episodes"]) == 100
    old_ids = {int(row["episode_id"]) for row in old["episodes"]}
    all_ids = audit_live.episode_ids(1000)
    selected = list(FROZEN_NEW_IDS)
    # Selection was frozen from the 20:27 listing by temporal ID only.
    assert len(selected) == 17 and len(set(selected)) == 17
    assert not (set(selected) & old_ids)
    assert min(selected) > max(old_ids) and set(selected) <= set(all_ids)
    manifest = {"submission": SUBMISSION,
                "old_audit_sha256": hashlib.sha256(OLD.read_bytes()).hexdigest(),
                "all_public_count": len(all_ids), "selected_ids": selected}
    (HERE / "selection.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    print("selected", len(selected), selected, flush=True)
    ready = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(audit_live.download, episode): episode for episode in selected}
        for future in as_completed(futures):
            episode = futures[future]
            path = future.result()
            if path is not None:
                ready[episode] = path
                print("ready", episode, path.stat().st_size, flush=True)
            else:
                print("pending", episode, flush=True)
    summaries = [audit_live.summarize(ready[episode]) for episode in selected if episode in ready]
    result = {"submission": SUBMISSION, "episodes": summaries}
    (HERE / "audit_new.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf8")
    print("ready_total", len(summaries), "wins", sum(x["outcome"] == "win" for x in summaries),
          "losses", sum(x["outcome"] == "loss" for x in summaries), flush=True)


if __name__ == "__main__":
    main()
