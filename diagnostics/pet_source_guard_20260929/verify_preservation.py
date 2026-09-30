"""Verify the reporting guard preserves the completed saved-panel outcomes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
BASE = ROOT / 'diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929'
DIGEST = '257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55'
FIELDS = ('result', 'candidate_reward', 'opponent_reward', 'margin',
          'candidate_status', 'opponent_status', 'frames')
NEW_KEY = 'a44_pet_market_gate_branch72'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def bindings():
    expected = {
        HERE / 'candidate.py': DIGEST,
        BASE / 'frozen_manifest.json': '2e376dcaffbcaf9557b5cade1a84e66e751f64b9cc550a07dbd9604cdeab34dc',
        BASE / 'outcome_receipt.json': 'ec2f45acfa6a7988868bb13e657a639e546ced46d148c15456e78679b0d7dcb5',
        BASE / 'panel.json': 'fee3b1d5f93cd295c28dd8d0c04ea672806dbb55e2b59999853a9f969c0fb90d',
    }
    for path, digest in expected.items():
        assert sha(path) == digest, str(path)
    prior = read(BASE / 'frozen_manifest.json')
    for rel, digest in prior['internal_files'].items():
        assert sha(BASE / rel) == digest, rel
    for path, digest in prior['external_inputs'].items():
        assert sha(path) == digest, path
    return {str(path): digest for path, digest in expected.items()}


def verify():
    frozen = read(HERE / 'preservation_manifest.json')
    assert frozen['bindings'] == bindings()
    assert frozen['runner_sha256'] == sha(Path(__file__))
    assert frozen['candidate_sha256'] == DIGEST
    assert frozen['planned_games'] == 102
    assert not any((HERE / p).exists() for p in ('preservation_outcomes.jsonl', 'preservation_receipt.json'))
    return frozen


def run():
    frozen = verify()
    from diagnostics.stream_replay_io_20260928.fast_game_cached import play
    from diagnostics.local_target_20260928.run_lock import exclusive_run
    panel = read(BASE / 'panel.json')
    old = read(BASE / 'outcome_receipt.json')
    old_rows = {(r['fixture_id'], int(r.get('candidate_seat', r.get('seat')))): r for r in old['games']}
    jobs = [dict(fixture=x['fixture'], fixture_id=x['fixture_id'], seat=int(x['candidate_seat']), panel=x['panel'])
            for x in panel['games']]
    jobs += [dict(fixture=x['fixture'], fixture_id=x['fixture_id'], seat=int(x['seat']), panel='public_win_control')
             for x in panel['controls']]
    assert len(jobs) == len({(j['fixture_id'], j['seat']) for j in jobs}) == 102
    rows = []
    with exclusive_run(ROOT / 'diagnostics/.shared_game_run.lock'):
        with exclusive_run(HERE / 'preservation.lock'):
            with (HERE / 'preservation_outcomes.jsonl').open('x', encoding='utf-8') as output:
                for i, job in enumerate(jobs, 1):
                    actual = play(job['fixture'], HERE / 'candidate.py', DIGEST, job['seat'])
                    reference = old_rows[(job['fixture_id'], job['seat'])]
                    expected = reference.get('actual', reference.get('candidate'))
                    t = actual['candidate_telemetry']
                    branch = t.get(NEW_KEY)
                    active = (branch == 'source' and t.get('a44_pet_market_gate_key72') == 'PET_CAFE|M8+|C>S|G0'
                              and t.get('a44_pet_market_gate_rival_melon72') == 12
                              and t.get('a44_pet_market_gate_wheat_stock72') == 9975)
                    checks = {
                        'exact_outcome_preservation': all(actual[k] == expected[k] for k in FIELDS),
                        'clean': actual['candidate_status'] == actual['opponent_status'] == 'DONE'
                                 and actual['frames'] == 720 and not actual['candidate_errors'],
                        'actual_bridge_recorded': branch == t.get('bridge_selected') and branch in ('source', 'shared150', 'shared151'),
                        'effective_pet_activation': t.get('a44_pet_market_gate_active72') is active,
                        'effective_pet_route': t.get('a44_pet_market_gate_route72') == ('113517834' if active else ''),
                        'effective_pet_calls': t.get('a44_pet_market_gate_turns') == (647 if active else 0),
                        'zero_pet_errors': t.get('a44_pet_market_gate_errors') == 0,
                    }
                    if 'candidate_telemetry' in expected:
                        checks['prior_telemetry_preserved'] = {k: v for k, v in t.items() if k != NEW_KEY} == expected['candidate_telemetry']
                    row = dict(fixture_id=job['fixture_id'], candidate_seat=job['seat'], panel=job['panel'],
                               actual=actual, checks=checks, passed=all(checks.values()))
                    rows.append(row)
                    output.write(json.dumps(row, ensure_ascii=True) + '\n'); output.flush()
                    print(json.dumps({'completed': i, 'planned': 102, 'fixture': job['fixture_id'],
                                      'seat': job['seat'], 'result': actual['result'], 'passed': row['passed']}), flush=True)
            sweeps = {}
            for tag in ('loss30', 'top20'):
                selected = [r for r in rows if r['panel'] == tag]
                by_id = {(r['fixture_id'], r['candidate_seat']): r for r in selected}
                ids = {r['fixture_id'] for r in selected}
                sweeps[tag] = sum(all(by_id[(fid, s)]['actual']['result'] == 'win' for s in (0, 1)) for fid in ids)
            receipt = dict(candidate_sha256=DIGEST, complete=len(rows) == 102,
                           passed=all(r['passed'] for r in rows) and sweeps == {'loss30': 27, 'top20': 19},
                           fixed_tape_only=True, research_promotion=False, preservation_only=True,
                           parent_candidate_sha256='ebfbe6e91008cf39d1929d52a60e3cb140d2b1cffdd3fac8e06c122eb9876bbe',
                           manifest_sha256=sha(HERE / 'preservation_manifest.json'),
                           completed_at_utc=datetime.now(timezone.utc).isoformat(),
                           winning_sweeps=sweeps, games=rows)
            with (HERE / 'preservation_receipt.json').open('x', encoding='utf-8') as out:
                json.dump(receipt, out, ensure_ascii=True, indent=2)
            print(json.dumps({k: v for k, v in receipt.items() if k != 'games'}, indent=2), flush=True)
            return receipt


if __name__ == '__main__':
    if '--freeze' in sys.argv:
        assert not (HERE / 'preservation_manifest.json').exists()
        payload = dict(candidate_sha256=DIGEST, bindings=bindings(), runner_sha256=sha(Path(__file__)),
                       planned_games=102, fixed_tape_only=True, preservation_only=True,
                       criteria='Exact prior results/rewards/status/frame and all prior telemetry on the 100 panel rows; 2 control outcomes preserved; effective Pet source ownership and zero errors; 27/30 loss and 19/20 top20 sweeps.')
        with (HERE / 'preservation_manifest.json').open('x', encoding='utf-8') as out:
            json.dump(payload, out, indent=2)
        print('Frozen preservation check; 0 games run.')
    elif '--run' in sys.argv:
        result = run()
        if not result['passed']:
            raise SystemExit(1)
    else:
        verify()
        print('Verified preservation inputs; 0 games run.')
