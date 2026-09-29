"""Frozen two-policy 48-game development screen; one cached worker."""
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
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

SOURCE_FULL=ROOT/'diagnostics/animal_liquidity_20260928/native_full.json'
SOURCE_FULL_SHA='51c8eab6805bd24c5907e58d845786e8c47ea4bc12e5737eb080e344938e5f8f'
PREFIX_SHA='befb989d8e8f5c393df3d9ad2a41eddff2e04a84001d36b66f60958a12d02e31'
MANIFEST=ROOT/'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
EPISODES=(114232208,114235177,114279308,114288168,114215872,114289228,114271958,114283577,114266440,114265033,114263239,114267880)


def key(row):return row['variant'],row['fixture_id'],row['candidate_seat']


def prepare():
    destination=HERE/'development_pool.json'
    assert not destination.exists()
    prefix=read(HERE/'prefix_results.json')
    assert sha(HERE/'prefix_results.json')==PREFIX_SHA
    assert prefix['complete'] and all(s['passed'] for s in prefix['summaries'])
    assert sha(SOURCE_FULL)==SOURCE_FULL_SHA
    source=read(SOURCE_FULL)
    assert source['passed'] and source['complete'] and source['clean']
    controls={(r['rival'],r['candidate_seat']):r for r in source['games']}
    original=read(HERE/'pool.json')
    assert all(sha(path)==digest for path,digest in original['bindings'].items())
    manifest=read(MANIFEST)
    fixtures=[]
    for index,episode in enumerate(EPISODES):
        panel=manifest['live_losses'] if index<8 else manifest['current_top20']
        matches=[f for f in panel if f['episode_id']==episode]
        if episode==114267880:matches=[f for f in matches if f['team']=='DECEM']
        assert len(matches)==1,(episode,len(matches))
        fixture=matches[0]
        for seat in (0,1):assert controls[fixture['fixture_id'],seat]['candidate_sha256']==original['source_sha256']
        fixtures.append(fixture)
    bindings=dict(original['bindings'])
    for path in (HERE/'pool.json',HERE/'prefix_results.json',HERE/'DEVELOPMENT_PLAN.md',Path(__file__),SOURCE_FULL,
                 ROOT/'diagnostics/physical_route_rollout_20260928/check.py',ROOT/'diagnostics/local_target_20260928/run_lock.py'):
        bindings[str(path)]=sha(path)
    for arm in original['arms'].values():
        assert sha(arm['candidate'])==arm['candidate_sha256']
        bindings[arm['candidate']]=arm['candidate_sha256']
    for fixture in fixtures:bindings[fixture['source_action_tape_path']]=sha(fixture['source_action_tape_path'])
    write(destination,dict(arms=original['arms'],fixtures=fixtures,bindings=bindings,
        controls=[controls[f['fixture_id'],seat] for f in fixtures for seat in (0,1)],
        source_full_sha256=SOURCE_FULL_SHA,prefix_sha256=PREFIX_SHA,
        created_at_utc=datetime.now(timezone.utc).isoformat()))
    print('Development pool frozen',sha(destination),len(fixtures),'fixtures',flush=True)


def worker(job):
    row=play(job['fixture'],job['candidate'],job['candidate_sha256'],job['candidate_seat'],job['trace_path'])
    control=job['control']
    row.update(variant=job['variant'],team=job['fixture']['team'],
        panel='loss30' if job['fixture']['fixture_id'].startswith('live-') else 'top20',
        source_result=control['result'],source_margin=control['margin'],
        source_own=control['candidate_reward'],source_rival=control['opponent_reward'],
        delta_own=row['candidate_reward']-control['candidate_reward'],
        delta_rival=row['opponent_reward']-control['opponent_reward'],
        delta_margin=row['margin']-control['margin'],
        trace_path=job['trace_path'],trace_sha256=sha(job['trace_path']),pool_sha256=job['pool_sha256'])
    stats=row['candidate_telemetry']
    row['procurement_failures']={k:stats[k] for k in ('bridge_common_failed','bridge_source_guard_failed') if stats.get(k,0)}
    row['clean']=(row['frames']==720 and row['candidate_status']==row['opponent_status']=='DONE'
                  and not row['candidate_errors'] and not row['procurement_failures'])
    return row


def run():
    pool=read(HERE/'development_pool.json');digest=sha(HERE/'development_pool.json')
    assert all(sha(path)==value for path,value in pool['bindings'].items())
    destination=HERE/'development_results.json';assert not destination.exists()
    controls={(r['rival'],r['candidate_seat']):r for r in pool['controls']}
    jobs=[]
    for variant,arm in pool['arms'].items():
        for fixture in pool['fixtures']:
            for seat in (0,1):
                jobs.append(dict(variant=variant,fixture_id=fixture['fixture_id'],fixture=fixture,
                    candidate=arm['candidate'],candidate_sha256=arm['candidate_sha256'],candidate_seat=seat,
                    control=controls[fixture['fixture_id'],seat],pool_sha256=digest,
                    trace_path=str(HERE/('development_'+variant+'_'+str(fixture['episode_id'])+'_seat'+str(seat)+'.jsonl.gz'))))
    expected={key(j):j for j in jobs}
    checkpoint=HERE/'development_results.jsonl'
    rows=[json.loads(line) for line in checkpoint.read_text().splitlines()] if checkpoint.exists() else []
    done={key(r) for r in rows};assert len(done)==len(rows)
    for row in rows:
        assert row['pool_sha256']==digest and row['candidate_sha256']==expected[key(row)]['candidate_sha256']
        assert sha(row['trace_path'])==row['trace_sha256']
    pending=[job for job in jobs if key(job) not in done]
    with checkpoint.open('a',encoding='utf-8') as stream:
        for start in range(0,len(pending),8):
            with ProcessPoolExecutor(max_workers=1) as executor:
                for row in executor.map(worker,pending[start:start+8]):
                    rows.append(row);stream.write(json.dumps(row)+'\n');stream.flush()
                    print('Bridge development',len(rows),'/48',row['variant'],row['team'],row['candidate_seat'],
                          row['result'],row['margin'],'delta',row['delta_margin'],'branch',
                          row['candidate_telemetry'].get('bridge_selected'),flush=True)
    summaries=[]
    for variant in pool['arms']:
        games=[r for r in rows if r['variant']==variant]
        groups={f['fixture_id']:[r for r in games if r['fixture_id']==f['fixture_id']] for f in pool['fixtures']}
        assert all(len(pair)==2 for pair in groups.values())
        regressions=[dict(fixture_id=r['fixture_id'],seat=r['candidate_seat'],margin=r['margin']) for r in games if r['source_result']=='win' and r['result']!='win']
        rescued=[fid for fid,pair in groups.items() if all(r['result']=='win' for r in pair) and any(r['source_result']!='win' for r in pair)]
        clean=all(r['clean'] for r in games)
        summaries.append(dict(variant=variant,candidate_sha256=pool['arms'][variant]['candidate_sha256'],
            complete=len(games)==24,clean=clean,regressions=regressions,rescued=rescued,
            public_rescues=[f for f in rescued if f.startswith('live-')],top_rescues=[f for f in rescued if not f.startswith('live-')],
            WDL=[sum(r['result']==label for r in games) for label in ('win','draw','loss')],
            both_seat_wins=sum(all(r['result']=='win' for r in pair) for pair in groups.values()),
            guard_refusals=sum(r['candidate_telemetry'].get('bridge_guard_refusals',0) for r in games),
            mean_delta_margin=sum(r['delta_margin'] for r in games)/len(games),
            passed=len(games)==24 and clean and not regressions and bool(rescued)))
    result=dict(complete=len(rows)==48,diagnostic_only=True,summaries=summaries,games=sorted(rows,key=key),
                pool_sha256=digest,helper_sha256=sha(__file__),completed_at_utc=datetime.now(timezone.utc).isoformat())
    write(destination,result)
    print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('prepare','run'));args=parser.parse_args()
    with exclusive_run(HERE/'development.lock'):
        prepare() if args.phase=='prepare' else run()
