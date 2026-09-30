"""Repeat one selected development result to explain its physical changes."""
from pathlib import Path
import gzip
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928.fast_game import play,sha


def main():
    pool=json.loads((HERE/'pool.json').read_text(encoding='utf-8'))
    screen=json.loads((HERE/'fast_screen.json').read_text(encoding='utf-8'))
    assert screen['passed'] and screen['selected']=='route'
    candidate=next(v for v in pool['variants'] if v['version']=='route')
    fixture=next(f for f in pool['fixtures'] if f['team']=='Boey')
    prior=next(r for r in screen['games'] if r['version']=='route' and r['team']=='Boey' and r['candidate_seat']==0)
    trace=HERE/'Boey_selected_seat0.jsonl.gz';assert not trace.exists()
    row=play(fixture,candidate['candidate'],candidate['candidate_sha256'],0,trace)
    assert all(row[k]==prior[k] for k in ('candidate_reward','opponent_reward','candidate_telemetry','frames'))
    with gzip.open(trace,'rt',encoding='utf-8') as f:rows=[json.loads(l) for l in f]
    changes=[]
    for r in rows:
        step=r['step'];obs=r['observation'];action=r['action']
        # Before route commitment, its opening still comes from the incumbent.
        if step<144:continue
        # Worker schedule is immutable; market wrappers do not change worker commands.
        import importlib.util
        if 'module' not in locals():
            spec=importlib.util.spec_from_file_location('diagnostic_schedule',candidate['candidate'])
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        raw=module._DATA['routes']['113349962'][step]
        before=[raw.get('farmer',['PASS']),*raw.get('hands',[])]
        after=[action.get('farmer',['PASS']),*action.get('hands',[])]
        if before==after:continue
        details=[];positions=[obs['farms'][0]['farmer'],*obs['farms'][0]['hands']]
        for index,(old,new) in enumerate(zip(before,after)):
            if old!=new:
                details.append(dict(worker=index,position=positions[index] if index<len(positions) else None,before=old,after=new))
        next_obs=rows[step+1]['observation'] if step<718 else None
        planted=[]
        if next_obs:
            for index,unit in enumerate(after):
                if len(unit)>=2 and unit[0]=='PLANT' and index<len(positions):
                    x,y=positions[index]
                    if next_obs['farms'][0]['tiles'][y][x]!=obs['farms'][0]['tiles'][y][x]:
                        planted.append(dict(worker=index,position=[x,y],tile_after=next_obs['farms'][0]['tiles'][y][x]))
        changes.append(dict(step=step,seeds_before=obs['private']['seeds'],changed_commands=details,successful_plants=planted))
    old=ROOT/'diagnostics/route_execution_gap_20260928/Boey_seat0.jsonl.gz'
    with gzip.open(old,'rt',encoding='utf-8') as f:previous=[json.loads(l) for l in f]
    assert len(rows)==len(previous)==719
    first_shop_difference=next((s for s,(o,n) in enumerate(zip(previous,rows)) if o['observation']['town']!=n['observation']['town']),None)
    payload=dict(diagnostic_only=True,repeated_known_outcome=True,candidate_sha256=candidate['candidate_sha256'],
        trace_path=str(trace),trace_sha256=sha(trace),previous_trace_sha256=sha(old),
        changes=changes,first_shop_difference=first_shop_difference,game=row)
    (HERE/'boey_mechanism.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in payload.items() if k!='game'},indent=2))


if __name__=='__main__':main()
