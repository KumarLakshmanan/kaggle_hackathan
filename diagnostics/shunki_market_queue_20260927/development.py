from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game


def game(job):
    seed, seat = job
    r = run_game(str(ROOT/"exp_shunki_market_queue_20260927.py"), str(ROOT/"main_uploaded_shunki_schedule_20260927_3cc0f69f.py"), seed, seat, False, 144, {})
    return {"seed": seed, "seat": seat, "game": r}


if __name__ == "__main__":
    manifest = json.loads((HERE/"manifest.json").read_text())
    assert hashlib.sha256((ROOT/"exp_shunki_market_queue_20260927.py").read_bytes()).hexdigest() == manifest["candidate_sha256"]
    rows = []
    report = {"manifest": manifest, "rows": rows}
    with ProcessPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(game, (seed, seat)) for seed in range(2658000,2658008) for seat in (0,1)]):
            r = f.result(); rows.append(r)
            (HERE/"development.json").write_text(json.dumps(report,indent=2),encoding="utf8")
            print(r["seed"],r["seat"],r["game"]["margin"],r["game"].get("candidate_telemetry"),flush=True)
    points = sum(1 if r["game"]["margin"] > 0 else .5 if r["game"]["margin"] == 0 else 0 for r in rows)/2
    active = len({r["seed"] for r in rows if r["game"].get("candidate_telemetry",{}).get("queue_turns",0)})
    done = all(r["game"]["candidate_status"] == r["game"]["opponent_status"] == "DONE" for r in rows)
    errors = sum(r["game"].get("candidate_telemetry",{}).get("queue_errors",0) for r in rows)
    report["decision"] = {"paired_points":points,"active_pairs":active,"all_done":done,"errors":errors,
                          "passed": points >= 6 and active >= 4 and done and errors == 0}
    (HERE/"development.json").write_text(json.dumps(report,indent=2),encoding="utf8")
    print(json.dumps(report["decision"]),flush=True)
