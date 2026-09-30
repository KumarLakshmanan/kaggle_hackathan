from datetime import datetime,timezone
from pathlib import Path
import gzip
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from diagnostics.physical_route_rollout_20260928.check import sha,state_from_frames,compare
from diagnostics.physical_route_rollout_20260928.fast_reactive import play
from diagnostics.local_target_20260928.run_lock import exclusive_run


def main():
    from paired_benchmark import make,engine_version
    assert engine_version=='1.32.7'
    manifest=ROOT/'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
    assert sha(manifest)=='524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
    fixture=json.loads(manifest.read_text(encoding='utf-8'))['live_losses'][0]
    raw=gzip.decompress(Path(fixture['source_replay_path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==fixture['source_replay_sha256']
    replay=json.loads(raw)
    env=make('kaggriculture',configuration={'episodeSteps':720,'seed':2909021},debug=False);env.reset(2)
    expected=json.loads(json.dumps(env.steps[0]))
    assert not compare(state_from_frames(replay['steps'][0]),expected)
    assert {k:v for k,v in replay['configuration'].items() if k!='seed'}=={k:v for k,v in dict(env.configuration).items() if k!='seed'}
    template=dict(frame=replay['steps'][0],configuration=dict(replay['configuration'],seed=None),
                  source_replay_sha256=fixture['source_replay_sha256'],native_initial_parity=True)
    target=HERE/'initial_template.json'
    if target.exists():assert json.loads(target.read_text(encoding='utf-8'))==template
    else:target.write_text(json.dumps(template,indent=2),encoding='utf-8')
    del replay,env,raw
    native=ROOT/'diagnostics/compatible_route_pool_20260928/native_pilot.json'
    reference=json.loads(native.read_text(encoding='utf-8'))
    assert reference['complete'] and reference['all_done'] and reference['no_errors']
    selected={('old','4ee',2909021),('new','4ee',2909080),('new','market',2909080),('old','market',2909112)}
    controls=[r for r in reference['games'] if (r['version'],r['rival'],r['seed']) in selected]
    assert len(controls)==8
    rows=[]
    for control in controls:
        names=('version','rival','seed','candidate_seat','path','candidate_sha256','opponent','opponent_sha256')
        row=play({k:control[k] for k in names})
        fields=('candidate_reward','opponent_reward','frames','candidate_status','opponent_status','candidate_telemetry')
        row['mismatches']=[k for k in fields if row[k]!=control[k]]
        row['passed']=not row['mismatches'] and not row['candidate_errors'] and not row['opponent_errors']
        rows.append(row)
        print(len(rows),row['version'],row['rival'],row['seed'],row['candidate_seat'],row['passed'],row['mismatches'],flush=True)
    result=dict(complete=True,passed=all(r['passed'] for r in rows),diagnostic_only=True,
                plan_sha256=sha(HERE/'REACTIVE_PLAN.md'),helper_sha256=sha(HERE/'fast_reactive.py'),
                core_sha256=sha(HERE/'native_core.py'),template_sha256=sha(target),native_results_sha256=sha(native),
                completed_at_utc=datetime.now(timezone.utc).isoformat(),games=rows)
    (HERE/'reactive_parity.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Reacting engine parity',result['passed'])


if __name__=='__main__':
    with exclusive_run(HERE/'reactive_parity.lock'):main()
