"""Every saved opponent's paired outcome and coin-margin change."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    rows = [json.loads(s) for s in (HERE/'top100_results.jsonl').read_text().splitlines()]
    by_team = {}
    for row in rows:
        by_team.setdefault(row['team'], {}).setdefault(row['version'], {})[row['candidate_seat']] = row
    table = []
    for team, versions in by_team.items():
        if set(versions) != {'baseline', 'candidate'} or any(set(v) != {0, 1} for v in versions.values()): continue
        a, b = versions['baseline'], versions['candidate']
        table.append({'rank': a[0]['rank'], 'team': team, 'episode_id': a[0]['episode_id'],
            'baseline_seat0': a[0]['result'], 'baseline_seat1': a[1]['result'],
            'candidate_seat0': b[0]['result'], 'candidate_seat1': b[1]['result'],
            'baseline_mean_margin': (a[0]['margin']+a[1]['margin'])/2,
            'candidate_mean_margin': (b[0]['margin']+b[1]['margin'])/2,
            'paired_mean_margin_gain': (b[0]['margin']+b[1]['margin']-a[0]['margin']-a[1]['margin'])/2,
            'wins_gained': sum(b[s]['result'] == 'win' and a[s]['result'] != 'win' for s in (0, 1)),
            'wins_lost': sum(a[s]['result'] == 'win' and b[s]['result'] != 'win' for s in (0, 1))})
    table.sort(key=lambda r:r['rank'])
    with (HERE/'TOP100_PAIRED.csv').open('w', newline='', encoding='utf-8-sig') as out:
        writer = csv.DictWriter(out, fieldnames=list(table[0])); writer.writeheader(); writer.writerows(table)
    text = ['# Saved top100 paired comparison', '', 'September29 saved snapshot; fixed action tapes, correlated episodes. This is not a current/live leaderboard check.', '',
        '| Rank | Team | Previous seats0/1 | Candidate seats0/1 | Previous margin | Candidate margin | Paired gain |', '|---:|---|---|---|---:|---:|---:|']
    for r in table:
        team = r['team'].replace('|', '\\|')
        text.append(f'| {r["rank"]} | {team} | {r["baseline_seat0"]}/{r["baseline_seat1"]} | {r["candidate_seat0"]}/{r["candidate_seat1"]} | {r["baseline_mean_margin"]:.0f} | {r["candidate_mean_margin"]:.0f} | {r["paired_mean_margin_gain"]:+.0f} |')
    (HERE/'TOP100_PAIRED.md').write_text('\n'.join(text)+'\n', encoding='utf-8')
    print(json.dumps({'teams': len(table), 'wins_gained': sum(r['wins_gained'] for r in table),
        'wins_lost': sum(r['wins_lost'] for r in table), 'mean_paired_margin_gain': sum(r['paired_mean_margin_gain'] for r in table)/len(table)}, indent=2))


if __name__ == '__main__': main()
