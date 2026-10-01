"""Inventory all locally present replay bodies; extract both players' tapes.

No replay observations, seeds or outcomes are made available to the agent.
Seeds are evaluation configuration only. Exact action/seed duplicates run once.
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".bench_deps"))
import pyarrow.parquet as pq
import simdjson

OUT = ROOT / "analysis_artifacts" / "dhana_strength"
ROUTES = OUT / "routes"


def main():
    ROUTES.mkdir(parents=True, exist_ok=True)
    rows, skipped, sources = {}, [], []
    seen_episodes = set()
    parser = simdjson.Parser()

    def compact_replay(raw):
        value = parser.parse(raw)
        if not isinstance(value, simdjson.Object) or "steps" not in value:
            return {}
        return {"info": value["info"].as_dict(), "module_version": value.get("module_version"),
                "steps": [[{"action": frame[seat]["action"].as_dict() if isinstance(frame[seat].get("action"), simdjson.Object) else None}
                           for seat in (0, 1)] for frame in value["steps"]]}

    def route(actions, metadata, source):
        if len(actions) != 719 or metadata.get("seed") is None:
            skipped.append({"source": source, "reason": "missing seed or incomplete episode",
                            "actions": len(actions)})
            return
        data = json.dumps(actions, sort_keys=True, separators=(",", ":")).encode()
        digest = hashlib.sha256(data).hexdigest()
        key = (digest, int(metadata["seed"]))
        if key in rows:
            rows[key]["sources"].append(source)
            return
        target = ROUTES / f"{digest[:20]}-{metadata['seed']}.json.gz"
        payload = {"actions": actions, "metadata": metadata}
        with gzip.open(target, "wt", encoding="utf-8") as handle:
            json.dump(payload, handle, separators=(",", ":"))
        rows[key] = {**metadata, "action_sha256": digest, "path": str(target), "sources": [source]}

    def replay(value, source):
        if not isinstance(value, dict):
            return
        steps = value.get("steps")
        if not isinstance(steps, list):
            return
        info = value.get("info") or {}
        episode = info.get("EpisodeId") or source
        if episode in seen_episodes:
            sources.append({"source": source, "episode": episode, "duplicate": True})
            return
        seen_episodes.add(episode)
        sources.append({"source": source, "episode": episode})
        names = info.get("TeamNames") or ["seat0", "seat1"]
        for seat in (0, 1):
            actions = [f[seat].get("action") or {"farmer": ["PASS"], "hands": [], "market": []}
                       for f in steps[1:]]
            route(actions, {"seed": info.get("seed"), "episode_id": episode,
                            "source_seat": seat, "team": names[seat],
                            "recorded_engine": value.get("module_version")}, source)

    for folder in ("best_replay", "failed_replay", "dhana/fail", "live_routes"):
        for path in sorted((ROOT / folder).rglob("*.json")):
            if path.stat().st_size < 100_000:
                continue
            try:
                replay(compact_replay(path.read_bytes()), str(path.relative_to(ROOT)))
            except (ValueError, KeyError, IndexError) as exc:
                skipped.append({"source": str(path), "reason": str(exc)})
        for path in sorted((ROOT / folder).rglob("*.json.gz")):
            try:
                with gzip.open(path, "rt", encoding="utf-8") as handle:
                    value = json.load(handle)
                route(value["actions"], value.get("metadata") or {}, str(path.relative_to(ROOT)))
            except (ValueError, KeyError) as exc:
                skipped.append({"source": str(path), "reason": str(exc)})
    print("JSON", len(rows), "routes", flush=True)
    (OUT / "json_manifest.json").write_text(json.dumps({"routes": list(rows.values())}), encoding="utf-8")
    if "--json-only" in sys.argv:
        return
    # Resume completed cached episodes. Both seats must be present before a
    # Parquet replay can be skipped; a partially written gzip is regenerated.
    cached_episodes = {}
    for path in sorted(ROUTES.glob("*.json.gz")):
        try:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                value = json.load(handle)
            meta = value["metadata"]
            episode = meta.get("episode_id")
            if episode is not None and "recorded_engine" in meta:
                cached_episodes.setdefault(episode, set()).add(meta["source_seat"])
                route(value["actions"], meta, "cached:" + path.name)
        except (ValueError, KeyError, OSError, EOFError):
            continue
    seen_episodes.update(k for k, seats in cached_episodes.items() if len(seats) == 2)
    for path in sorted((ROOT / "current_top10_replays_2026-09-21").glob("replays_*.parquet")):
        parquet = pq.ParquetFile(path)
        print("SHARD", path.name, parquet.metadata.num_rows, flush=True)
        for index, batch in enumerate(parquet.iter_batches(batch_size=1, columns=["episode_id", "replay_json"])):
            record = batch.to_pylist()[0]
            source = f"{path.name}#{record['episode_id']}"
            if record["episode_id"] in seen_episodes:
                sources.append({"source": source, "episode": record["episode_id"], "duplicate": True})
                continue
            try:
                replay(compact_replay(record["replay_json"]), source)
            except (ValueError, KeyError, IndexError) as exc:
                skipped.append({"source": source, "reason": str(exc)})
            if index % 100 == 0:
                print("PROGRESS", path.name, index, "routes", len(rows), flush=True)
    result = {"episodes": len(seen_episodes), "route_count": len(rows), "sources": sources,
              "skipped": skipped, "routes": sorted(rows.values(), key=lambda r: (r["action_sha256"], r["seed"]))}
    (OUT / "manifest.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("COMPLETE", len(seen_episodes), len(rows), "skipped", len(skipped), flush=True)


if __name__ == "__main__":
    main()
