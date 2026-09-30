from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
from collect import collect, HERE, ROOT

if __name__ == '__main__':
    source=ROOT/'diagnostics/disjoint_upload_20260927/live_091515/episodes.json'
    listing=json.loads(source.read_text())
    chosen=[e for e in listing if 'PUBLIC' in str(e['type']) and str(e['state']).endswith('COMPLETED')]
    assert len(chosen)==29
    previous= json.loads((HERE/'cohort_0848.json').read_text())
    assert previous['complete'] and len(previous['games'])==21
    old_ids={g['episode_id'] for g in previous['games']}
    assert old_ids <= {e['id'] for e in chosen}
    for g in previous['games']:
        assert hashlib.sha256(gzip.decompress(Path(g['replay_path']).read_bytes())).hexdigest()==g['replay_sha256']
    target=HERE/'cohort_0915.json'
    assert not target.exists()
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),submission_id=56602057,
             listing=str(source.resolve()),listing_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
             selection='All 29 completed public episodes in the 09:15:19 UTC listing; no outcome filtering',
             reused_verified_episodes=21,complete=False,games=previous['games'].copy())
    def save():target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    save()
    new=[e for e in chosen if e['id'] not in old_ids]
    assert len(new)==8
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(collect,e) for e in new]):
            g=future.result();out['games'].append(g)
            out['games'].sort(key=lambda g:g['listing']['createTime']);save()
            print(f"{len(out['games'])}/29 {g['episode_id']} {g['result']} {g['margin']:+} vs {g['opponent']}",flush=True)
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat(),
               wins=sum(g['result']=='win' for g in out['games']),
               losses=sum(g['result']=='loss' for g in out['games']),draws=sum(g['result']=='draw' for g in out['games']))
    save();print(json.dumps({k:v for k,v in out.items() if k!='games'}),flush=True)
