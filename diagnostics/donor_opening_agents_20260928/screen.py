"""One-worker development and complete target gates for whole donor policies."""
from datetime import datetime,timezone
from pathlib import Path
import argparse
import json
import sys

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
from build import sha,read,write,MANIFEST,FULL,SOURCE,SOURCE_SHA
from diagnostics.physical_route_rollout_20260928.fast_game import play
from diagnostics.local_target_20260928.run_lock import exclusive_run


def key(r):return r['version'],r['fixture_id'],r['candidate_seat']


def run(phase):
    pool=read(HERE/'pool.json');assert sha(SOURCE)==SOURCE_SHA
    assert sha(MANIFEST)==pool['manifest_sha256'] and sha(FULL)==pool['native_source_full_sha256']
    assert sha(HERE/'PLAN.md')==pool['plan_sha256'] and sha(HERE/'build.py')==pool['build_helper_sha256']
    assert sha(HERE/'extracted_helpers.py')==pool['extracted_helpers_sha256']
    assert all(sha(a['candidate'])==a['candidate_sha256'] for a in pool['arms'].values())
    output=HERE/(phase+'.json');assert not output.exists()
    ledger=HERE/(phase+'.jsonl');pool_digest=sha(HERE/'pool.json');helper_digest=sha(__file__)
    source={(r['rival'],r['candidate_seat']):r for r in read(FULL)['games'] if r['version']=='integrated'}
    if phase=='pilot':
        arms=pool['arms'];fixtures=pool['fixtures'];seed_rows=[]
    else:
        pilot=read(HERE/'pilot.json');assert pilot['complete'] and pilot['pool_sha256']==pool_digest and pilot['helper_sha256']==helper_digest
        survivors=[s['version'] for s in pilot['summaries'] if s['passed']];assert survivors
        arms={v:pool['arms'][v] for v in survivors}
        m=read(MANIFEST);fixtures=m['live_losses']+m['current_top20'];seed_rows=[r for r in pilot['games'] if r['version'] in arms]
    jobs=[(v,a,f,seat) for v,a in arms.items() for f in fixtures for seat in (0,1)]
    rows=[json.loads(l) for l in ledger.read_text().splitlines()] if ledger.exists() else list(seed_rows)
    if not ledger.exists():ledger.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    done={key(r) for r in rows};assert len(done)==len(rows)
    assert all(r['candidate_sha256']==arms[r['version']]['candidate_sha256'] for r in rows)
    with ledger.open('a',encoding='utf-8') as out:
        for version,arm,fixture,seat in jobs:
            if (version,fixture['fixture_id'],seat) in done:continue
            trace=HERE/(phase+'_'+version+'_'+fixture['fixture_id']+'_seat'+str(seat)+'.jsonl.gz')
            row=play(fixture,arm['candidate'],arm['candidate_sha256'],seat,trace)
            old=source[(fixture['fixture_id'],seat)]
            row.update(version=version,team=fixture['team'],panel='loss30' if fixture['fixture_id'].startswith('live-') else 'top20',
                       parent_result=old['result'],parent_margin=old['margin'],parent_own=old['candidate_reward'],parent_rival=old['opponent_reward'],
                       delta_own=row['candidate_reward']-old['candidate_reward'],delta_rival=row['opponent_reward']-old['opponent_reward'],
                       delta_margin=row['margin']-old['margin'],trace_path=str(trace),trace_sha256=sha(trace))
            rows.append(row);done.add(key(row));out.write(json.dumps(row)+'\n');out.flush()
            print(phase,len(rows),'/',len(jobs),version,fixture['team'],seat,row['result'],row['margin'],flush=True)
    summaries=[]
    for version in arms:
        games=[r for r in rows if r['version']==version]
        clean=all(r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' and not r['candidate_errors'] for r in games)
        ids=sorted({r['fixture_id'] for r in games});pairs={fid:[r for r in games if r['fixture_id']==fid] for fid in ids}
        assert all(len(pair)==2 for pair in pairs.values())
        rescues=[fid for fid,pair in pairs.items() if fid.startswith('live-') and all(r['result']=='win' for r in pair) and any(r['parent_result']!='win' for r in pair)]
        lost_top=[fid for fid,pair in pairs.items() if fid.startswith('top20-') and all(r['parent_result']=='win' for r in pair) and any(r['result']!='win' for r in pair)]
        lost_seats=[dict(fixture_id=r['fixture_id'],seat=r['candidate_seat'],parent_margin=r['parent_margin'],margin=r['margin']) for r in games if r['parent_result']=='win' and r['result']!='win']
        counts={panel:sum(all(r['result']=='win' for r in pair) for fid,pair in pairs.items() if pair[0]['panel']==panel) for panel in ('loss30','top20')}
        passed=clean and bool(rescues) and len(lost_top)<=2 if phase=='pilot' else clean and counts['top20']>=18 and counts['loss30']>=14
        summaries.append(dict(version=version,passed=passed,clean=clean,both_seat_wins=counts,new_public_rescues=rescues,lost_top_fixtures=lost_top,lost_source_winning_seats=lost_seats))
    result=dict(complete=len(rows)==len(jobs),phase=phase,diagnostic_only=True,pool_sha256=pool_digest,helper_sha256=helper_digest,
                source_sha256=SOURCE_SHA,summaries=summaries,games=rows,completed_at_utc=datetime.now(timezone.utc).isoformat())
    write(output,result);print(json.dumps({k:v for k,v in result.items() if k!='games'},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('pilot','full'));args=parser.parse_args()
    with exclusive_run(HERE/'screen.lock'):run(args.phase)
