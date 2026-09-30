"""Read-only c68 comparison on the three current failing action tapes."""

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game, engine_version

PRIOR = ROOT / "main_uploaded_disjoint_integrated_20260927_c68fa46f.py"
PRIOR_SHA = "c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad"
TARGETS = {"DECEM", "Boey", "Vadim Vasilenko"}


def play(job):
    entry, seat = job
    assert hashlib.sha256(PRIOR.read_bytes()).hexdigest() == PRIOR_SHA
    route = json.loads(gzip.decompress(Path(entry["path"]).read_bytes()))
    digest = hashlib.sha256(json.dumps(route["actions"], sort_keys=True,
                                       separators=(",", ":")).encode()).hexdigest()
    assert digest == entry["action_sha256"]
    game = run_game(str(PRIOR), "rawroute:" + entry["path"],
                    int(entry["seed"]), seat, False, 144, {})
    return {"rank": entry["rank"], "team": entry["team"],
            "team_id": entry["team_id"], "episode_id": entry["episode_id"], **game}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf8", errors="replace")
    assert not (HERE / "prior_top3.json").exists()
    entries = [r for r in json.loads((HERE / "manifest.json").read_text(encoding="utf8"))["rows"]
               if r["team"] in TARGETS]
    assert len(entries) == 3 and {r["team"] for r in entries} == TARGETS
    out = {"started_at_utc": datetime.now(timezone.utc).isoformat(),
           "source_manifest_sha256": hashlib.sha256((HERE / "manifest.json").read_bytes()).hexdigest(),
           "prior_sha256": PRIOR_SHA, "engine_version": engine_version,
           "complete": False, "games": []}

    def save():
        (HERE / "prior_top3.json").write_text(json.dumps(out, indent=2,
                                      ensure_ascii=False), encoding="utf8")

    save()
    with ProcessPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(play, (entry, seat))
                                    for entry in entries for seat in (0, 1)]):
            row = future.result()
            out["games"].append(row)
            out["games"].sort(key=lambda r: (r["rank"], r["candidate_seat"]))
            save()
            print(f'{len(out["games"])}/6 {row["team"]} seat={row["candidate_seat"]} '
                  f'{row["result"]} margin={row["margin"]:+.0f}', flush=True)
    assert len(out["games"]) == 6
    out.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat(),
               all_done=all(r["candidate_status"] == r["opponent_status"] == "DONE"
                            and r["frames"] == 720 for r in out["games"]))
    save()
