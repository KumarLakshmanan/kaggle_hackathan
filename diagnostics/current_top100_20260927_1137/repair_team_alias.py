from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from refresh_top_leaderboard_routes import _write_route

target=HERE/'manifest.json'
raw_manifest=target.read_bytes()
manifest=json.loads(raw_manifest)
assert manifest['complete'] and manifest['eligible']==99
row=next(r for r in manifest['rows'] if r['team_id']==16735341)
assert row['team']=='MAC' and row['submission_id']==56571351 and 'error' in row
prior_path=ROOT/'diagnostics/current_top100_20260927_0730/manifest.json'
prior_raw=prior_path.read_bytes()
prior=next(r for r in json.loads(prior_raw)['rows'] if r['team_id']==row['team_id'])
assert prior['team']=='MacCook' and prior['submission_id']==row['submission_id']
listing=json.loads((HERE/f"listings/team-{row['team_id']}-submission-{row['submission_id']}-episodes.json").read_text())
choices=sorted([e for e in listing if 'PUBLIC' in str(e['type']) and str(e['state']).endswith('COMPLETED')],key=lambda e:(e['createTime'],e['id']),reverse=True)
episode=choices[0]
assert episode['id']==114137868
archive=HERE/f"raw_archive/episode-{episode['id']}-replay.json.gz"
receipt=json.loads((HERE/f"raw_archive/episode-{episode['id']}-receipt.json").read_text())
raw=gzip.decompress(archive.read_bytes())
assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
replay=json.loads(raw)
assert replay['statuses']==['DONE','DONE'] and len(replay['steps'])==720
assert replay['info']['TeamNames'].count(prior['team'])==1
route=_write_route(HERE/'routes',prior['team'],row['team_id'],row['submission_id'],episode,replay)
payload=json.loads(gzip.decompress(Path(route['path']).read_bytes()))
payload['metadata'].update(team=row['team'],source_team_name=prior['team'])
Path(route['path']).write_bytes(gzip.compress(json.dumps(payload,separators=(',',':'),ensure_ascii=False).encode('utf8')))
backup=HERE/'manifest_before_alias_fix.json'
assert not backup.exists()
backup.write_bytes(raw_manifest)
base=dict(row);base.pop('error')
route.update(base)
route.update(source_team_name=prior['team'],replay_path=str(archive.resolve()),replay_sha256=receipt['sha256'],
             downloaded_at_utc=receipt['downloaded_at_utc'],source_statuses=replay['statuses'],
             episode_end_time=episode.get('endTime'),compressed=True)
manifest['rows']=[route if r['team_id']==row['team_id'] else r for r in manifest['rows']]
eligible=[r for r in manifest['rows'] if 'action_sha256' in r]
assert len(eligible)==100
manifest.update(eligible=100,unique_episodes=len({r['episode_id'] for r in eligible}),
                identity_repaired_at_utc=datetime.now(timezone.utc).isoformat())
identity=dict(team_id=row['team_id'],submission_id=row['submission_id'],snapshot_name=row['team'],source_name=prior['team'],
              episode_id=episode['id'],old_identity_source=str(prior_path),old_identity_source_sha256=hashlib.sha256(prior_raw).hexdigest(),
              fresh_source_unchanged=True,action_sha256=route['action_sha256'],before_manifest_sha256=hashlib.sha256(raw_manifest).hexdigest())
for path,obj in ((target,manifest),(HERE/'routes/summary.json',eligible),(HERE/'identity_receipt.json',identity)):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps(identity,indent=2),flush=True)
