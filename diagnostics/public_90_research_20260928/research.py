"""Offline first-shop production commitments; one sequential benchmark worker."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.physical_route_rollout_20260928.fast_game import play, sha
from diagnostics.local_target_20260928.run_lock import exclusive_run

SOURCE = ROOT / 'main_candidate_hire_recovery_integrated_20260928_367d2e76.py'
SOURCE_SHA = '367d2e7683472af526bdaee5af80c9e7fe59dfb2136475555a2970ef8beccaa0'
FULL = ROOT / 'diagnostics/observed_hire_recovery_20260928/native_full.json'
FULL_SHA = '1cd02ac25079a1df229ad528c51a94ec467181a4adcd1e6ab13248ff4fd82545'
TARGETS = ROOT / 'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
TARGETS_SHA = '524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'


def now(): return datetime.now(timezone.utc).isoformat()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path, data):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
def action_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
def key(row): return row['version'], row['fixture_id'], row['candidate_seat']
def points(row): return {'win': 1, 'draw': .5, 'loss': 0}[row['result']]


def sources():
    for path, digest in ((SOURCE, SOURCE_SHA), (FULL, FULL_SHA), (TARGETS, TARGETS_SHA)):
        assert sha(path) == digest, str(path)


def candidate(replacements, path):
    assert sha(SOURCE) == SOURCE_SHA
    layer = (HERE / 'layer.py').read_text(encoding='utf-8').replace('REPLACEMENTS_VALUE', repr(replacements))
    blob = SOURCE.read_bytes() + b'\n' + layer.encode('utf-8')
    compile(blob, str(path), 'exec')
    path.write_bytes(blob) if not path.exists() else None
    assert path.read_bytes() == blob
    return sha(path)


def prepare():
    sources(); assert not (HERE / 'pool.json').exists()
    spec = importlib.util.spec_from_file_location('early_public_source', SOURCE)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    opening = module._DATA['opening'][:72]
    unique, groups = {}, {}
    for rid, actions in sorted(module._DATA['routes'].items(), key=lambda item: int(item[0])):
        assert len(actions) == 719 and actions[:72] == opening
        unique.setdefault(action_hash(actions), (rid, actions))
    for rid, actions in unique.values():
        group = action_hash(actions[:144]); groups.setdefault(group, []).append((rid, actions))
    assert len(unique) == 91 and len(groups) == 10
    representatives = []
    for prefix, routes in sorted(groups.items()):
        vectors = {rid: [action_hash([a.get('farmer', []), a.get('hands', [])]) for a in acts] for rid, acts in routes}
        scores = {rid: sum(sum(a != b for a, b in zip(vector, other)) for other in vectors.values())
                  for rid, vector in vectors.items()}
        rid = min(scores, key=lambda r: (scores[r], int(r)))
        representatives.append(dict(route=rid, prefix144_sha256=prefix, medoid_distance=scores[rid],
                                    group_size=len(routes), group_routes=sorted(scores, key=int),
                                    action_sha256=action_hash(module._DATA['routes'][rid])))
    all_targets = read(TARGETS); fixtures = all_targets['live_losses'] + all_targets['current_top20']
    full = read(FULL); assert full['passed'] and full['complete']
    controls = {(r['rival'], r['candidate_seat']): r for r in full['games'] if r['version'] == 'integrated'}
    assert len(controls) == 100
    by_shop, targets_by_shop = {}, {}
    for fixture in fixtures:
        fid = fixture['fixture_id']
        shops = {controls[(fid, seat)]['candidate_telemetry']['guard_route_pair144'].split('|')[0] for seat in (0, 1)}
        assert len(shops) == 1
        shop = next(iter(shops)); by_shop.setdefault(shop, []).append(fixture)
        if fid.startswith('live-') and fid != 'live-114283577' and any(controls[(fid, seat)]['result'] != 'win' for seat in (0, 1)):
            targets_by_shop.setdefault(shop, []).append(fid)
    assert len(targets_by_shop) == 7 and sum(map(len, targets_by_shop.values())) == 16
    variants = []; (HERE / 'candidates').mkdir(exist_ok=True)
    for shop in sorted(targets_by_shop):
        for rep in sorted(representatives, key=lambda x: int(x['route'])):
            version = shop + '_' + rep['route']; path = HERE / 'candidates' / (version + '.py')
            variants.append(dict(version=version, shop=shop, route=rep['route'], candidate=str(path),
                                 candidate_sha256=candidate({shop: int(rep['route'])}, path)))
    bindings = dict(source_sha256=SOURCE_SHA, source_full_sha256=FULL_SHA, target_sha256=TARGETS_SHA,
                    helper_sha256=sha(__file__), layer_sha256=sha(HERE / 'layer.py'),
                    plan_sha256=sha(HERE / 'PLAN.md'),
                    fast_sha256=sha(ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py'),
                    core_sha256=sha(ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py'))
    write(HERE / 'pool.json', dict(created_at_utc=now(), **bindings, representatives=representatives,
                                  fixtures=by_shop, target_ids=targets_by_shop, variants=variants))
    print(json.dumps(dict(variants=len(variants), target_games=320, representatives=representatives), indent=2), flush=True)


def context():
    sources(); pool = read(HERE / 'pool.json')
    for field, path in (('helper_sha256', Path(__file__)), ('layer_sha256', HERE / 'layer.py'),
                        ('plan_sha256', HERE / 'PLAN.md'),
                        ('fast_sha256', ROOT / 'diagnostics/physical_route_rollout_20260928/fast_game.py'),
                        ('core_sha256', ROOT / 'diagnostics/physical_route_rollout_20260928/native_core.py')):
        assert pool[field] == sha(path), field
    for variant in pool['variants']:
        assert sha(variant['candidate']) == variant['candidate_sha256']
    return pool


def jobs(pool, phase):
    if phase == 'target':
        variants = pool['variants']
    else:
        shortlist = read(HERE / 'shortlist.json')
        assert shortlist['complete'] and shortlist['passed'] and shortlist['pool_sha256'] == sha(HERE / 'pool.json')
        assert shortlist['target_sha256'] == sha(HERE / 'target.json')
        variants = [v for v in pool['variants'] if v['version'] in shortlist['versions']]
    result = []
    for variant in variants:
        for fixture in pool['fixtures'][variant['shop']]:
            target = fixture['fixture_id'] in pool['target_ids'][variant['shop']]
            if target == (phase == 'target'):
                result.extend((variant, fixture, seat) for seat in (0, 1))
    if phase == 'target': assert len(result) == 320
    return result


def validate(row, job):
    variant, fixture, seat = job
    assert key(row) == (variant['version'], fixture['fixture_id'], seat)
    assert row['candidate_sha256'] == variant['candidate_sha256']
    assert row['pool_sha256'] == sha(HERE / 'pool.json') and row['helper_sha256'] == sha(__file__)
    assert row['frames'] == 720 and row['candidate_status'] == row['opponent_status'] == 'DONE'
    assert not row['candidate_errors']
    telemetry = row['candidate_telemetry']
    assert telemetry['early_public_shop72'] == variant['shop']
    assert telemetry['early_public_turns'] == 647 and telemetry['early_public_route'] == variant['route']


def run(phase):
    pool = context(); todo = jobs(pool, phase); expected = {(v['version'], f['fixture_id'], s): (v, f, s) for v, f, s in todo}
    destination = HERE / (phase + '.json'); assert not destination.exists()
    ledger = HERE / (phase + '.jsonl'); rows = []
    if ledger.exists():
        for line in ledger.read_text(encoding='utf-8').splitlines():
            row = json.loads(line); validate(row, expected[key(row)]); rows.append(row)
    done = {key(r) for r in rows}; assert len(done) == len(rows)
    print(f'{phase}: {len(rows)}/{len(todo)} available; one sequential worker', flush=True)
    with ledger.open('a', encoding='utf-8') as output:
        for variant, fixture, seat in todo:
            if (variant['version'], fixture['fixture_id'], seat) in done: continue
            row = play(fixture, variant['candidate'], variant['candidate_sha256'], seat)
            row.update(version=variant['version'], shop=variant['shop'], route=variant['route'], team=fixture['team'],
                       pool_sha256=sha(HERE / 'pool.json'), helper_sha256=sha(__file__))
            validate(row, (variant, fixture, seat))
            output.write(json.dumps(row, ensure_ascii=False) + '\n'); output.flush(); rows.append(row)
            print(f'{phase} {len(rows)}/{len(todo)} {variant["version"]} {fixture["team"]} seat{seat}: {row["result"]} {row["margin"]:+.0f}', flush=True)
    write(destination, dict(complete=True, clean=True, completed_at_utc=now(), pool_sha256=sha(HERE / 'pool.json'),
                            helper_sha256=sha(__file__), game_count=len(rows), games=sorted(rows, key=key)))


def metrics(rows):
    ids = {r['fixture_id'] for r in rows}
    return dict(sweeps=sum(all(r['result'] == 'win' for r in rows if r['fixture_id'] == fid) for fid in ids),
                points=sum(points(r) for r in rows), margin=sum(r['margin'] for r in rows))


def shortlist():
    pool = context(); target = read(HERE / 'target.json')
    assert target['complete'] and target['clean'] and target['game_count'] == 320
    selected, summaries = [], []
    for shop in sorted(pool['target_ids']):
        candidates = []
        for variant in (v for v in pool['variants'] if v['shop'] == shop):
            rows = [r for r in target['games'] if r['version'] == variant['version']]
            score = dict(version=variant['version'], shop=shop, route=variant['route'], **metrics(rows)); summaries.append(score)
            if score['sweeps'] > 0: candidates.append(score)
        candidates.sort(key=lambda c: (-c['sweeps'], -c['points'], -c['margin'], int(c['route'])))
        selected.extend(c['version'] for c in candidates[:2])
    write(HERE / 'shortlist.json', dict(complete=True, passed=bool(selected), completed_at_utc=now(),
         pool_sha256=sha(HERE / 'pool.json'), target_sha256=sha(HERE / 'target.json'), versions=selected, summaries=summaries))
    print(json.dumps(dict(selected=selected), indent=2), flush=True)


def select():
    pool = context(); target = read(HERE / 'target.json'); retention = read(HERE / 'retention.json'); short = read(HERE / 'shortlist.json')
    assert retention['complete'] and retention['clean']
    control = {(r['rival'], r['candidate_seat']): r for r in read(FULL)['games'] if r['version'] == 'integrated'}
    candidates, replacements, summaries = {}, {}, []
    for variant in (v for v in pool['variants'] if v['version'] in short['versions']):
        rows = [r for r in target['games'] + retention['games'] if r['version'] == variant['version']]
        assert len(rows) == 2 * len(pool['fixtures'][variant['shop']])
        regressions = [key(r) for r in rows if r['result'] != 'win' and control[(r['fixture_id'], r['candidate_seat'])]['result'] == 'win']
        loss_rows = [r for r in rows if r['fixture_id'].startswith('live-')]
        score = dict(version=variant['version'], shop=variant['shop'], route=variant['route'], regressions=regressions,
                     **metrics(rows), public_sweeps=metrics(loss_rows)['sweeps'],
                     delta_margin=sum(r['margin'] - control[(r['fixture_id'], r['candidate_seat'])]['margin'] for r in rows))
        summaries.append(score)
        if not regressions: candidates.setdefault(variant['shop'], []).append(score)
    for shop, options in candidates.items():
        options.sort(key=lambda x: (-x['sweeps'], -x['public_sweeps'], -x['points'], -x['delta_margin'], int(x['route'])))
        replacements[shop] = int(options[0]['route'])
    result = dict(complete=True, passed=bool(replacements), completed_at_utc=now(), pool_sha256=sha(HERE / 'pool.json'),
                  target_sha256=sha(HERE / 'target.json'), retention_sha256=sha(HERE / 'retention.json'),
                  replacements=replacements, summaries=summaries)
    if replacements:
        path = HERE / 'candidate_selected.py'; digest = candidate(replacements, path)
        backup = HERE / ('main_candidate_early_public_' + digest[:8] + '.py'); backup.write_bytes(path.read_bytes())
        result.update(candidate=str(path), candidate_sha256=digest, backup=str(backup))
    write(HERE / 'selection.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'summaries'}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['prepare', 'target', 'shortlist', 'retention', 'select'])
    phase = parser.parse_args().phase
    with exclusive_run(HERE / ('research_' + phase + '.lock')):
        if phase == 'prepare': prepare()
        elif phase == 'shortlist': shortlist()
        elif phase == 'select': select()
        else: run(phase)


if __name__ == '__main__': main()
