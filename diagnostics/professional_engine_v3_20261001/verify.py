"""Independent native phase parity and final-action commitment checks."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from kaggriculture_engine.engine import canonical


def load(name):
    path = HERE/f'candidate_{name}_r3.py'
    spec = importlib.util.spec_from_file_location('v3_verify_'+name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def main():
    modules = {name: load(name) for name in ('wide', 'guard')}
    m = modules['wide']; package = m._PRO_PACKAGE_NAME
    projection = sys.modules[package+'.pro.projection']
    core = sys.modules[package+'.native_core']
    sim = sys.modules[package+'.pro.simulation']
    sc = sys.modules[package+'.pro.scenarios']
    beliefs = sys.modules[package+'.pro.beliefs']
    jobs = json.loads((ROOT/'diagnostics/fresh90_improvement_20260929/combined_v2_top100_jobs.json').read_text())
    rows = []; decisions = []; native_seconds = 0.; projection_seconds = 0.
    for rank in (1, 8, 10):
        job = next(j for j in jobs if j['rank'] == rank and j['candidate_seat'] == 0)
        replay = json.loads(gzip.decompress(Path(job['entry']['replay_path']).read_bytes()))
        cfg = dict(replay['configuration'], seed=None)
        for step in (0, 144, 239, 478, 480, 718):
            for seat in (0, 1):
                obs = copy.deepcopy(replay['steps'][step][seat]['observation']); obs['step'] = step
                reference = replay['steps'][step+1][seat]['action']
                if not isinstance(reference, dict): reference = {'farmer':['PASS'], 'hands':[], 'market':[]}
                belief = beliefs.RivalBelief().update(obs, cfg)
                scenarios = sc.generate(obs, belief, anchors=True)
                assert scenarios == sc.generate(obs, beliefs.RivalBelief().update(obs, dict(cfg, seed=7654321)), anchors=True)
                for s in scenarios:
                    world = sim.make_world(obs, cfg, s)
                    rival = sc.rival_action(world, seat, reference, s)
                    actions = [None, None]; actions[seat] = reference; actions[1-seat] = rival
                    prepared = projection.prepare(world, actions)
                    alternatives = [reference.get('market', []),
                        [['HIRE'], ['BUY_LAND'], [], ['SELL','WHEAT',9], ['BUY_PRODUCT','WHEAT',9],
                         ['BUY_SEED','WHEAT',2], ['BUY_ANIMAL','GOOSE',1]]]
                    for number, queue in enumerate(alternatives):
                        joint = copy.deepcopy(actions); joint[seat]['market'] = queue
                        queues = [a.get('market', []) for a in joint]
                        stamp = canonical(prepared)
                        tick = time.perf_counter(); projected = projection.project(prepared, queues)
                        projection_seconds += time.perf_counter()-tick
                        assert canonical(prepared) == stamp
                        captured = []
                        original = core._process_market
                        def capture(state, environment):
                            original(state, environment)
                            captured.append(copy.deepcopy(state))
                        direct = copy.deepcopy(world)
                        for p in (0, 1): direct[0][p].action = copy.deepcopy(joint[p])
                        core._process_market = capture
                        tick = time.perf_counter()
                        try: core.interpreter(*direct)
                        finally: core._process_market = original
                        native_seconds += time.perf_counter()-tick
                        actual = captured[0]
                        assert projection.fingerprint(projected) == projection.fingerprint(actual)
                        assert projected[0].observation.farms == actual[0].observation.farms
                        assert projected[0].observation.market == actual[0].observation.market
                        # Output branch isolation, including tile dictionaries.
                        projected[0].observation.farms[0]['tiles'][0][0] = {'kind':'POISON'}
                        projected[0].observation.private['shed']['WHEAT'] = -999
                        assert canonical(prepared) == stamp
                        rows.append({'rank':rank, 'step':step, 'seat':seat, 'scenario':s['name'], 'branch':number, 'passed':True})
                for name, module in modules.items():
                    opt = sys.modules[module._PRO_PACKAGE_NAME+'.pro.optimizer']
                    ps = sys.modules[module._PRO_PACKAGE_NAME+'.pro.simulation']
                    ss = sys.modules[module._PRO_PACKAGE_NAME+'.pro.scenarios']
                    tick = time.perf_counter(); chosen, report = opt.optimize(obs, cfg, reference, belief)
                    elapsed = time.perf_counter()-tick
                    assert report['nodes'] <= 36
                    assert chosen.get('farmer') == reference.get('farmer')
                    assert chosen.get('hands') == reference.get('hands')
                    if report['changed']:
                        for scenario in ss.generate(obs, belief, anchors=True):
                            w = ps.make_world(obs, cfg, scenario)
                            rival = ss.rival_action(w, seat, reference, scenario)
                            before = [None, None]; before[seat] = reference; before[1-seat] = rival
                            after = [None, None]; after[seat] = chosen; after[1-seat] = rival
                            baseline = ps.TransitionCache(0).advance(w, before)
                            result = ps.TransitionCache(0).advance(w, after)
                            assert ps.physical_signature(result) == ps.physical_signature(baseline)
                            assert result[0][0].observation.market['inventory'] == baseline[0][0].observation.market['inventory']
                            a = result[0][0].observation.farms; b = baseline[0][0].observation.farms
                            assert a[seat]['money'] >= b[seat]['money']
                            assert a[seat]['money']-a[1-seat]['money'] >= b[seat]['money']-b[1-seat]['money']
                    decisions.append(dict(rank=rank, step=step, seat=seat, variant=name, seconds=elapsed, **report))
        del replay
    report = {'passed':True, 'phase_parity_branches':len(rows), 'decision_checks':len(decisions),
        'native_full_branch_seconds':native_seconds, 'factored_branch_seconds':projection_seconds,
        'changed_decisions':{n:sum(r['changed'] for r in decisions if r['variant']==n) for n in modules},
        'max_optimizer_seconds':{n:max(r['seconds'] for r in decisions if r['variant']==n) for n in modules},
        'cases':rows, 'decisions':decisions,
        'candidate_hashes':{n:hashlib.sha256((HERE/f'candidate_{n}_r3.py').read_bytes()).hexdigest() for n in modules},
        'limitation':'Counterfactual saved observations; execution parity, not measured game win rate.'}
    (HERE/'engineering_receipt.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('cases','decisions')}, indent=2), flush=True)


if __name__ == '__main__': main()
