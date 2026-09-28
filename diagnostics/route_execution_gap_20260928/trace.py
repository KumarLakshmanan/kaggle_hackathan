from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928.fast_game import play,sha
from diagnostics.bakery_pizza_pool_20260928.analyze_mhw import analyze
from diagnostics.local_target_20260928.run_lock import exclusive_run


def main():
    source=ROOT/'diagnostics/compatible_route_pool_20260928'
    pool=json.loads((source/'pool.json').read_text(encoding='utf-8'))
    screen=json.loads((source/'corrected_screen.json').read_text(encoding='utf-8'))
    assert sha(source/'corrected_screen.json')=='28ca6b2c42b71e51ba664da34b49d4d380297acb7f6f05ae0dae093a46fe9dd7'
    manifest_path=ROOT/'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
    assert sha(manifest_path)=='524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
    fixtures=json.loads(manifest_path.read_text(encoding='utf-8'))['current_top20']
    assert screen['complete'] and screen['all_done'] and screen['no_errors']
    assert sha(ROOT/'main.py')==pool['source_sha256']
    rows=[];analyses=[]
    for team,group,route in [('DECEM','A','113373693'),('Boey','B','113349962'),('Kaggledew','B','113349962')]:
        fixture=next(f for f in fixtures if f['team'].startswith(team))
        candidate=next(v for v in pool['variants'] if v['group']==group and v['route']==route)
        for seat in (0,1):
            output=HERE/f'{team}_seat{seat}.jsonl.gz'
            receipt=output.with_name(output.name+'.receipt.json')
            if output.exists() and not receipt.exists():
                output=HERE/f'{team}_seat{seat}_recovered.jsonl.gz'
                receipt=output.with_name(output.name+'.receipt.json')
            if output.exists():
                row=json.loads(receipt.read_text(encoding='utf-8'))
            else:
                row=play(fixture,candidate['candidate'],candidate['candidate_sha256'],seat,output)
            control=next(r for r in screen['games'] if r['version']==route and r['rival']==fixture['fixture_id'] and r['candidate_seat']==seat)
            for field in ('candidate_reward','opponent_reward','frames','candidate_status','opponent_status'):
                assert row[field]==control[field],(team,seat,field,row[field],control[field])
            assert row['candidate_sha256']==candidate['candidate_sha256'] and not row['candidate_errors']
            row.update(version=route,team=fixture['team'],trace_path=str(output),trace_sha256=sha(output),
                       plan_sha256=sha(HERE/'PLAN.md'),native_terminal_parity=True)
            receipt.write_text(json.dumps(row,indent=2),encoding='utf-8')
            item=analyze(row);item['team']=fixture['team']
            rows.append(row);analyses.append(item)
            print(team,seat,'native parity',row['margin'],'noops',item['nochange_counts'],'land',item['land_orders'],flush=True)
    result=dict(complete=True,diagnostic_only=True,plan_sha256=sha(HERE/'PLAN.md'),
                native_screen_sha256=sha(source/'corrected_screen.json'),games=rows,analyses=analyses)
    (HERE/'audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':
    with exclusive_run(HERE/'trace.lock'):main()
