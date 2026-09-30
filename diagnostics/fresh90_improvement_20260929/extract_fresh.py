"""Extract outcome-unfiltered newest tapes from the fresh download archive."""
from pathlib import Path
import gzip
import hashlib
import json
from datetime import datetime, timezone
from run_panel import ROOT, HERE, sha
from refresh_top_leaderboard_routes import _write_route

collection = ROOT / 'diagnostics/fresh90_refresh_20260929'
manifest_path = collection / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
output = HERE / 'fresh_routes'
output.mkdir(exist_ok=True)
entries = []
missing = []
for row in sorted(manifest['rows'], key=lambda r: r['rank']):
    slots = [e for e in row.get('episodes', []) if e['position'] == 1]
    if not slots:
        missing.append({'rank': row['rank'], 'reason': row.get('unavailable', 'No newest episode')})
        continue
    slot = slots[0]
    eid = int(slot['episode']['id'])
    archive = collection / 'raw_archive' / f'episode-{eid}-replay.json.gz'
    if not archive.exists():
        missing.append({'rank': row['rank'], 'reason': 'Replay not downloaded yet', 'episode_id': eid})
        continue
    raw = gzip.decompress(archive.read_bytes())
    replay = json.loads(raw)
    assert isinstance(replay, dict), f'Replay {eid} is not a JSON object'
    assert str(replay['module_version']) == '1.32.7'
    assert replay['statuses'] == ['DONE', 'DONE'] and len(replay['steps']) == 720
    entry = _write_route(output, row['team'], row['team_id'], slot['submission_id'], slot['episode'], replay)
    entry.update(rank=row['rank'], snapshot_score=row['snapshot_score'],
                 replay_path=str(archive.resolve()), replay_sha256=hashlib.sha256(raw).hexdigest(),
                 episode_end_time=slot['episode'].get('endTime'), engine_version=str(replay['module_version']),
                 leaderboard_snapshot_utc=manifest['leaderboard_snapshot_utc'])
    entries.append(entry)
for name, selected, expected in [('top20', [r for r in entries if r['rank'] <= 20], 20),
                                 ('top100', entries, 100)]:
    target = HERE / f'fresh_{name}_entries.json'
    if len(selected) == expected:
        if target.exists():
            assert json.loads(target.read_text(encoding='utf-8')) == selected
        else:
            target.write_text(json.dumps(selected, indent=2, ensure_ascii=True), encoding='utf-8')
            (HERE / f'fresh_{name}_freeze.json').write_text(json.dumps(dict(
                frozen_at_utc=datetime.now(timezone.utc).isoformat(), entries_sha256=sha(target),
                collection_manifest_sha256=sha(manifest_path), count=expected,
                distinct_episodes=len({e['episode_id'] for e in selected}),
                leaderboard_snapshot_utc=manifest['leaderboard_snapshot_utc']), indent=2), encoding='utf-8')
        print('READY', name, expected, sha(target))
print(json.dumps(dict(available=len(entries), missing=missing), indent=2))
