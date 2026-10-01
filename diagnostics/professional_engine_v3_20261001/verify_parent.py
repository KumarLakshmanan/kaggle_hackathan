"""Assert inherited search decisions are unchanged by phase factorization."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    path = HERE/'candidate_wide_r3.py'
    spec = importlib.util.spec_from_file_location('v3_parent_parity', path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    engine = m._SEARCH_ENGINE
    jobs = json.loads((ROOT/'diagnostics/fresh90_improvement_20260929/combined_v2_top100_jobs.json').read_text())
    rows = []; slow_seconds = 0.; fast_seconds = 0.
    for rank in (1, 8, 10):
        job = next(j for j in jobs if j['rank'] == rank and j['candidate_seat'] == 0)
        replay = json.loads(gzip.decompress(Path(job['entry']['replay_path']).read_bytes()))
        cfg = dict(replay['configuration'], seed=None)
        for step in (0, 144, 239, 478, 480, 696, 718):
            for seat in (0, 1):
                obs = copy.deepcopy(replay['steps'][step][seat]['observation']); obs['step'] = step
                act = copy.deepcopy(replay['steps'][step+1][seat]['action'])
                if not isinstance(act, dict): act = {'farmer':['PASS'], 'hands':[], 'market':[]}
                if step == 239 and len(act.get('market', [])) < 2:
                    act = dict(act, market=[['BUY_SEED','WHEAT',2], ['HIRE']])
                engine['advance'] = m._FAST_ORIGINAL_ADVANCE
                tick = time.perf_counter(); original, report = engine['optimize_market'](obs, act, cfg, m._SEARCH_SETTINGS)
                slow_seconds += time.perf_counter()-tick
                engine['advance'] = m._fast_parent_advance
                tick = time.perf_counter(); accelerated, fast = engine['optimize_market'](obs, act, cfg, m._SEARCH_SETTINGS)
                fast_seconds += time.perf_counter()-tick
                assert original == accelerated, (rank,step,seat)
                for key in ('nodes', 'accepted', 'gain', 'best_path', 'scenarios', 'scenario_gains', 'budget_exhausted'):
                    assert report.get(key) == fast.get(key), (rank,step,seat,key)
                rows.append({'rank':rank,'step':step,'seat':seat,'nodes':report['nodes'],'passed':True})
        del replay
    assert m._FAST_STATS['parent_full_fallbacks'] > 0
    receipt = {'passed':True,'cases':rows,'original_seconds':slow_seconds,'factored_seconds':fast_seconds,
        'workload_speedup':slow_seconds/fast_seconds if fast_seconds else None,
        'factored_calls':m._FAST_STATS['parent_factored_calls'],
        'full_end_day_fallbacks':m._FAST_STATS['parent_full_fallbacks'],
        'scope':'Same inherited action search; unchanged outputs on saved-state differential probes, not independent win validation.'}
    (HERE/'parent_parity_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k != 'cases'},indent=2),flush=True)


if __name__ == '__main__': main()
