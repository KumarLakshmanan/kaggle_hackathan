"""Finite source-compatible production leaves; one sequential worker."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import gc
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PRIOR = ROOT / 'diagnostics/public_90_research_20260928'
CACHE = ROOT / 'diagnostics/stream_replay_io_20260928'
sys.path.insert(0, str(ROOT))
from diagnostics.stream_replay_io_20260928.fast_game_cached import play
from diagnostics.local_target_20260928.run_lock import exclusive_run

SOURCE = ROOT / 'main_candidate_hire_recovery_integrated_20260928_367d2e76.py'
FULL = ROOT / 'diagnostics/observed_hire_recovery_20260928/native_full.json'
TARGETS = ROOT / 'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
WINS = ROOT / 'diagnostics/partial_planting_20260928/public_win_manifest.json'
ARMS = ('production', 'production_goose')
FIXED = {
    SOURCE: '367d2e7683472af526bdaee5af80c9e7fe59dfb2136475555a2970ef8beccaa0',
    FULL: '1cd02ac25079a1df229ad528c51a94ec467181a4adcd1e6ab13248ff4fd82545',
    TARGETS: '524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20',
    WINS: 'f1cd25bbe3e058fec3bea3bb0cc470cd135780d2bb098e701908daf4053555de',
    PRIOR / 'target.json': 'a588a300e8354b59f7edebbbdf74aee937efb3e7bd3c23736f11e1ec4317a7bb',
    PRIOR / 'pool.json': 'c95aeefaa9b7cc9cd291b8db143c18c71e37d7dad780986c20a9ec70fa7d5cfc',
    PRIOR / 'matched_features72.json': '3876e2ca44714841604a9d7b019a90cabc85f6da45c1dd2a5f4220e3570fdb7e',
    PRIOR / 'feature_parity.json': '1cfd42208a1cfe86680e4854fe66cb785d5ea425b9bc3969fe0cb2b7bdc339af',
    CACHE / 'fast_game_cached.py': 'a57d12659af613512a61ac02aaa43d4c5ae4f4d8f2c5c02d3ed4ac6eafa2a38e',
    CACHE / 'cached_input.py': 'e2aaefda623775c9c7d56304271c827ecd6e56cc109e5c6d8b35aeb458268aa1',
    CACHE / 'initial_states.json': 'f544b134e2ad51160e4d6ad7719b9f41ad6cc850a1a51162249ede1cba279968',
    ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py': '5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795',
}


def now(): return datetime.now(timezone.utc).isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
def point(row): return {'win': 1, 'draw': .5, 'loss': 0}[row['result']]
def rowkey(row): return row['version'], row['fixture_id'], row['candidate_seat']


def inputs():
    for path, digest in FIXED.items(): assert sha(path) == digest, str(path)
    parity = read(PRIOR / 'feature_parity.json')
    assert parity['complete'] and parity['passed'] and parity['compared_prefixes'] == 42
    assert parity['matched_features_sha256'] == sha(PRIOR / 'matched_features72.json')
    cached = read(CACHE / 'cached_helper_parity.json')
    assert cached['passed'] and len(cached['games']) == 2
    for path, digest in read(CACHE / 'cached_helper_manifest.json')['bindings'].items():
        assert sha(path) == digest, path
    prior = read(PRIOR / 'pool.json'); target = read(PRIOR / 'target.json')
    assert target['complete'] and target['clean'] and target['game_count'] == 320
    assert target['pool_sha256'] == sha(PRIOR / 'pool.json')
    for variant in prior['variants']: assert sha(variant['candidate']) == variant['candidate_sha256']
    features = read(PRIOR / 'matched_features72.json')
    assert features['complete'] and features['prefix_count'] == 208
    fs = read(TARGETS); fixtures = fs['live_losses'] + fs['current_top20'] + read(WINS)['fixtures']
    assert len(fixtures) == 104 and len({f['fixture_id'] for f in fixtures}) == 104
    by_feature = {(r['fixture_id'], r['candidate_seat']): r for r in features['rows']}
    assert len(by_feature) == 208
    controls = {(r['rival'], r['candidate_seat']): r for r in read(FULL)['games'] if r['version'] == 'integrated'}
    assert len(controls) == 100
    return prior, target, fixtures, by_feature, controls


def feature_key(row, arm):
    public = row['rival_public']; animals = public['animal_counts']
    cow, sheep = animals.get('COW', 0), animals.get('SHEEP', 0)
    comparison = 'C<S' if cow < sheep else 'C>S' if cow > sheep else 'C=S'
    key = row['revealed_shops'][0] + '|' + ('M8+' if public['crop_counts'].get('MELON', 0) >= 8 else 'M<8') + '|' + comparison
    if arm == 'production_goose': key += '|G+' if animals.get('GOOSE', 0) > 0 else '|G0'
    return key


def observation(row):
    seat = row['candidate_seat']; farms = [None, None]
    farms[seat] = row['own_farm']; farms[1-seat] = row['rival_farm']
    return dict(step=72, player=seat, farms=farms, town={'unlocked_shops': row['revealed_shops']})


def build(arm, rules, path):
    layer = (HERE / 'layer.py').read_text(encoding='utf-8').replace('ARM_VALUE', repr(arm)).replace('RULES_VALUE', repr(rules))
    blob = SOURCE.read_bytes() + b'\n' + layer.encode('utf-8')
    compile(blob, str(path), 'exec')
    if not path.exists(): path.write_bytes(blob)
    assert path.read_bytes() == blob
    return sha(path)


def load(path):
    spec = importlib.util.spec_from_file_location('production_leaf_preflight', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def metrics(rows, controls):
    pairs = {fid: [r for r in rows if r['fixture_id'] == fid] for fid in {r['fixture_id'] for r in rows}}
    assert all(len(pair) == 2 for pair in pairs.values())
    rescued = sorted(fid for fid, pair in pairs.items() if all(r['result'] == 'win' for r in pair)
                     and any(controls[(fid, seat)]['result'] != 'win' for seat in (0, 1)))
    return dict(rescues=rescued, points=sum(point(r) for r in rows),
                delta_margin=sum(r['margin'] - controls[(r['fixture_id'], r['candidate_seat'])]['margin'] for r in rows))


def prepare():
    assert not (HERE / 'pool.json').exists()
    prior, target, fixtures, features, controls = inputs()
    reps = sorted([r['route'] for r in prior['representatives']], key=int)
    dev_ids = {fid for fids in prior['target_ids'].values() for fid in fids}
    assert len(reps) == 10 and len(dev_ids) == 16
    development = {(r['shop'], r['route'], r['fixture_id'], r['candidate_seat']): r for r in target['games']}
    (HERE / 'candidates').mkdir(exist_ok=True)
    candidates = []; rejected_fits = []; key_rows = []; checks = []
    for arm in ARMS:
        leaves = {key: feature_key(row, arm) for key, row in features.items()}
        key_rows.extend(dict(arm=arm, fixture_id=fid, seat=seat, leaf=leaf) for (fid, seat), leaf in leaves.items())
        dev_leaves = sorted({leaves[(fid, seat)] for fid in dev_ids for seat in (0, 1)})
        for leaf in dev_leaves:
            shop = leaf.split('|')[0]
            affected_dev = sorted(fid for fid in dev_ids if any(leaves[(fid, s)] == leaf for s in (0, 1)))
            scores = []
            for route in reps:
                rows = []
                for fid in affected_dev:
                    for seat in (0, 1):
                        chosen = development[(shop, route, fid, seat)] if leaves[(fid, seat)] == leaf else controls[(fid, seat)]
                        rows.append(dict(chosen, fixture_id=fid, candidate_seat=seat))
                score = dict(route=route, **metrics(rows, controls))
                if score['rescues']: scores.append(score)
            scores.sort(key=lambda s: (-len(s['rescues']), -s['points'], -s['delta_margin'], int(s['route'])))
            if not scores:
                rejected_fits.append(dict(arm=arm, leaf=leaf, reason='No independently rescuing one-leaf medoid in fixed development panel'))
            for rank, score in enumerate(scores[:2]):
                route = score['route']; token = hashlib.sha256(leaf.encode()).hexdigest()[:10]
                version = f'{arm}_{token}_{route}'; path = HERE / 'candidates' / (version + '.py')
                digest = build(arm, {leaf: int(route)}, path)
                affected = sorted(f['fixture_id'] for f in fixtures if any(leaves[(f['fixture_id'], s)] == leaf for s in (0, 1)))
                module = load(path)
                assert module._DATA['routes'][route][:72] == module._DATA['opening'][:72]
                assert len(module._DATA['routes'][route]) == 719
                for key, row in features.items(): assert module._production_leaf_key(observation(row)) == leaves[key]
                base_map = dict(module._DATA['route_map']); base_farmice = module._FARMICE_TAPE
                module._production_leaf_commit(leaf, route)
                assert all(value == int(route) if key.split('|')[0] == shop else value == base_map[key]
                           for key, value in module._DATA['route_map'].items() if key in base_map)
                representative_obs = observation(features[(affected_dev[0], next(s for s in (0, 1) if leaves[(affected_dev[0], s)] == leaf))])
                assert module._hire_recovery_schedule(representative_obs) == module._DATA['routes'][route]
                if shop == 'FARMERS_MARKET': assert module._FARMICE_TAPE == module._DATA['routes'][route]
                module._production_leaf_reset()
                assert module._DATA['route_map'] == base_map and module._FARMICE_TAPE == base_farmice
                assert callable(module.kaggle_production_leaf_entrypoint)
                del module; gc.collect()
                checks.append(dict(version=version, all208_feature_keys=True, common72=True, route_maps=True, hire_schedule=True, reset=True))
                candidates.append(dict(version=version, arm=arm, leaf=leaf, shop=shop, route=route,
                                       candidate=str(path), candidate_sha256=digest, shortlist_rank=rank,
                                       development_fixture_ids=affected_dev, affected_fixture_ids=affected, fitting_score=score))
    affected_wins = sorted({fid for c in candidates for fid in c['affected_fixture_ids'] if fid.startswith('public-win-')})
    bound = dict((str(path), digest) for path, digest in FIXED.items())
    for path in [Path(__file__), HERE / 'layer.py', HERE / 'PLAN.md', CACHE / 'cached_helper_parity.json', CACHE / 'cached_helper_manifest.json']:
        bound[str(path)] = sha(path)
    pool = dict(created_at_utc=now(), bindings=bound, candidates=candidates, no_fit_leaves=rejected_fits,
                features=key_rows, fixtures=fixtures, source_control_fixture_ids=affected_wins,
                source_control_games=2*len(affected_wins), conditional_games=sum(2*len(c['affected_fixture_ids']) for c in candidates),
                development_fitting_only=True, no_new_outcomes=True)
    write(HERE / 'pool.json', pool)
    write(HERE / 'preflight.json', dict(passed=True, pool_sha256=sha(HERE / 'pool.json'), checks=checks, created_at_utc=now()))
    print(json.dumps(dict(candidates=len(candidates), no_fit_leaves=len(rejected_fits), controls=pool['source_control_games'],
                          conditional=pool['conditional_games'], pool_sha256=sha(HERE / 'pool.json')), indent=2), flush=True)


def context():
    pool = read(HERE / 'pool.json')
    for path, digest in pool['bindings'].items(): assert sha(path) == digest, path
    for c in pool['candidates']: assert sha(c['candidate']) == c['candidate_sha256']
    assert read(HERE / 'preflight.json')['passed']
    assert read(HERE / 'preflight.json')['pool_sha256'] == sha(HERE / 'pool.json')
    return pool


def source_controls():
    controls = {(r['rival'], r['candidate_seat']): r for r in read(FULL)['games'] if r['version'] == 'integrated'}
    if (HERE / 'controls.json').exists():
        receipt = read(HERE / 'controls.json'); assert receipt['complete'] and receipt['pool_sha256'] == sha(HERE / 'pool.json')
        controls.update(((r['fixture_id'], r['candidate_seat']), r) for r in receipt['games'])
    return controls


def run(phase):
    pool = context(); fixtures = {f['fixture_id']: f for f in pool['fixtures']}
    leaves = {(r['arm'], r['fixture_id'], r['seat']): r['leaf'] for r in pool['features']}
    if phase == 'controls':
        jobs = [(dict(version='source', candidate=str(SOURCE), candidate_sha256=FIXED[SOURCE]), fixtures[fid], seat)
                for fid in pool['source_control_fixture_ids'] for seat in (0, 1)]
    elif phase == 'conditional':
        control_receipt = read(HERE / 'controls.json'); assert control_receipt['complete'] and control_receipt['clean']
        jobs = [(c, fixtures[fid], seat) for c in pool['candidates'] for fid in c['affected_fixture_ids'] for seat in (0, 1)]
    else:
        selection = read(HERE / 'selection.json'); assert selection['complete'] and selection['pool_sha256'] == sha(HERE / 'pool.json')
        jobs = [(c, f, seat) for c in selection['combined'] for f in pool['fixtures'] if not f['fixture_id'].startswith('public-win-') for seat in (0, 1)]
        for c in selection['combined']: assert sha(c['candidate']) == c['candidate_sha256']
    output_path = HERE / (phase + '.json'); assert not output_path.exists()
    ledger = HERE / (phase + '.jsonl'); rows = [json.loads(s) for s in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
    done = {rowkey(r) for r in rows}; assert len(rows) == len(done)
    expected = {(c['version'], f['fixture_id'], s): (c, f, s) for c, f, s in jobs}
    for row in rows:
        c, _, _ = expected[rowkey(row)]
        assert row['candidate_sha256'] == c['candidate_sha256'] and row['pool_sha256'] == sha(HERE / 'pool.json')
    controls = source_controls()
    development = {(r['shop'], r['route'], r['fixture_id'], r['candidate_seat']): r for r in read(PRIOR / 'target.json')['games']}
    with ledger.open('a', encoding='utf-8') as stream:
        for c, f, seat in jobs:
            key = c['version'], f['fixture_id'], seat
            if key in done: continue
            row = play(f, c['candidate'], c['candidate_sha256'], seat)
            row.update(version=c['version'], team=f['team'], pool_sha256=sha(HERE / 'pool.json'), helper_sha256=sha(__file__))
            row['clean'] = row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE' and not row['candidate_errors']
            if phase != 'controls':
                old = controls[(f['fixture_id'], seat)]
                row.update(parent_result=old['result'], parent_margin=old['margin'],
                           delta_own=row['candidate_reward']-old['candidate_reward'], delta_rival=row['opponent_reward']-old['opponent_reward'],
                           delta_margin=row['margin']-old['margin'])
                leaf = leaves[(c['arm'], f['fixture_id'], seat)]
                route = (c['route'] if leaf == c['leaf'] else '') if phase == 'conditional' else str(c['rules'].get(leaf, ''))
                telem = row['candidate_telemetry']
                row['activation_passed'] = telem['production_leaf_key72'] == leaf and telem['production_leaf_route'] == route and telem['production_leaf_turns'] == (647 if route else 0)
                row['development_parity_mismatches'] = []
                if phase == 'conditional':
                    reference = development.get((c['shop'], c['route'], f['fixture_id'], seat)) if route else old
                    if reference is not None:
                        row['development_parity_mismatches'] = [field for field in ('candidate_reward', 'opponent_reward', 'result', 'frames', 'candidate_status', 'opponent_status') if row[field] != reference[field]]
            rows.append(row); done.add(key); stream.write(json.dumps(row, ensure_ascii=False)+'\n'); stream.flush()
            print(phase, len(rows), '/', len(jobs), c['version'], f['team'], seat, row['result'], row['margin'], flush=True)
    write(output_path, dict(complete=len(rows)==len(jobs), clean=all(r['clean'] for r in rows), phase=phase,
                            pool_sha256=sha(HERE / 'pool.json'), helper_sha256=sha(__file__), games=rows, completed_at_utc=now(), diagnostic_only=True))


def select():
    pool = context(); receipt = read(HERE / 'conditional.json')
    assert receipt['complete'] and receipt['pool_sha256'] == sha(HERE / 'pool.json')
    controls = source_controls(); summaries = []; eligible = {}
    for c in pool['candidates']:
        rows = [r for r in receipt['games'] if r['version'] == c['version']]
        assert len(rows) == 2*len(c['affected_fixture_ids'])
        regressions = [dict(fixture_id=r['fixture_id'], seat=r['candidate_seat'], parent_margin=r['parent_margin'],
                            margin=r['margin'], delta_own=r['delta_own'], delta_rival=r['delta_rival'])
                       for r in rows if r['parent_result']=='win' and r['result']!='win']
        development = [r for r in rows if r['fixture_id'] in c['development_fixture_ids']]
        score = metrics(development, controls)
        clean = all(r['clean'] and r['activation_passed'] and not r['development_parity_mismatches'] for r in rows)
        passed = clean and not regressions and bool(score['rescues'])
        summary = dict(version=c['version'], arm=c['arm'], leaf=c['leaf'], route=c['route'], passed=passed,
                       clean=clean, regressions=regressions, actual_development=score, shortlist_rank=c['shortlist_rank'])
        summaries.append(summary)
        if passed: eligible.setdefault((c['arm'], c['leaf']), []).append(c)
    combined = []
    for arm in ARMS:
        rules = {leaf: int(min(options, key=lambda c:c['shortlist_rank'])['route']) for (a, leaf), options in eligible.items() if a==arm}
        if rules:
            path = HERE / ('candidate_'+arm+'.py'); digest = build(arm, dict(sorted(rules.items())), path)
            backup = HERE / ('main_candidate_'+arm+'_'+digest[:8]+'.py'); backup.write_bytes(path.read_bytes())
            combined.append(dict(version=arm, arm=arm, rules=rules, candidate=str(path), candidate_sha256=digest, backup=str(backup)))
    write(HERE / 'selection.json', dict(complete=True, passed=bool(combined), pool_sha256=sha(HERE / 'pool.json'),
          conditional_sha256=sha(HERE / 'conditional.json'), controls_sha256=sha(HERE / 'controls.json'),
          combined=combined, summaries=summaries, selected_at_utc=now(), diagnostic_only=True))
    print(json.dumps(dict(combined=combined, rejected=len(summaries)-sum(s['passed'] for s in summaries)), indent=2), flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('phase', choices=('prepare','controls','conditional','select','full'))
    args=parser.parse_args()
    with exclusive_run(HERE/'study.lock'):
        if args.phase=='prepare': prepare()
        elif args.phase=='select': select()
        else: run(args.phase)
