"""Collect all newly completed public schedules without selecting outcomes."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
KAGGLE = r"C:\Users\Veeramani Selvaraj\AppData\Roaming\Python\Python314\Scripts\kaggle.exe"
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module


def collect(ep):
    eid = int(ep["id"])
    incoming = HERE / "incoming"
    incoming.mkdir(parents=True, exist_ok=True)
    path = incoming / f"episode-{eid}-replay.json"
    if not path.is_file():
        subprocess.run([KAGGLE, "competitions", "replay", str(eid), "-p", str(incoming), "-q"], check=True, capture_output=True)
    raw = path.read_bytes()
    replay = json.loads(raw)
    assert replay["statuses"] == ["DONE", "DONE"]
    seat = replay["info"]["TeamNames"].index("ShunkiKyoya")
    actions = [frame[seat].get("action") or {} for frame in replay["steps"][1:]]
    assert len(actions) == 719
    shops = {str(t): replay["steps"][t][seat]["observation"]["town"]["unlocked_shops"]
             for t in (72, 144, 216, 288, 360, 432, 504, 576)}
    target = HERE / f"episode-{eid}-route.json.gz"
    with gzip.open(target, "wt", encoding="utf8") as f:
        json.dump({"actions": actions, "shops": shops}, f, separators=(",", ":"))
    return {"episode_id": eid, "source_seat": seat, "seed": replay["info"]["seed"],
            "replay_sha256": hashlib.sha256(raw).hexdigest(), "route_path": str(target.resolve()),
            "shops": shops}


if __name__ == "__main__":
    frozen = ROOT / "diagnostics/shunki_portfolio_20260927/latest_episodes_2342.json"
    episodes = json.loads(frozen.read_text())["uncollected"]
    rows = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(collect, ep) for ep in episodes]):
            r = future.result()
            rows.append(r)
            print(r["episode_id"], r["shops"]["144"], flush=True)
    module = _load_module(ROOT / "exp_shunki_ice_schedule_20260927.py", "refresh_prefix")
    opportunities = []
    for row in rows:
        with gzip.open(row["route_path"], "rt", encoding="utf8") as f:
            tape = json.load(f)["actions"]
        for count in range(2, 9):
            step = count * 72
            parts = row["shops"][str(step)][:count]
            key = "|".join(parts)
            parent = None
            for n in range(1, count):
                parent = module._DATA["route_map"].get("|".join(parts[:n]), parent)
            if parent is not None and module._DATA["routes"][str(parent)][:step] == tape[:step]:
                existing = module._DATA["route_map"].get(key)
                if existing is None:
                    opportunities.append({"key": key, "step": step, "episode_id": row["episode_id"], "parent": parent})
    (HERE / "manifest.json").write_text(json.dumps({"listing_sha256": hashlib.sha256(frozen.read_bytes()).hexdigest(), "rows": rows, "new_exact_compatible_prefixes": opportunities}, indent=2), encoding="utf8")
    print("New exact-compatible prefixes:", opportunities, flush=True)
