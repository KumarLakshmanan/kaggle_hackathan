"""Derive a paired comparison only after the frozen full receipt is complete."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.public_90_research_20260928.research import read, write, sha, now, FULL, SOURCE_SHA


def main():
    full = read(HERE / 'combined_full.json')
    selection = read(HERE / 'selection.json')
    assert full['complete'] and full['passed'] and full['clean']
    assert full['source_sha256'] == SOURCE_SHA
    assert full['candidate_sha256'] == selection['candidate_sha256']
    assert full['selection_sha256'] == sha(HERE / 'selection.json')
    assert sha(selection['candidate']) == sha(selection['backup']) == full['candidate_sha256']
    source = {(r['rival'], r['candidate_seat']): r for r in read(FULL)['games'] if r['version'] == 'integrated'}
    games = {(r['fixture_id'], r['candidate_seat']): r for r in full['games']}
    assert len(source) == len(games) == 100 and set(source) == set(games)
    fixtures = []
    for fid in sorted({key[0] for key in games}):
        base = [source[(fid, seat)] for seat in (0, 1)]
        test = [games[(fid, seat)] for seat in (0, 1)]
        source_sweep = all(r['result'] == 'win' for r in base)
        candidate_sweep = all(r['result'] == 'win' for r in test)
        assert all(b['result'] != 'win' or t['result'] == 'win' for b, t in zip(base, test))
        fixtures.append(dict(
            fixture_id=fid, team=test[0]['team'],
            source_sweep=source_sweep, candidate_sweep=candidate_sweep,
            newly_won=candidate_sweep and not source_sweep,
            source_margins=[r['margin'] for r in base], candidate_margins=[r['margin'] for r in test],
            delta_own=[t['candidate_reward'] - b['candidate_reward'] for b, t in zip(base, test)],
            delta_rival=[t['opponent_reward'] - b['opponent_reward'] for b, t in zip(base, test)],
            delta_margin=[t['margin'] - b['margin'] for b, t in zip(base, test)],
            source_results=[r['result'] for r in base], candidate_results=[r['result'] for r in test],
        ))
    result = dict(
        complete=True, diagnostic_only=True, created_at_utc=now(),
        source_sha256=SOURCE_SHA, candidate_sha256=full['candidate_sha256'],
        source_full_sha256=sha(FULL), combined_full_sha256=sha(HERE / 'combined_full.json'),
        helper_sha256=sha(__file__), source_winning_seats=sum(r['result'] == 'win' for r in source.values()),
        candidate_winning_seats=sum(r['result'] == 'win' for r in games.values()),
        lost_source_winning_seats=0, newly_won_fixtures=[r['fixture_id'] for r in fixtures if r['newly_won']],
        total_delta_margin=sum(sum(r['delta_margin']) for r in fixtures), fixtures=fixtures,
    )
    write(HERE / 'paired_comparison.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'fixtures'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
