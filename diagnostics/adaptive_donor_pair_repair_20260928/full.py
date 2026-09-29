"""Exact full50 development; verified reuse24 plus76 new cached games."""
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import argparse
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.adaptive_opening_bridge_20260928.build import read,write,sha
from diagnostics.stream_replay_io_20260928.fast_game_cached import play
from diagnostics.local_target_20260928.run_lock import exclusive_run

MANIFEST=ROOT/'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
MANIFEST_SHA='524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
CONTROL=ROOT/'diagnostics/animal_liquidity_20260928/native_full.json'
CONTROL_SHA='51c8eab6805bd24c5907e58d845786e8c47ea4bc12e5737eb080e344938e5f8f'
CANDIDATE_SHA='a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f'
COMBINED_SHA='82953029de1373927b43ffb766dbdaf02b18990d71e534a4a78705c78af517a3'
BACKUP=ROOT/'main_candidate_adaptive_donor_pair_repair_20260928_a44c8c2c.py'


def key(row):return row['fixture_id'],row['candidate_seat']


def decorate(row,control,ceed):
    stats=row['candidate_telemetry']
    row.update(source32e_result=control['result'],source32e_margin=control['margin'],
        delta_own_vs32e=row['candidate_reward']-control['candidate_reward'],
        delta_rival_vs32e=row['opponent_reward']-control['opponent_reward'],
        delta_margin_vs32e=row['margin']-control['margin'],
        known_ceed_result=ceed['result'] if ceed else None,known_ceed_margin=ceed['margin'] if ceed else None)
    row['clean']=(row['frames']==720 and row['candidate_status']==row['opponent_status']=='DONE' and not row['candidate_errors']
                  and not stats.get('bridge_common_failed',0) and not stats.get('bridge_source_guard_failed',0))
    return row


def prepare():
    assert sha(MANIFEST)==MANIFEST_SHA and sha(CONTROL)==CONTROL_SHA
    assert sha(HERE/'combined_results.json')==COMBINED_SHA and sha(HERE/'candidate_combined.py')==CANDIDATE_SHA
    original=read(HERE/'pool.json');combined=read(HERE/'combined_results.json');control=read(CONTROL)
    assert all(sha(path)==digest for path,digest in original['bindings'].items())
    assert combined['complete'] and combined['passed'] and control['complete'] and control['passed']
    assert len(combined['games'])==24 and len(control['games'])==100
    controls={(r['rival'],r['candidate_seat']):r for r in control['games']}
    ceed={key(r):r for r in original['controls']}
    manifest=read(MANIFEST);fixtures=manifest['current_top20']+manifest['live_losses']
    byid={f['fixture_id']:f for f in fixtures};assert len(byid)==50
    old_byid={f['fixture_id']:f for f in original['fixtures']}
    bindings=dict(original['bindings'])
    for row in combined['games']:
        fid,seat=key(row);assert byid[fid]==old_byid[fid]
        assert row['candidate_sha256']==CANDIDATE_SHA and sha(row['trace_path'])==row['trace_sha256']
        assert row['source_result']==controls[fid,seat]['result'] and row['source_margin']==controls[fid,seat]['margin']
        bindings[row['trace_path']]=row['trace_sha256']
    if BACKUP.exists():assert sha(BACKUP)==CANDIDATE_SHA
    else:
        with BACKUP.open('xb') as stream:stream.write((HERE/'candidate_combined.py').read_bytes())
    assert sha(BACKUP)==CANDIDATE_SHA
    for path in (HERE/'FULL_PLAN.md',Path(__file__),HERE/'pool.json',HERE/'combined_results.json',HERE/'combined_binding.json',
                 HERE/'screen.json',HERE/'prefix_results.json',HERE/'candidate_combined.py',BACKUP,MANIFEST,CONTROL):
        bindings[str(path)]=sha(path)
    for fixture in fixtures:bindings[fixture['source_action_tape_path']]=sha(fixture['source_action_tape_path'])
    write(HERE/'full_pool.json',dict(candidate=str(BACKUP),candidate_sha256=CANDIDATE_SHA,fixtures=fixtures,
        controls=list(control['games']),known_ceed_controls=list(ceed.values()),bindings=bindings,
        reused_games=combined['games'],combined_receipt_sha256=COMBINED_SHA,
        created_at_utc=datetime.now(timezone.utc).isoformat()))
    print('Full50 prepared; reuse24/new76; pool',sha(HERE/'full_pool.json'),'backup',str(BACKUP),flush=True)


def worker(job):
    row=play(job['fixture'],job['candidate'],job['candidate_sha256'],job['candidate_seat'],job['trace_path'])
    decorate(row,job['control'],job['ceed'])
    row.update(team=job['fixture']['team'],panel=job['panel'],trace_path=job['trace_path'],trace_sha256=sha(job['trace_path']),
               reused=False,pool_sha256=job['pool_sha256'])
    return row


def run():
    pool=read(HERE/'full_pool.json');digest=sha(HERE/'full_pool.json')
    assert all(sha(path)==value for path,value in pool['bindings'].items())
    controls={(r['rival'],r['candidate_seat']):r for r in pool['controls']}
    ceed={key(r):r for r in pool['known_ceed_controls']};fixtures={f['fixture_id']:f for f in pool['fixtures']}
    destination=HERE/'full_results.json';assert not destination.exists()
    checkpoint=HERE/'full_results.jsonl'
    if checkpoint.exists():rows=[json.loads(line) for line in checkpoint.read_text().splitlines()]
    else:
        rows=[]
        for raw in pool['reused_games']:
            row=dict(raw);decorate(row,controls[key(row)],ceed.get(key(row)))
            row.update(team=fixtures[row['fixture_id']]['team'],panel='loss30' if row['fixture_id'].startswith('live-') else 'top20',
                       reused=True,reused_receipt=str(HERE/'combined_results.json'),reused_receipt_sha256=COMBINED_SHA,pool_sha256=digest)
            rows.append(row)
        with checkpoint.open('x',encoding='utf-8') as stream:
            for row in rows:stream.write(json.dumps(row)+'\n')
    done={key(r) for r in rows};assert len(done)==len(rows)
    for row in rows:
        assert row['candidate_sha256']==CANDIDATE_SHA and row['pool_sha256']==digest and sha(row['trace_path'])==row['trace_sha256']
    jobs=[]
    for fixture in pool['fixtures']:
        for seat in (0,1):
            fid=fixture['fixture_id']
            if (fid,seat) in done:continue
            jobs.append(dict(candidate=pool['candidate'],candidate_sha256=CANDIDATE_SHA,fixture=fixture,candidate_seat=seat,
                control=controls[fid,seat],ceed=ceed.get((fid,seat)),panel='loss30' if fid.startswith('live-') else 'top20',pool_sha256=digest,
                trace_path=str(HERE/('full_'+fid.replace(' ','_')+'_seat'+str(seat)+'.jsonl.gz'))))
    with checkpoint.open('a',encoding='utf-8') as stream:
        for start in range(0,len(jobs),8):
            with ProcessPoolExecutor(max_workers=1) as executor:
                for row in executor.map(worker,jobs[start:start+8]):
                    rows.append(row);stream.write(json.dumps(row)+'\n');stream.flush()
                    print('Pair repair full',len(rows),'/100',row['panel'],row['team'],row['candidate_seat'],row['result'],row['margin'],flush=True)
    regressions32=[list(key(r)) for r in rows if r['source32e_result']=='win' and r['result']!='win']
    regressions_ceed=[list(key(r)) for r in rows if r['known_ceed_result']=='win' and r['result']!='win']
    panels=[]
    for panel in ('top20','loss30'):
        games=[r for r in rows if r['panel']==panel];ids=sorted({r['fixture_id'] for r in games})
        groups={fid:[r for r in games if r['fixture_id']==fid] for fid in ids};assert all(len(p)==2 for p in groups.values())
        panels.append(dict(panel=panel,fixtures=len(ids),WDL=[sum(r['result']==label for r in games) for label in ('win','draw','loss')],
            both_seat_wins=sum(all(r['result']=='win' for r in pair) for pair in groups.values()),
            new_rescues=[fid for fid,pair in groups.items() if all(r['result']=='win' for r in pair) and any(r['source32e_result']!='win' for r in pair)],
            mean_delta_margin_vs32e=sum(r['delta_margin_vs32e'] for r in games)/len(games)))
    count={p['panel']:p['both_seat_wins'] for p in panels};clean=all(r['clean'] for r in rows)
    result=dict(complete=len(rows)==100,clean=clean,passed=len(rows)==100 and clean and not regressions32 and not regressions_ceed
                and count['top20']>=19 and count['loss30']>14,
        regressions_vs32e=regressions32,regressions_vs_known_ceed=regressions_ceed,panels=panels,games=rows,
        reused_games=sum(bool(r['reused']) for r in rows),new_games=sum(not r['reused'] for r in rows),
        candidate_sha256=CANDIDATE_SHA,pool_sha256=digest,helper_sha256=sha(__file__),
        completed_at_utc=datetime.now(timezone.utc).isoformat())
    write(destination,result)
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('prepare','run'));args=parser.parse_args()
    with exclusive_run(HERE/'full.lock'):prepare() if args.phase=='prepare' else run()
