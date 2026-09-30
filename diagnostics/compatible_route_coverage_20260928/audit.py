"""Offline coverage inventory; no candidate outcomes or source changes."""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    source = ROOT / 'main.py'
    source_sha = '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
    cohort_path = ROOT / 'diagnostics/new_live_56609430_20260927/cohort_180951.json'
    features_path = ROOT / 'diagnostics/new_live_56609430_20260927/structural_audit/features.json'
    assessment_path = ROOT / 'diagnostics/current_top20_20260927_172258/assessment.json'
    assert sha(source) == source_sha
    assert sha(cohort_path) == '2e37cf158c4e28edcc3e044c6b7d3fd84d4bfc5a983b31e1aeeee5a2986f0116'
    assert sha(features_path) == '0b608492da8038f147cea29c3dbc994782d8386c088ddfe2ed76e1761339ad18'
    assert sha(assessment_path) == '9d328af8115e27acb45fd4251a1bbc1fde5fda8c793c027b46792a54c04cbeb7'
    spec = importlib.util.spec_from_file_location('route_coverage_4ee', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    data = module._DATA
    cohort = json.loads(cohort_path.read_text(encoding='utf-8'))
    features = {r['episode_id']: r for r in json.loads(features_path.read_text(encoding='utf-8'))['rows']}
    assessment = json.loads(assessment_path.read_text(encoding='utf-8'))
    groups = defaultdict(lambda: dict(live_losses=[], live_wins=[], top20=[]))
    for row in cohort['games']:
        if row['episode_id'] in features:
            feature = features[row['episode_id']]
            assert feature['replay_sha256'] == row['replay_sha256']
            shops = feature['periods']['144']['shops']
        else:
            raw = gzip.decompress(Path(row['replay_path']).read_bytes())
            assert hashlib.sha256(raw).hexdigest() == row['replay_sha256']
            replay = json.loads(raw)
            shops = replay['steps'][144][row['candidate_seat']]['observation'].get('town', replay['steps'][144][0]['observation']['town'])['unlocked_shops']
            del replay, raw
        assert len(shops) == 2
        groups['|'.join(shops)]['live_'+('wins' if row['result']=='win' else 'losses')].append(
            dict(fixture_id='live-'+str(row['episode_id']), team=row['opponent'], margin=row['margin']))
    top_pairs = defaultdict(list)
    for row in assessment['games']:
        top_pairs[row['team_id']].append(row)
    assert len(top_pairs) == 20
    for rows in top_pairs.values():
        assert len(rows) == 2 and rows[0]['candidate_capture']['shops'] == rows[1]['candidate_capture']['shops']
        row = rows[0]
        groups['|'.join(row['candidate_capture']['shops'])]['top20'].append(dict(
            team=row['team'], episode_id=row['episode_id'], both_seat_win=all(r['result']=='win' for r in rows)))
    for pair, group in groups.items():
        first_route = data['route_map'].get(pair.split('|')[0], next(iter(data['routes'])))
        prefix = data['opening'][:72] + data['routes'][str(first_route)][72:144]
        unique = {}
        for route, actions in sorted(data['routes'].items()):
            if actions[:144] == prefix:
                digest = hashlib.sha256(json.dumps(actions,sort_keys=True,separators=(',', ':')).encode()).hexdigest()
                unique.setdefault(digest, route)
        group['compatible_unique_routes'] = list(unique.values())
        group['current_day6_route'] = data['route_map'].get(pair, first_route)
        group['live_loss_count'] = len(group['live_losses'])
        group['live_win_count'] = len(group['live_wins'])
        group['top20_failure_count'] = sum(not r['both_seat_win'] for r in group['top20'])
        group['top20_win_count'] = sum(r['both_seat_win'] for r in group['top20'])
    result = dict(completed_at_utc=datetime.now(timezone.utc).isoformat(),source_sha256=source_sha,
        cohort_sha256=sha(cohort_path),features_sha256=sha(features_path),assessment_sha256=sha(assessment_path),
        scope='Existing observations and outcomes only; no candidate tested. Live shop coverage is from the original seat.',
        groups=dict(sorted(groups.items(),key=lambda kv:(-kv[1]['live_loss_count'],kv[0]))))
    (HERE/'coverage.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    for pair, group in result['groups'].items():
        print(pair, 'losses',group['live_loss_count'],'public wins',group['live_win_count'],
              'top20 W/L',group['top20_win_count'],group['top20_failure_count'],
              'compatible routes',len(group['compatible_unique_routes']))
    assert sha(source) == source_sha


if __name__ == '__main__':
    main()
