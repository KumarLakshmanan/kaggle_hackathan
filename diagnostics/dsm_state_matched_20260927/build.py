"""Build an outcome-blind, exact-state schedule bank from complete public sources."""
from datetime import datetime, timezone
import base64
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
STEPS = tuple(range(72, 719, 72))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def signature(farm, private):
    physical = {k: v for k, v in farm.items() if k != "money"}
    return hashlib.sha256(canonical([physical, private]).encode()).hexdigest()


def key(step, shops, digest):
    return canonical([step, shops, digest])


if __name__ == "__main__":
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf8"))
    assert manifest["complete"] and manifest["eligible"] == 121
    fresh = json.loads((ROOT / "diagnostics/current_top100_20260927_0730/manifest.json").read_text(encoding="utf8"))
    sources = {r["episode_id"]: r for r in manifest["rows"] if "action_sha256" in r}
    for row in fresh["rows"]:
        if row.get("submission_id") == 56582621:
            sources[row["episode_id"]] = row
    sources = sorted(sources.values(), key=lambda r: (r["create_time"], r["episode_id"]), reverse=True)
    assert len(sources) == 122
    tapes, index, audits = [], {}, []
    endpoints = Counter()
    first_shops, second_shops = Counter(), Counter()
    for number, source in enumerate(sources):
        path = Path(source["replay_path"])
        raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == source["replay_sha256"]
        replay = json.loads(raw)
        assert replay["statuses"] == ["DONE", "DONE"] and len(replay["steps"]) == 720
        seat = source["source_seat"]
        actions = [frame[seat]["action"] for frame in replay["steps"][1:]]
        assert hashlib.sha256(canonical(actions).encode()).hexdigest() == source["action_sha256"]
        tapes.append(actions)
        audit = {"episode_id": source["episode_id"], "source_seat": seat, "boundaries": []}
        for step in STEPS:
            frame = replay["steps"][step]
            observation = dict(frame[0]["observation"])
            observation.update(frame[seat]["observation"])
            farm = observation["farms"][seat]
            digest = signature(farm, observation["private"])
            shops = observation["town"]["unlocked_shops"]
            lookup = key(step, shops, digest)
            index.setdefault(lookup, number)
            audit["boundaries"].append({"step": step, "shops": shops, "state_hash": digest,
                                        "source_money": farm["money"]})
            if step == 72:
                endpoints[digest] += 1
                first_shops[tuple(shops)] += 1
            if step == 144:
                second_shops[tuple(shops)] += 1
        audits.append(audit)
        if (number + 1) % 20 == 0:
            print(f"Indexed {number+1}/{len(sources)} sources", flush=True)
    payload = {"tapes": tapes, "index": index, "episode_ids": [r["episode_id"] for r in sources]}
    encoded = base64.b64encode(zlib.compress(canonical(payload).encode(), level=9)).decode()
    template = (HERE / "runtime.py.txt").read_text(encoding="utf8")
    candidate = ROOT / "exp_dsm_state_matched_20260927.py"
    assert not candidate.exists(), "Preserve previous candidate; inspect before rebuilding"
    candidate.write_text(template.replace("__PACKED_DATA__", encoded), encoding="utf8")
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    backup = ROOT / f"main_candidate_dsm_state_matched_20260927_{digest[:8]}.py"
    assert not backup.exists()
    backup.write_bytes(candidate.read_bytes())
    report = {"built_at_utc": datetime.now(timezone.utc).isoformat(), "candidate": str(candidate),
              "candidate_sha256": digest, "backup": str(backup), "candidate_bytes": candidate.stat().st_size,
              "source_count": len(sources), "sources": sources, "default_episode_id": sources[0]["episode_id"],
              "index_keys": len(index), "boundary_keys": dict(Counter(json.loads(k)[0] for k in index)),
              "unique_turn72_full_states": len(endpoints), "turn72_state_counts": dict(endpoints),
              "first_shop_coverage": [{"shops": list(k), "count": v} for k, v in sorted(first_shops.items())],
              "first_two_shop_coverage": [{"shops": list(k), "count": v} for k, v in sorted(second_shops.items())]}
    (HERE / "build_manifest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf8")
    (HERE / "source_boundary_audit.json").write_text(json.dumps(audits, indent=2), encoding="utf8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("sources", "first_two_shop_coverage", "turn72_state_counts")}, indent=2), flush=True)
