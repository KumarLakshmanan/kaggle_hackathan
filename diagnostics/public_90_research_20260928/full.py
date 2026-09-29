"""Verify the exact combined candidate on all50 frozen targets."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.public_90_research_20260928.research import (
    context, read, write, now, sha, SOURCE_SHA, FULL, play, exclusive_run)


def main():
    pool = context(); selection = read(HERE / 'selection.json')
    assert selection['complete'] and selection['passed']
    assert selection['pool_sha256'] == sha(HERE / 'pool.json')
    assert sha(selection['candidate']) == sha(selection['backup']) == selection['candidate_sha256']
    controls = {(r['rival'], r['candidate_seat']): r for r in read(FULL)['games'] if r['version'] == 'integrated'}
    components = read(HERE / 'target.json')['games'] + read(HERE / 'retention.json')['games']
    destination = HERE / 'combined_full.json'; assert not destination.exists()
    ledger = HERE / 'combined_full.jsonl'; rows = []
    if ledger.exists():
        rows = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()]
    done = {(r['fixture_id'], r['candidate_seat']) for r in rows}; assert len(done) == len(rows)
    def validate(row):
        assert row['candidate_sha256'] == selection['candidate_sha256']
        assert row['selection_sha256'] == sha(HERE / 'selection.json') and row['helper_sha256'] == sha(__file__)
        assert row['candidate_status'] == row['opponent_status'] == 'DONE' and row['frames'] == 720 and not row['candidate_errors']
        fid, seat = row['fixture_id'], row['candidate_seat']; base = controls[(fid, seat)]
        shop = base['candidate_telemetry']['guard_route_pair144'].split('|')[0]
        route = selection['replacements'].get(shop)
        if route is None:
            expected = base
        else:
            expected = next(r for r in components if r['version'] == shop + '_' + str(route)
                            and r['fixture_id'] == fid and r['candidate_seat'] == seat)
        assert row['candidate_reward'] == expected['candidate_reward'] and row['opponent_reward'] == expected['opponent_reward']
        assert base['result'] != 'win' or row['result'] == 'win'
    for row in rows: validate(row)
    with ledger.open('a', encoding='utf-8') as output:
        for shop, fixtures in sorted(pool['fixtures'].items()):
            for fixture in fixtures:
                for seat in (0, 1):
                    if (fixture['fixture_id'], seat) in done: continue
                    row = play(fixture, selection['candidate'], selection['candidate_sha256'], seat)
                    row.update(selection_sha256=sha(HERE / 'selection.json'), helper_sha256=sha(__file__), team=fixture['team'])
                    validate(row); output.write(json.dumps(row, ensure_ascii=False) + '\n'); output.flush(); rows.append(row)
                    print(f'full {len(rows)}/100 {fixture["team"]} seat{seat} {row["result"]} {row["margin"]:+.0f}', flush=True)
    assert len(rows) == 100
    summaries = []
    for prefix, count in [('live-', 30), ('top20-', 20)]:
        subset = [r for r in rows if r['fixture_id'].startswith(prefix)]
        ids = sorted({r['fixture_id'] for r in subset}); assert len(ids) == count
        sweeps = [fid for fid in ids if all(r['result'] == 'win' for r in subset if r['fixture_id'] == fid)]
        summaries.append(dict(panel=prefix, fixtures=count, both_seat_wins=len(sweeps), won_fixtures=sweeps,
                              WDL=[sum(r['result'] == x for r in subset) for x in ('win','draw','loss')]))
    assert summaries[0]['both_seat_wins'] > 13 and summaries[1]['both_seat_wins'] >= 19
    write(destination, dict(complete=True, passed=True, clean=True, completed_at_utc=now(),
                           source_sha256=SOURCE_SHA, candidate_sha256=selection['candidate_sha256'],
                           selection_sha256=sha(HERE / 'selection.json'), helper_sha256=sha(__file__),
                           summaries=summaries, games=rows))
    print(json.dumps(summaries, indent=2), flush=True)


if __name__ == '__main__':
    with exclusive_run(HERE / 'combined_full.lock'): main()
