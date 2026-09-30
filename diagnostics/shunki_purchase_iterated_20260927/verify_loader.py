from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_module, make, TimedAgent, _timing_dict
from kaggle_environments.agent import get_last_callable

if __name__ == '__main__':
    manifest = json.loads((HERE / 'build_manifest.json').read_text())
    gate = json.loads((HERE / 'confirmation.json').read_text())
    assert gate['complete'] and gate['passed'] and gate['candidate_sha256'] == manifest['candidate_sha256']
    candidate = Path(manifest['candidate'])
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == manifest['candidate_sha256']
    loaded = get_last_callable(candidate.read_text(encoding='utf8'), path=str(candidate)).__name__
    assert loaded == manifest['entrypoint']
    pilot = json.loads((HERE / 'pilot.json').read_text())
    seed = pilot['both_component_pairs']['c68'][0]
    reference = ROOT / 'main_uploaded_disjoint_integrated_20260927_c68fa46f.py'
    assert hashlib.sha256(reference.read_bytes()).hexdigest() == manifest['incumbent_sha256']
    rows = []
    for seat in (0,1):
        results = {}
        for mode in ('direct','file'):
            modules = [_load_module(reference, 'purchase_iterated_file_rival')]
            def rival(obs,cfg):
                cfg = dict(cfg); cfg['seed'] = None
                return modules[0].agent(obs,cfg)
            agents = [rival,rival]
            if mode == 'file':
                agents[seat] = str(candidate)
            else:
                modules.append(_load_module(candidate, 'purchase_iterated_file_candidate'))
                def call(obs,cfg):
                    cfg = dict(cfg); cfg['seed'] = None
                    return modules[1].agent(obs,cfg)
                timed = TimedAgent(call)
                agents[seat] = timed
            try:
                env = make('kaggriculture', configuration={'episodeSteps':720,'seed':seed}, debug=False)
                env.run(agents)
                final = env.steps[-1]
                result = dict(cash=[float(x.reward) for x in final], statuses=[x.status for x in final],
                              frames=len(env.steps), actions=[[f[p].action for p in (0,1)] for f in env.steps[1:]])
                assert result['statuses'] == ['DONE','DONE'] and result['frames'] == 720
                result['minimum_remaining_overage_seconds'] = min(float(f[seat].observation.remainingOverageTime) for f in env.steps)
                result['initial_overage_seconds'] = float(env.steps[0][seat].observation.remainingOverageTime)
                assert result['minimum_remaining_overage_seconds'] >= 0
                if mode == 'direct':
                    result['timing'] = _timing_dict(timed)
                    result['act_timeout_seconds'] = float(env.configuration.actTimeout)
                    result['telemetry'] = dict(modules[1].agent.telemetry)
                    peak_step = int(result['timing']['max_step'])
                    peak_budget = result['act_timeout_seconds'] + float(env.steps[peak_step][seat].observation.remainingOverageTime)
                    result['native_budget_at_peak_seconds'] = peak_budget
                    assert result['timing']['max_ms'] < peak_budget * 1000
                    assert result['telemetry']['purchase_queue_turns'] > 0 and result['telemetry']['iterated_queue_turns'] > 0
                results[mode] = result
            finally:
                for module in modules:
                    sys.modules.pop(module.__name__,None)
        assert results['direct']['cash'] == results['file']['cash']
        assert results['direct']['actions'] == results['file']['actions']
        row = dict(seat=seat, seed=seed, file_cash=results['file']['cash'], direct_cash=results['direct']['cash'],
                   all_719_actions_both_players_equal=True, statuses=results['file']['statuses'],
                   timing=results['direct']['timing'], act_timeout_seconds=results['direct']['act_timeout_seconds'],
                   native_budget_at_peak_seconds=results['direct']['native_budget_at_peak_seconds'],
                   file_minimum_remaining_overage_seconds=results['file']['minimum_remaining_overage_seconds'],
                   direct_minimum_remaining_overage_seconds=results['direct']['minimum_remaining_overage_seconds'],
                   initial_overage_seconds=results['file']['initial_overage_seconds'],
                   telemetry=results['direct']['telemetry'])
        rows.append(row)
        print('PARITY '+json.dumps(row),flush=True)
    out = dict(completed_at_utc=datetime.now(timezone.utc).isoformat(), candidate_sha256=manifest['candidate_sha256'],
               loaded_name=loaded, rows=rows, passed=True)
    (HERE / 'loader_parity.json').write_text(json.dumps(out,indent=2),encoding='utf8')
