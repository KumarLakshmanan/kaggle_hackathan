"""Evaluate only the already frozen full-stage criteria."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import json
import hashlib

HERE = Path(__file__).resolve().parent


def read(name): return json.loads((HERE/name).read_text(encoding='utf-8'))
def digest(name): return hashlib.sha256((HERE/name).read_bytes()).hexdigest()


def main():
    pool = read('pool.json'); controls = read('controls.json')
    conditional = read('conditional.json'); selection = read('selection.json'); full = read('full.json')
    for receipt in (controls, conditional, selection, full):
        assert receipt['complete'] and receipt['pool_sha256'] == digest('pool.json')
    assert selection['conditional_sha256'] == digest('conditional.json')
    assert selection['controls_sha256'] == digest('controls.json')
    summaries = []
    for candidate in selection['combined']:
        rows = [r for r in full['games'] if r['version'] == candidate['version']]
        assert len(rows) == 100 and len({(r['fixture_id'],r['candidate_seat']) for r in rows}) == 100
        pairs = {fid: [r for r in rows if r['fixture_id']==fid] for fid in {r['fixture_id'] for r in rows}}
        counts = {panel: sum(all(r['result']=='win' for r in pair) for fid,pair in pairs.items() if fid.startswith(prefix))
                  for panel,prefix in (('public30','live-'),('top20','top20-'))}
        regressions = [dict(fixture_id=r['fixture_id'],seat=r['candidate_seat'],source_margin=r['parent_margin'],
                            margin=r['margin'],delta_own=r['delta_own'],delta_rival=r['delta_rival'])
                       for r in rows if r['parent_result']=='win' and r['result']!='win']
        rescues = sorted(fid for fid,pair in pairs.items() if fid.startswith('live-') and all(r['result']=='win' for r in pair)
                         and any(r['parent_result']!='win' for r in pair))
        clean = all(r['clean'] and r['activation_passed'] for r in rows)
        passed = clean and not regressions and counts['public30']>=14 and counts['top20']>=18
        summaries.append(dict(version=candidate['version'],candidate=candidate['candidate'],candidate_sha256=candidate['candidate_sha256'],
                              clean=clean,passed=passed,both_seat_wins=counts,new_public_rescues=rescues,regressions=regressions,
                              points=sum({'win':1,'draw':.5,'loss':0}[r['result']] for r in rows),
                              delta_margin=sum(r['delta_margin'] for r in rows),rules=candidate['rules']))
    eligible = sorted([s for s in summaries if s['passed']],key=lambda s:(-s['both_seat_wins']['public30'],
                      -s['both_seat_wins']['top20'],-s['points'],-s['delta_margin'],s['version']!='production'))
    decision = dict(complete=True,diagnostic_only=True,pool_sha256=digest('pool.json'),full_sha256=digest('full.json'),
                    conditional_sha256=digest('conditional.json'),controls_sha256=digest('controls.json'),
                    passed=bool(eligible),selected_version=eligible[0]['version'] if eligible else None,summaries=summaries,
                    created_at_utc=datetime.now(timezone.utc).isoformat())
    with (HERE/'decision.json').open('x',encoding='utf-8') as stream: json.dump(decision,stream,indent=2,ensure_ascii=False)
    lines=['# Production-leaf selector results — 28 September 2026','','Source 367 sweeps 19/20 saved top fixtures and 13/30 frozen public-loss fixtures. '
           'This separate study fit exactly two coarse public-production selectors to the existing 320 medoid development outcomes. '
           'Every shortlisted route then faced all affected source-winning controls before selection. '
           'Saved tapes are development evidence; native/reacting qualification remains separate.','',
           f"The frozen pool contains {len(pool['candidates'])} candidates, {pool['source_control_games']} fresh exact 367 public-win control games, "
           f"{pool['conditional_games']} conditional games and {len(full['games'])} exact combined target games.",'',
           '| Combined arm | Top sweeps | Public-loss sweeps | Source winning seats lost | Clean | Decision |',
           '| --- | ---: | ---: | ---: | --- | --- |']
    for s in summaries:
        lines.append(f"| {s['version']} | {s['both_seat_wins']['top20']}/20 | {s['both_seat_wins']['public30']}/30 | "
                     f"{len(s['regressions'])} | {s['clean']} | {'Advance further research' if s['passed'] else 'Reject'} |")
    if not summaries: lines += ['No one-leaf candidate survived complete source-win preservation; no combined policy was generated.']
    lines += ['', 'Selected development arm: '+str(decision['selected_version'])+'.', '', '## Every conditional leaf decision', '',
              '| Arm | Leaf | Route | Result | New development rescues | Lost source-winning seats |',
              '| --- | --- | ---: | --- | --- | ---: |']
    for s in selection['summaries']:
        lines.append(f"| {s['arm']} | {s['leaf'].replace('|',' / ')} | {s['route']} | "
                     f"{'Eligible' if s['passed'] else 'Rejected'} | {', '.join(s['actual_development']['rescues'])} | {len(s['regressions'])} |")
    lines += ['', 'Every rejected source-winning seat, its own/rival cash changes and all candidate outcomes remain in selection.json and conditional.json. '
              'The unchanged source is retained wherever the frozen shortlist fails. No routes were added after outcomes.', '',
              '## Fresh source public-win controls', '']
    source_counts = Counter(r['result'] for r in controls['games'])
    lines += [f"Exact 367 fresh controls: {dict(source_counts)} across {len(controls['games'])} seats. These controls cover only the affected "
              'public-win fixtures; they do not establish whole 54-panel performance. Historical 4ee rewards were never substituted for source outcomes.', '']
    for s in summaries:
        lines += ['## '+s['version'],'','Exact candidate SHA-256: `'+s['candidate_sha256']+'`.','',
                  'New public both-seat rescues: '+(', '.join(s['new_public_rescues']) or 'none')+'.','',
                  '| Fixture | Seat | Source margin | Candidate margin | Own change | Rival change |',
                  '| --- | ---: | ---: | ---: | ---: | ---: |']
        for r in sorted([r for r in full['games'] if r['version']==s['version']],key=lambda r:(r['fixture_id'],r['candidate_seat'])):
            lines.append(f"| {r['fixture_id']} | {r['candidate_seat']} | {r['parent_margin']:.0f} | {r['margin']:.0f} | "
                         f"{r['delta_own']:.0f} | {r['delta_rival']:.0f} |")
        lines += ['']
    lines += ['## Decision limits','','No root source/main files were edited and no Kaggle access/upload occurred. '
              'This study does not integrate the separate animal-liquidity repair or later91-route screen. '
              'Original-framework parity, all54 public-win preservation, fresh reacting opponents and both-seat file-loader '
              'checks remain necessary before promotion. No leaderboard score or universal win is inferred.', '',
              'Decision SHA-256: `'+digest('decision.json')+'`.',
              'Full receipt SHA-256: `'+digest('full.json')+'`.', '']
    (HERE/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({k:v for k,v in decision.items() if k!='summaries'},indent=2))
    for s in summaries: print(s['version'],s['both_seat_wins'],s['passed'],len(s['regressions']))


if __name__=='__main__': main()
