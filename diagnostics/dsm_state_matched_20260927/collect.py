from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from refresh_top_leaderboard_routes import _run_json, _write_route

KAGGLE = r"C:/Users/Veeramani Selvaraj/AppData/Roaming/Python/Python314/Scripts/kaggle.exe"
SUBMISSION = 56582621
CACHE = {r["episode_id"]: r for r in json.loads((ROOT / "diagnostics/dsm_opening_audit_20260927/audit.json").read_text())["rows"]}


def collect(episode):
    eid = int(episode["id"])
    if eid in CACHE:
        path = Path(CACHE[eid]["replay_path"])
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == CACHE[eid]["replay_sha256"]
        origin = "existing exact cache"
    else:
        path = HERE / "raw_archive" / ("episode-" + str(eid) + "-replay.json.gz")
        if path.exists():
            raw = gzip.decompress(path.read_bytes())
            origin = "existing compressed collection file"
        else:
            temporary = (HERE / "unpacked" / ("episode-" + str(eid) + "-replay.json")).resolve()
            assert temporary.parent == (HERE / "unpacked").resolve()
            assert not temporary.exists()
            proc = subprocess.run([KAGGLE, "competitions", "replay", str(eid), "-p", str(temporary.parent), "-q"], capture_output=True)
            if proc.returncode:
                return {"episode": eid, "error": "Replay download failed", "exit_code": proc.returncode}
            raw = temporary.read_bytes()
            compressed = gzip.compress(raw, compresslevel=6)
            assert hashlib.sha256(gzip.decompress(compressed)).digest() == hashlib.sha256(raw).digest()
            path.write_bytes(compressed)
            assert hashlib.sha256(gzip.decompress(path.read_bytes())).digest() == hashlib.sha256(raw).digest()
            temporary.unlink()
            origin = "new losslessly compressed replay"
    data = json.loads(raw)
    if data["statuses"] != ["DONE", "DONE"] or len(data["steps"]) != 720:
        return {"episode": eid, "ineligible": "Not a complete 720-frame DONE/DONE episode", "replay_path": str(path)}
    row = _write_route(HERE / "routes", "DSM", 16732748, SUBMISSION, episode, data)
    row.update(replay_path=str(path.resolve()), replay_sha256=hashlib.sha256(raw).hexdigest(),
               compressed=path.suffix == ".gz", origin=origin, source_bytes=len(raw))
    return row


if __name__ == "__main__":
    for name in ("unpacked", "raw_archive", "routes"):
        (HERE / name).mkdir(exist_ok=True)
    listing = _run_json(KAGGLE, ["competitions", "episodes", str(SUBMISSION)])
    (HERE / "episodes.json").write_text(json.dumps(listing, indent=2), encoding="utf8")
    chosen = sorted([r for r in listing if "PUBLIC" in r["type"] and r["state"].endswith("COMPLETED")],
                    key=lambda r: r["createTime"], reverse=True)[:128]
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "submission": SUBMISSION,
              "selection": "Latest completed public episodes, no reward filtering", "selected_episodes": chosen,
              "rows": [], "complete": False}
    (HERE / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    with ThreadPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(collect, e) for e in chosen]):
            row = f.result(); report["rows"].append(row)
            (HERE / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf8")
            print(len(report["rows"]), "/", len(chosen), row.get("episode_id", row.get("episode")), row.get("error", row.get("ineligible", "stored")), flush=True)
    report["complete"] = True
    report["eligible"] = sum("action_sha256" in r for r in report["rows"])
    (HERE / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    print("Completed", report["eligible"], "eligible source episodes", flush=True)
