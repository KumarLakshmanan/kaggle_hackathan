import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import copy
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from paired_benchmark import _load_module,TimedAgent,_timing_dict,make
from diagnostics.shunki_funded_purchase_20260927.native import errors

OLD=ROOT/'main_uploaded_disjoint_integrated_20260927_c68fa46f.py'
OLD_SHA='c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad'


def resources(obs,seat):
    return {'farm':{k:v for k,v in obs['farms'][seat].items() if k!='money'},'private':obs['private']}


def play(job):
    manifest,seed,seat=job
    path=Path(manifest['candidate'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest['candidate_sha256']
    assert hashlib.sha256(OLD.read_bytes()).hexdigest()==OLD_SHA
    a=_load_module(path,'weed_window_candidate');b=_load_module(OLD,'weed_window_rival')
    endpoint={}
    def call_a(obs,cfg):
        if int(obs['step'])==143:endpoint.update(copy.deepcopy(resources(obs,seat)))
        visible=dict(cfg);visible['seed']=None
        return a.agent(obs,visible)
    def call_b(obs,cfg):
        visible=dict(cfg);visible['seed']=None
        return b.agent(obs,visible)
    ta,tb=TimedAgent(call_a),TimedAgent(call_b)
    try:
        env=make('kaggriculture',configuration={'episodeSteps':720,'seed':seed},debug=False)
        env.run([ta,tb] if seat==0 else [tb,ta]);last=env.steps[-1]
        own,other=float(last[seat].reward or 0),float(last[1-seat].reward or 0)
        return dict(seed=seed,candidate_seat=seat,candidate_reward=own,opponent_reward=other,margin=own-other,
                    result='win' if own>other else 'loss' if own<other else 'draw',
                    candidate_status=last[seat].status,opponent_status=last[1-seat].status,frames=len(env.steps),
                    candidate_errors=errors(a),opponent_errors=errors(b),candidate_telemetry=dict(a.agent.telemetry),
                    candidate_timing=_timing_dict(ta),opponent_timing=_timing_dict(tb),endpoint143=endpoint,
                    configuration_seed_visible=None)
    finally:
        sys.modules.pop(a.__name__,None);sys.modules.pop(b.__name__,None)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('mechanism','pilot'));args=parser.parse_args()
    manifest=json.loads((HERE/'build_manifest.json').read_text())
    if args.phase=='pilot':
        gate=json.loads((HERE/'mechanism.json').read_text());assert gate['complete'] and gate['passed']
    seeds=[2693100,2693103] if args.phase=='mechanism' else list(range(2707000,2707008))
    target=HERE/(args.phase+'.json');assert not target.exists()
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),phase=args.phase,
             candidate_sha256=manifest['candidate_sha256'],complete=False,games=[])
    def save():target.write_text(json.dumps(out,indent=2),encoding='utf8')
    save()
    with ProcessPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(play,(manifest,seed,seat)) for seed in seeds for seat in (0,1)]):
            g=f.result();out['games'].append(g);save()
            print(f"{len(out['games'])}/{len(seeds)*2} seed={g['seed']} seat={g['candidate_seat']} {g['result']} {g['margin']:+.0f} {g['candidate_telemetry']}",flush=True)
    games=out['games'];points=sum(1 if g['result']=='win' else .5 if g['result']=='draw' else 0 for g in games)
    all_done=all(g['candidate_status']==g['opponent_status']=='DONE' and g['frames']==720 for g in games)
    error_count=sum(sum(g['candidate_errors'].values())+sum(g['opponent_errors'].values()) for g in games)
    repairs_complete=all(g['candidate_telemetry']['weed_window_started']==g['candidate_telemetry']['weed_window_completed'] for g in games)
    passed=all_done and error_count==0 and repairs_complete
    if args.phase=='mechanism':
        old=json.loads((ROOT/'diagnostics/dsm_frontloaded_bank_20260927/pilot.json').read_text())['games']
        lookup={(g['seed'],g['candidate_seat']):g for g in old}
        source_manifest=json.loads((ROOT/'diagnostics/dsm_state_matched_20260927/build_manifest.json').read_text())
        source=next(s for s in source_manifest['sources'] if s['episode_id']==114016188)
        raw=Path(source['replay_path']).read_bytes();raw=gzip.decompress(raw) if raw[:2]==b'\x1f\x8b' else raw
        assert hashlib.sha256(raw).hexdigest()==source['replay_sha256']
        replay=json.loads(raw);seat=source['source_seat'];frame=replay['steps'][143]
        expected=dict(frame[0]['observation']);expected.update(frame[seat]['observation']);expected=resources(expected,seat)
        targets=[g for g in games if g['seed']==2693103]
        endpoints=all(g['endpoint143']==expected for g in targets)
        improved=all(g['margin']>lookup[g['seed'],g['candidate_seat']]['margin'] for g in targets)
        activated=all(g['candidate_telemetry']['weed_window_started']>0 for g in targets)
        passed=passed and endpoints and improved and activated
        out.update(target_endpoint143_matches=endpoints,target_both_seat_margin_gain=improved,
                   comparisons=[dict(seed=g['seed'],seat=g['candidate_seat'],old_margin=lookup[g['seed'],g['candidate_seat']]['margin'],new_margin=g['margin']) for g in games])
    else:
        active={seed for seed in seeds if all(g['candidate_telemetry']['weed_window_started']>0
                                              for g in games if g['seed']==seed)}
        passed=passed and points>=12 and bool(active)
        out['activated_seeds']=sorted(active)
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat(),points=points,
               all_done=all_done,errors=error_count,repairs_complete=repairs_complete,passed=bool(passed))
    save();print('RESULT '+json.dumps({k:v for k,v in out.items() if k!='games'}),flush=True)
