from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from paired_benchmark import run_game


def run(job):
    seed, seat = job
    result = run_game(str(ROOT / "exp_shunki_trade_quantity_20260927.py"),
                      str(ROOT / "exp_shunki_market_queue_20260927.py"), seed, seat, False, 144, {})
    return {"seed": seed, "seat": seat, "game": result}


if __name__ == "__main__":
    manifest = json.loads((HERE / "manifest.json").read_text())
    assert hashlib.sha256(Path(manifest["candidate"]).read_bytes()).hexdigest() == manifest["candidate_sha256"]
    rows = []
    report = {"candidate_sha256": manifest["candidate_sha256"], "rows": rows, "complete": False, "passed": False}
    with ProcessPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(run, (seed, seat)) for seed in range(2674000, 2674008) for seat in (0, 1)]):
            row = future.result(); rows.append(row)
            (HERE / "development.json").write_text(json.dumps(report, indent=2), encoding="utf8")
            print(len(rows), "/16", row["seed"], row["seat"], row["game"]["margin"], flush=True)
    done = all(r["game"]["candidate_status"] == r["game"]["opponent_status"] == "DONE" for r in rows)
    points = sum(1 if r["game"]["margin"] > 0 else .5 if r["game"]["margin"] == 0 else 0 for r in rows)
    errors = sum((r["game"].get("candidate_telemetry") or {}).get(k, 0) for r in rows for k in ("quantity_errors", "queue_errors"))
    active = sum(all((r["game"].get("candidate_telemetry") or {}).get("quantity_turns", 0) > 0 for r in rows if r["seed"] == seed) for seed in range(2674000, 2674008))
    report.update(complete=True, passed=done and errors == 0 and points >= 12 and active >= 6,
                  all_done=done, errors=errors, win_points=points, active_pairs=active)
    (HERE / "development.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    print({k: v for k, v in report.items() if k != "rows"}, flush=True)
