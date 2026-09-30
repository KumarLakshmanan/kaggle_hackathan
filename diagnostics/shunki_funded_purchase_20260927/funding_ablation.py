"""Prospectively recruit native funding cases without observing game outcomes."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from diagnostics.shunki_planned_funding_20260927.native import play, point, errors, RIVALS
from paired_benchmark import _load_module, make

CONTROL=ROOT/'main_candidate_purchase_queue_20260927_43d6f448.py'
CONTROL_HASH='43d6f44806f7ce7204aa92180584f96c894653d6cb36bb9442a0425e8fbef176'
REFERENCE_ORDER=('c68','1f','489','C95')


class PrefixComplete(Exception):
    pass


def recruit(job):
    path,digest,seed,reference,reference_digest=job
    assert hashlib.sha256(CONTROL.read_bytes()).hexdigest()==CONTROL_HASH
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    assert hashlib.sha256(RIVALS[reference].read_bytes()).hexdigest()==reference_digest
    control=_load_module(CONTROL,'funding_prefix_control')
    rival=_load_module(RIVALS[reference],'funding_prefix_rival')
    probe=_load_module(Path(path),'funding_prefix_probe')
    context={'step':None,'eligible':False}
    started=time.perf_counter()

    def control_call(obs,cfg):
        visible=dict(cfg);visible['seed']=None
        action=control.agent(obs,visible)
        context['step']=int(obs['step'])
        proposal=probe._planned_funding_apply(obs,copy.deepcopy(action),visible)
        if proposal.get('market')!=action.get('market'):
            context.update(eligible=True,observation=copy.deepcopy(dict(obs)),
                           original_action=copy.deepcopy(action),proposed_action=copy.deepcopy(proposal),
                           configuration=visible)
        return action

    def rival_call(obs,cfg):
        visible=dict(cfg);visible['seed']=None
        return rival.agent(obs,visible)

    env=make('kaggriculture',configuration={'episodeSteps':720,'seed':seed},debug=False)
    original_step=env.step

    def bounded_step(actions,logs=None):
        # Stop outside agent execution, before a proposed change or turn 288
        # is settled. Native configuration and every prior transition stay
        # unchanged. No terminal result is generated or consulted.
        if context['eligible'] or (context['step'] is not None and context['step']>=288):
            raise PrefixComplete
        return original_step(actions,logs)

    try:
        env.step=bounded_step
        stopped=False
        try:
            env.run([control_call,rival_call])
        except PrefixComplete:
            stopped=True
        row=dict(seed=seed,reference=reference,control_seat=0,eligible=context['eligible'],
                 prefix_observation_step=context['step'],prefix_frames=len(env.steps),
                 stopped_before_settlement=stopped,terminal_outcome_observed=False,
                 engine_episode_steps=720,configuration_seed_visible=None,
                 control_errors=errors(control),rival_errors=errors(rival),
                 wall_seconds=time.perf_counter()-started)
        assert stopped and not env.done,'Unexpected terminal prefix; inspect before selection'
        assert not row['control_errors'] and not row['rival_errors']
        if row['eligible']:
            evidence=dict(row,observation=context['observation'],original_action=context['original_action'],
                          proposed_action=context['proposed_action'],configuration=context['configuration'])
            raw=json.dumps(evidence,separators=(',',':'),ensure_ascii=False).encode('utf8')
            target=HERE/'eligibility'/f"seed-{seed}-{reference}.json.gz"
            target.write_bytes(gzip.compress(raw))
            row.update(evidence_path=str(target.resolve()),evidence_sha256=hashlib.sha256(raw).hexdigest())
        return row
    finally:
        env.step=original_step
        for m in (control,rival,probe):sys.modules.pop(m.__name__,None)


if __name__=='__main__':
    manifest=json.loads((HERE/'build_manifest.json').read_text())
    gate=json.loads((HERE/'confirmation.json').read_text())
    assert gate['complete'] and gate['passed'] and gate['candidate_sha256']==manifest['candidate_sha256']
    target=HERE/'funding_ablation.json';assert not target.exists()
    (HERE/'eligibility').mkdir(exist_ok=True)
    hashes={k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in RIVALS.items()}
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),candidate_sha256=manifest['candidate_sha256'],
             purchase_control_sha256=CONTROL_HASH,reference_hashes=hashes,
             selection='First 16 eligible seed/reference prefixes, seed-major and c68,1f,489,C95 order; control seat 0',
             seed_range=[2705000,2705319],complete=False,prefixes=[],selected=[],games=[])
    def save():target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    save()
    # At most one four-reference seed batch runs ahead. Rows are admitted in
    # the frozen reference order, never completion order or outcome order.
    with ProcessPoolExecutor(max_workers=4) as pool:
        for seed in range(2705000,2705320):
            jobs=[(manifest['candidate'],manifest['candidate_sha256'],seed,r,hashes[r]) for r in REFERENCE_ORDER]
            futures=[pool.submit(recruit,j) for j in jobs]
            rows=[f.result() for f in futures]
            for row in rows:
                out['prefixes'].append(row)
                if row['eligible'] and len(out['selected'])<16:
                    out['selected'].append(row)
            save()
            print(f"PREFIX seed={seed} inspected={len(out['prefixes'])} selected={len(out['selected'])}/16",flush=True)
            if len(out['selected'])==16:break
    counts={r:sum(g['reference']==r for g in out['selected']) for r in REFERENCE_ORDER}
    coverage=len(out['selected'])==16 and sum(n>=4 for n in counts.values())>=2
    out['eligibility_reference_counts']=counts
    if not coverage:
        out.update(complete=True,passed=False,reason='Frozen eligibility recruitment/coverage requirement failed',
                   completed_at_utc=datetime.now(timezone.utc).isoformat())
        save();print('REJECT '+json.dumps(counts),flush=True);raise SystemExit(0)
    versions={'purchase':(str(CONTROL),CONTROL_HASH),'combined':(manifest['candidate'],manifest['candidate_sha256'])}
    jobs=[(p,h,v,c['reference'],hashes[c['reference']],c['seed'],seat)
          for c in out['selected'] for v,(p,h) in versions.items() for seat in (0,1)]
    assert len(jobs)==64
    with ProcessPoolExecutor(max_workers=4) as pool:
        for f in as_completed([pool.submit(play,j) for j in jobs]):
            g=f.result();out['games'].append(g);save()
            print(f"{len(out['games'])}/64 {g['version']} vs {g['rival']} seed={g['seed']} "
                  f"seat={g['candidate_seat']} {g['result']} {g['margin']:+.0f}",flush=True)
    games=out['games']
    scores={r:{v:sum(point(g) for g in games if g['rival']==r and g['version']==v) for v in versions} for r in REFERENCE_ORDER}
    active={(g['seed'],g['rival']) for g in games if g['version']=='combined' and g['candidate_telemetry'].get('planned_funding_turns',0)>0}
    selected={(r['seed'],r['reference']) for r in out['selected']}
    all_done=all(g['candidate_status']==g['opponent_status']=='DONE' and g['frames']==720 for g in games)
    error_count=sum(sum(g['candidate_errors'].values())+sum(g['opponent_errors'].values()) for g in games)
    nonregression=all(s['combined']>=s['purchase'] for s in scores.values())
    gain=sum(s['combined']-s['purchase'] for s in scores.values())
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat(),scores=scores,
               activated_pairs=[list(x) for x in sorted(active)],all_done=all_done,errors=error_count,
               reference_nonregression=nonregression,pooled_win_point_gain=gain,
               passed=active==selected and all_done and error_count==0 and nonregression and gain>0)
    save();print('RESULT '+json.dumps({k:out[k] for k in ('scores','activated_pairs','all_done','errors','pooled_win_point_gain','passed')}),flush=True)
