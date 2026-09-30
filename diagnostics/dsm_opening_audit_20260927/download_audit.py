"""Read-only public leading-team opening audit; no agent changes."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from refresh_top_leaderboard_routes import _run_json, _score, _write_route

KAGGLE = r"C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe"


def download(job):
    submission, episode = job
    folder = HERE / "incoming"
    folder.mkdir(exist_ok=True)
    path = folder / f"episode-{episode['id']}-replay.json"
    if not path.exists():
        subprocess.run([KAGGLE, "competitions", "replay", str(episode["id"]), "-p", str(folder), "-q"], check=True, capture_output=True)
    raw = path.read_bytes()
    replay = json.loads(raw)
    assert replay["statuses"] == ["DONE", "DONE"]
    row = _write_route(HERE / "routes", "DSM", 16732748, submission, episode, replay)
    seat = row["source_seat"]
    actions = [frame[seat]["action"] for frame in replay["steps"][1:]]
    physical = [{"farmer": a.get("farmer"), "hands": a.get("hands"),
                 "market": [o for o in a.get("market", []) if o and o[0] in ("HIRE", "BUY_LAND", "BUY_SEED", "BUY_ANIMAL")]}
                for a in actions]
    row.update(replay_path=str(path.resolve()), replay_sha256=hashlib.sha256(raw).hexdigest(),
               opening_hashes={str(n): hashlib.sha256(json.dumps(physical[:n], sort_keys=True).encode()).hexdigest()
                               for n in (1, 24, 72, 144)},
               first_two_shops=replay["steps"][144][0]["observation"]["town"]["unlocked_shops"][:2],
               source_cash=replay["rewards"][seat])
    return row


if __name__ == "__main__":
    submissions = json.loads((HERE / "submissions.json").read_text())
    chosen = max(submissions, key=lambda r: _score(r["publicScore"]))
    listing = _run_json(KAGGLE, ["competitions", "episodes", str(chosen["id"])])
    (HERE / "episodes.json").write_text(json.dumps(listing, indent=2), encoding="utf8")
    episodes = sorted([r for r in listing if "PUBLIC" in r["type"] and r["state"].endswith("COMPLETED")],
                      key=lambda r: r["createTime"], reverse=True)[:12]
    (HERE / "routes").mkdir(exist_ok=True)
    rows = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(download, (chosen["id"], e)) for e in episodes]):
            rows.append(future.result())
            print("public opening", len(rows), "/", len(episodes), flush=True)
    out = {"submission": chosen, "rows": rows,
           "physical_prefix_groups": {str(n): dict(Counter(r["opening_hashes"][str(n)] for r in rows))
                                      for n in (1, 24, 72, 144)}}
    (HERE / "audit.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf8")
    print("distinct physical prefixes", {n: len(groups) for n, groups in out["physical_prefix_groups"].items()}, flush=True)
