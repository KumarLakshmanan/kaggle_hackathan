"""Passive replay context for interpreting the frozen assessment; no policy changes."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def farm_counts(farm):
    counts = {}
    for row in farm["tiles"]:
        for tile in row:
            if isinstance(tile, dict):
                kind = tile.get("crop") or tile.get("animal") or tile.get("kind")
                if kind:
                    counts[kind] = counts.get(kind, 0) + 1
    return counts


if __name__ == "__main__":
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf8"))
    assert manifest["complete"]
    cache = {}
    output = {"started_at_utc": datetime.now(timezone.utc).isoformat(), "complete": False, "rows": []}
    for entry in manifest["rows"]:
        eid = entry["episode_id"]
        if eid not in cache:
            raw = gzip.decompress(Path(entry["replay_path"]).read_bytes())
            assert hashlib.sha256(raw).hexdigest() == entry["replay_sha256"]
            replay = json.loads(raw)
            context = {"engine_version": replay.get("module_version"), "states": {}}
            for step in (72, 144, 288, 432, 719):
                frame = replay["steps"][step]
                obs = frame[0]["observation"]
                context["states"][str(step)] = {
                    "shops": obs["town"]["unlocked_shops"],
                    "prices": obs["market"]["prices"],
                    "farms": [{"counts": farm_counts(farm), "hands": len(farm["hands"]),
                               "land": len(farm["unlocked_quadrants"])} for farm in obs["farms"]],
                }
            cache[eid] = context
        output["rows"].append({"team": entry["team"], "team_id": entry["team_id"],
                               "rank": entry["rank"], "episode_id": eid,
                               "source_seat": entry["source_seat"], **cache[eid]})
        if len(output["rows"]) % 10 == 0:
            (HERE / "source_context.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf8")
            print(f"Source context {len(output['rows'])}/100", flush=True)
    output.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat())
    (HERE / "source_context.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf8")
