"""Compare recorded source resources with the audited continuation, no games."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module
from diagnostics.dsm_state_matched_20260927.diagnose_prefix import differences


def source_obs(replay, step, seat):
    frame = replay['steps'][step]
    obs = dict(frame[0]['observation'])
    obs.update(frame[seat]['observation'])
    return obs


def resources(obs, seat):
    return dict(farm={k:v for k,v in obs['farms'][seat].items() if k!='money'}, private=obs['private'])


if __name__ == '__main__':
    d = json.loads((HERE / 'audit.json').read_text()); assert d['complete']
    manifest = json.loads((ROOT / 'diagnostics/dsm_state_matched_20260927/build_manifest.json').read_text())
    sources = {s['episode_id']:s for s in manifest['sources']}
    module = _load_module(ROOT / 'main_candidate_dsm_frontloaded_bank_20260927_dd420938.py', 'dsm_source_comparison')
    rows=[]
    try:
        for g in d['games']:
            raw = gzip.decompress(Path(g['trace_path']).read_bytes())
            assert hashlib.sha256(raw).hexdigest() == g['trace_sha256']
            trace = json.loads(raw)
            seat = g['candidate_seat']
            obs72 = trace['traces'][seat][72]['observation']
            key = module._canonical([72,obs72['town']['unlocked_shops'],module._state_hash(obs72)])
            selected = module._INDEX[key]
            eid = module._EPISODES[selected]
            source = sources[eid]
            stored_source = Path(source['replay_path']).read_bytes()
            raw_source = gzip.decompress(stored_source) if stored_source[:2] == b'\x1f\x8b' else stored_source
            assert hashlib.sha256(raw_source).hexdigest() == source['replay_sha256']
            replay = json.loads(raw_source)
            source_seat = source['source_seat']
            expected72 = source_obs(replay,72,source_seat)
            assert resources(obs72,seat)==resources(expected72,source_seat)
            states=[]
            for step in range(72,145):
                actual = trace['traces'][seat][step]['observation']
                expected = source_obs(replay,step,source_seat)
                delta = differences(resources(expected,source_seat),resources(actual,seat))
                states.append(dict(step=step,resource_differences=delta,
                                   native_cash=actual['farms'][seat]['money'],source_cash=expected['farms'][source_seat]['money'],
                                   native_prices=actual['market']['prices'],source_prices=expected['market']['prices'],
                                   native_market_orders=trace['traces'][seat][step]['action']['market'],
                                   source_market_orders=replay['steps'][step+1][source_seat]['action']['market']))
            first = next((s for s in states if s['resource_differences']),None)
            row=dict(seed=g['seed'],seat=seat,selected_episode=eid,source_replay_sha256=source['replay_sha256'],
                     opening_native_cash=obs72['farms'][seat]['money'],opening_source_cash=expected72['farms'][source_seat]['money'],
                     first_resource_divergence=first,states=states)
            rows.append(row)
            print(json.dumps({k:v for k,v in row.items() if k!='states'},ensure_ascii=False),flush=True)
        (HERE / 'source_comparison.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
    finally:
        sys.modules.pop(module.__name__,None)
