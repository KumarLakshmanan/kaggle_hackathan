"""Summarize paired native outcomes from the frozen 18-loss tape panel."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent


def score(result):
    return {'win': 1.0, 'draw': 0.5, 'loss': 0.0}[result]


def wdl(rows):
    counts = Counter(row['result'] for row in rows)
    return dict(wins=counts['win'], draws=counts['draw'], losses=counts['loss'])


def main():
    result_path = HERE / 'results.json'
    data = json.loads(result_path.read_text(encoding='utf8'))
    manifest = json.loads((HERE / 'manifest.json').read_text(encoding='utf8'))
    assert data['complete'] and data['all_done_720'] and data['original_seat_cash_parity'], data['errors']
    games = data['games']
    by_key = {(g['episode_id'], g['tested_seat'], g['version']): g for g in games}
    assert len(by_key) == 72
    pairs = []
    for source in manifest['rows']:
        for seat in (0, 1):
            old = by_key[source['episode_id'], seat, 'c68']
            new = by_key[source['episode_id'], seat, '4ee']
            pairs.append(dict(episode_id=source['episode_id'], opponent=source['opponent'],
                              source_seat=source['live_candidate_seat'], tested_seat=seat,
                              original_seat=(seat == source['live_candidate_seat']),
                              live_margin=source['live_margin'],
                              c68_result=old['result'], c68_margin=old['margin'],
                              c68_own_cash=old['candidate_reward'], c68_opponent_cash=old['opponent_reward'],
                              new_result=new['result'], new_margin=new['margin'],
                              new_own_cash=new['candidate_reward'], new_opponent_cash=new['opponent_reward'],
                              new_minus_c68_win_points=score(new['result']) - score(old['result']),
                              new_minus_c68_margin=new['margin'] - old['margin'],
                              new_minus_c68_own_cash=new['candidate_reward'] - old['candidate_reward'],
                              new_minus_c68_opponent_cash=new['opponent_reward'] - old['opponent_reward']))
    paired = {}
    for label, rows in [('all', pairs), ('original_seat', [p for p in pairs if p['original_seat']]),
                        ('swapped_seat', [p for p in pairs if not p['original_seat']])]:
        scores = [p['new_minus_c68_win_points'] for p in rows]
        margins = [p['new_minus_c68_margin'] for p in rows]
        paired[label] = dict(pairs=len(rows),
                             c68_wdl=wdl([by_key[p['episode_id'], p['tested_seat'], 'c68'] for p in rows]),
                             new_wdl=wdl([by_key[p['episode_id'], p['tested_seat'], '4ee'] for p in rows]),
                             new_minus_c68_win_points=sum(scores),
                             better_results=sum(x > 0 for x in scores),
                             worse_results=sum(x < 0 for x in scores),
                             equal_results=sum(x == 0 for x in scores),
                             new_minus_c68_total_margin=sum(margins),
                             new_minus_c68_mean_margin=statistics.fmean(margins),
                             new_minus_c68_median_margin=statistics.median(margins),
                             new_minus_c68_mean_own_cash=statistics.fmean(p['new_minus_c68_own_cash'] for p in rows),
                             new_minus_c68_mean_opponent_cash=statistics.fmean(p['new_minus_c68_opponent_cash'] for p in rows))
    sweeps = {}
    for version in ('c68', '4ee'):
        sweeps[version] = sum(all(by_key[source['episode_id'], seat, version]['result'] == 'win' for seat in (0, 1))
                              for source in manifest['rows'])
    summary = dict(completed_at_utc=datetime.now(timezone.utc).isoformat(),
                   manifest_path=str((HERE / 'manifest.json').resolve()),
                   results_path=str(result_path.resolve()),
                   cases=18, games=72, all_done_720=True, original_seat_cash_parity=True,
                   paired=paired, both_seat_sweeps=sweeps, pairs=pairs,
                   interpretation='Fixed opponent actions, selected from 4ee live losses; diagnostic only, not reactive strength validation.')
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf8')
    lines = ['# c68 versus 4ee on 18 new live-loss tapes', '',
             'Frozen inputs: `manifest.json`; full game outcomes: `results.json`; paired deltas: `summary.json`.',
             'All 18 episodes are losses from the complete 16:41 UTC live cohort. Each opponent action sequence has 719 moves.',
             'A later 16:53 UTC live extension added one loss after this diagnostic panel was frozen; it is outside these 18 cases.',
             'Each agent was run in both seats at the recorded seed with native shops: **72 games**, all DONE/DONE/720.',
             'The 4ee original-seat reruns reproduce both Kaggle cash totals in all 18 episodes.', '',
             '| Seat panel | c68 W/D/L | 4ee W/D/L | 4ee − c68 win points | Better / worse / same results | Mean relative-cash change |',
             '|---|---:|---:|---:|---:|---:|']
    for label in ('original_seat', 'swapped_seat', 'all'):
        row = paired[label]
        a, b = row['c68_wdl'], row['new_wdl']
        lines.append(f"| {label.replace('_', ' ')} | {a['wins']}/{a['draws']}/{a['losses']} | "
                     f"{b['wins']}/{b['draws']}/{b['losses']} | {row['new_minus_c68_win_points']:+g} | "
                     f"{row['better_results']}/{row['worse_results']}/{row['equal_results']} | "
                     f"{row['new_minus_c68_mean_margin']:+,.0f} |")
    lines += ['', f"Both-seat sweeps over 18 sources: c68 **{sweeps['c68']}**, 4ee **{sweeps['4ee']}**.",
              'Relative-cash change is (4ee own − 4ee rival) − (c68 own − c68 rival) on the same tape, seed, and seat.',
              'The `summary.json` ledger also separates own-cash and opponent-cash changes.', '',
              '| Episode | Opponent | Source seat | c68 original | 4ee original | c68 swapped | 4ee swapped |',
              '|---:|---|---:|---|---|---|---|']
    for source in manifest['rows']:
        orig = next(p for p in pairs if p['episode_id'] == source['episode_id'] and p['original_seat'])
        swapped = next(p for p in pairs if p['episode_id'] == source['episode_id'] and not p['original_seat'])
        opponent = str(source['opponent']).replace('|', '\\|')
        def fmt(p, version):
            return f"{p[version + '_result']} {p[version + '_margin']:+,.0f}"
        lines.append(f"| {source['episode_id']} | {opponent} | {source['live_candidate_seat']} | "
                     f"{fmt(orig, 'c68')} | {fmt(orig, 'new')} | {fmt(swapped, 'c68')} | {fmt(swapped, 'new')} |")
    lines += ['', '**Decision:** retain this as a counterfactual diagnostic. The opponent moves are fixed from games that 4ee lost; the opponents cannot react to c68 or a seat swap. No policy promotion or Kaggle upload follows from these results.', '']
    (HERE / 'RESULTS.md').write_text('\n'.join(lines), encoding='utf8')
    print(json.dumps(dict(paired=paired, both_seat_sweeps=sweeps), ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
