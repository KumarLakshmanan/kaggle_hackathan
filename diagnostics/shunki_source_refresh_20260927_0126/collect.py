"""Read-only public source refresh, with no selection by game outcome."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from refresh_top_leaderboard_routes import _run_json
from diagnostics.shunki_refresh_farming_20260927 import collect as previous

previous.HERE = HERE


if __name__ == "__main__":
    known = set()
    sources = [ROOT / "diagnostics/shunki_portfolio_20260927/route_manifest.json",
               ROOT / "diagnostics/shunki_refresh_farming_20260927/manifest.json"]
    for path in sources:
        known.update(r["episode_id"] for r in json.loads(path.read_text(encoding="utf8"))["rows"])
    episodes = _run_json(previous.KAGGLE, ["competitions", "episodes", "56553856"])
    listing = HERE / "episodes.json"
    listing.write_text(json.dumps(episodes, indent=2), encoding="utf8")
    new = [ep for ep in episodes if ep["id"] not in known and "PUBLIC" in ep["type"] and ep["state"].endswith("COMPLETED")]
    rows, errors = [], []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(previous.collect, ep): ep["id"] for ep in new}
        for future in as_completed(futures):
            try:
                row = future.result()
                rows.append(row)
                print(row["episode_id"], row["shops"]["144"], flush=True)
            except Exception as exc:
                errors.append({"episode_id": futures[future], "error": str(exc)})
    result = {"submission": 56553856, "checked_utc": datetime.now(timezone.utc).isoformat(),
              "listing_sha256": hashlib.sha256(listing.read_bytes()).hexdigest(),
              "selection": "Every newly listed completed public episode; no reward/outcome filter", "new_ids": [ep["id"] for ep in new],
              "known_count": len(known), "rows": rows, "errors": errors}
    (HERE / "manifest.json").write_text(json.dumps(result, indent=2), encoding="utf8")
    print("New public schedules", len(rows), "errors", len(errors), flush=True)
