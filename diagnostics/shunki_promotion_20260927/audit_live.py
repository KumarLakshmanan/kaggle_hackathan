"""Read-only status and first twelve completed public games of our new upload."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent / "live_0033"
sys.path.insert(0, str(ROOT))
from refresh_top_leaderboard_routes import _run_json

KAGGLE = r"C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe"


def download(episode):
    folder = HERE / "incoming"
    path = folder / f"episode-{episode['id']}-replay.json"
    if not path.exists():
        subprocess.run([KAGGLE, "competitions", "replay", str(episode["id"]), "-p", str(folder), "-q"],
                       check=True, capture_output=True)
    raw = path.read_bytes()
    replay = json.loads(raw)
    names = replay["info"]["TeamNames"]
    seat = names.index("Lakshmanan R")
    return {"episode": episode["id"], "seed": replay["info"]["seed"], "seat": seat,
            "opponent": names[1-seat], "own_cash": replay["rewards"][seat],
            "rival_cash": replay["rewards"][1-seat], "statuses": replay["statuses"],
            "replay_sha256": hashlib.sha256(raw).hexdigest(), "path": str(path),
            "shops": replay["steps"][144][0]["observation"]["town"]["unlocked_shops"][:2]}


if __name__ == "__main__":
    (HERE / "incoming").mkdir(parents=True, exist_ok=True)
    submissions = _run_json(KAGGLE, ["competitions", "submissions", "kaggriculture", "--page-size", "3"])
    (HERE / "submissions.json").write_text(json.dumps(submissions, indent=2), encoding="utf8")
    print("Submission scores:", [(r["ref"], r["publicScore"], r["status"]) for r in submissions], flush=True)
    listing = _run_json(KAGGLE, ["competitions", "episodes", "56591314"])
    (HERE / "episodes.json").write_text(json.dumps(listing, indent=2), encoding="utf8")
    chosen = sorted([r for r in listing if "PUBLIC" in r["type"] and r["state"].endswith("COMPLETED")],
                    key=lambda r: r["createTime"])[:12]
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(download, chosen))
    (HERE / "games.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf8")
    (HERE / "checked_utc.txt").write_text(datetime.now(timezone.utc).isoformat(), encoding="utf8")
    print("Public games", len(rows), "wins", sum(r["own_cash"] > r["rival_cash"] for r in rows),
          "draws", sum(r["own_cash"] == r["rival_cash"] for r in rows), flush=True)
