from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928.fast_game import play,sha
from diagnostics.local_target_20260928.run_lock import exclusive_run


def main():
    selected=json.loads((HERE/'selection.json').read_text(encoding='utf-8'))
    pool=json.loads((HERE/'pool.json').read_text(encoding='utf-8'))
    screen=json.loads((HERE/'screen.json').read_text(encoding='utf-8'))
    fixture=next(f for f in pool['fixtures'] if f['team']=='mhw')
    route=str(selected['selected_replacements']['BAKERY|PIZZA_SHOP'])
    versions={'old':(str(ROOT/'main.py'),pool['source_sha256']),
              'new':(selected['candidate'],selected['candidate_sha256'])}
    rows=[]
    for version,(path,digest) in versions.items():
        for seat in (0,1):
            output=HERE/f'mhw_{version}_seat{seat}.jsonl.gz'
            receipt=output.with_name(output.name+'.receipt.json')
            if output.exists():
                row=json.loads(receipt.read_text())
            else:
                row=play(fixture,path,digest,seat,output)
            baseline=(next(r for r in fixture['baseline_frozen_tape_both_seat_outcomes'] if r['seat']==seat)
                if version=='old' else next(r for r in screen['games'] if r['version']==route and r['rival']==fixture['fixture_id'] and r['candidate_seat']==seat))
            for name in ('candidate_reward','opponent_reward','frames','candidate_status','opponent_status'):
                assert row[name]==baseline[name],(version,seat,name,row[name],baseline[name])
            assert row['candidate_sha256']==digest and not row['candidate_errors']
            row.update(version=version,trace_path=str(output),trace_sha256=sha(output),
                       plan_sha256=sha(HERE/'SEAT_DIAGNOSIS_PLAN.md'),native_terminal_parity=True)
            receipt.write_text(json.dumps(row,indent=2),encoding='utf-8')
            rows.append(row);print(version,seat,'exact native parity',row['margin'],flush=True)
    (HERE/'mhw_traces.json').write_text(json.dumps(dict(complete=True,diagnostic_only=True,games=rows),indent=2),encoding='utf-8')


if __name__=='__main__':
    with exclusive_run(HERE/'trace.lock'):main()
