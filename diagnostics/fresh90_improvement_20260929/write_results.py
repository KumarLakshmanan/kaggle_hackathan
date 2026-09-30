"""Create a readable evidence index after the bounded qualification run."""
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from run_panel import HERE, ROOT, sha

def read(name):
    path = HERE / name
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None

def link(label, path):
    return f'[{label}]({Path(path).resolve().as_posix()})'

manifest = read('combined_v2_manifest.json')
candidate = Path(manifest['candidate'])
assert sha(candidate) == manifest['candidate_sha256']
assert sha(ROOT / 'main.py') == '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
lines = ['# Fresh-replay improvement results', '',
    'Research snapshot: official leaderboard of **2026-09-29 17:04:23 UTC (22:34:23 IST)**. '
    'Downloaded the latest three eligible completed public episodes per top100 team, '
    'plus all27 then-available completed episodes for uploaded submission56680167. '
    'There are267 unique replay archives (240 top100 episodes and27 submission episodes), '
    'with provenance and hashes in ' + link('collection folder', ROOT / 'diagnostics/fresh90_refresh_20260929') + '.', '',
    'The comparison baseline is the exact uploaded **cb76fbc4** source. The retained '
    'latest-panel development candidate is **4802aa95**, kept as a separate experimental file. '
    'Root main.py remains **4eeac9c3**. No upload was made in this research task.', '',
    '## Measured replay results', '',
    '| Panel | Baseline wins | Candidate wins | Candidate both-seat teams | Added / lost winning seats |',
    '|---|---:|---:|---:|---:|']
comparisons = {}
for panel, title in [('top100', 'Newest top100'), ('public27', 'All27 uploaded-submission opponent tapes'),
                     ('reserved2', 'Reserved second-latest top100'), ('reserved3', 'Reserved third-latest top100')]:
    data = read(f'combined_v2_{panel}_comparison.json')
    if data is None:
        continue
    comparisons[panel] = data
    old = data['baseline_assessment']['cb76']['all']
    new = data['candidate_assessment']['combined_v2']['all']
    assert old['all_clean'] and new['all_clean']
    lines.append(f"| {title} | {old['wins']}/{old['games']} ({100*old['wins']/old['games']:.1f}%) | "
                 f"{new['wins']}/{new['games']} ({100*new['wins']/new['games']:.1f}%) | "
                 f"{new['both_seat_wins']}/{new['fixtures']} | +{len(data['gained_wins'])} / -{len(data['lost_wins'])} |")
    if panel != 'public27':
        a, b = data['baseline_assessment']['cb76']['top20'], data['candidate_assessment']['combined_v2']['top20']
        added = sum(r['rank'] <= 20 for r in data['gained_wins'])
        lost = sum(r['rank'] <= 20 for r in data['lost_wins'])
        top_label = 'Newest top20 subset' if panel == 'top100' else f'{title}: top20 subset'
        lines.append(f"| {top_label} | {a['wins']}/{a['games']} ({100*a['wins']/a['games']:.1f}%) | "
                     f"{b['wins']}/{b['games']} ({100*b['wins']/b['games']:.1f}%) | {b['both_seat_wins']}/20 | +{added} / -{lost} |")
lines += ['', '**The requested greater-than90% target is not met.** The newest top100 result is78%; '
    'the newest top20 subset is exactly90%. These are fixed-action replay diagnostics, '
    'not an estimated online win rate or a top10 probability. The newest100 includes84 '
    'distinct episodes; the top20 subset includes15. The reserved sets have92 and96 distinct '
    'episodes, with9 and7 episode IDs also present in development.', '',
    'The27 original uploaded seats reproduce all719 submitted actions and both final rewards '
    'exactly; this verifies baseline provenance and replay mechanics. Online at the collection '
    'snapshot, the submission had24 wins and3 losses. Playing both seats locally produces48/54 '
    'baseline wins. The new combined candidate retains those wins but does not rescue the three losses.', '',
    '## Changes in the combined candidate', '',
    '- Reorders an existing land purchase after same-turn sales only when guarded market forecasts '
    'fund the next quadrant and preserve other resources. This rescues both latest Majkel seats.',
    '- Uses eight whole, prefix-compatible schedules after observing the second shop. '
    'These preserve the existing opening and match worker and investment commitments.',
    '- Removes the Yarn/Smoothie rule that initially lost four public-control wins. '
    'The repeated public27 panel is development evidence after this correction.', '',
    '## Experiment record', '',
    '| Experiment | Result | Decision |', '|---|---|---|',
    '| Forecast rollout V1 | Two-seed reacting pilot tied baseline; no activation | Rejected |',
    '| Forecast rollout V2 | 32/40 top20, no added win; mean margin decreased | Rejected |',
    '| Whole-route searches | 33 then232 variants; selected rules checked against affected winners | Development only |',
    '| Funded-land repair | 134/200 vs132/200, no lost winning seats | Retained for combination |',
    '| Combined V1 | 158/200, but public27 fell48/54 to44/54 | Rejected |',
    '| Combined V2 | 156/200; public27 restored48/54 | Qualification below |',
    '| Three current melon-opening families | 15W/31L,8W/2D/36L,23W/23L vs32W/14L | All rejected |', '',
    'The opening families rescued one or two public losses but sacrificed too many top20 wins. '
    'Earlier melon output alone did not establish a stronger policy.', '', '## Qualification', '']
reserved = [comparisons.get(k) for k in ('reserved2', 'reserved3')]
if all(reserved):
    reserved_pass = all(d['delta_points'] >= 0 for d in reserved) and sum(d['delta_points'] for d in reserved) > 0
    lines.append(f"Reserved replay gate: **{'PASS' if reserved_pass else 'FAIL'}**, combined point change "
                 f"{sum(d['delta_points'] for d in reserved):+.1f}. Individual gained/lost seats are in the case reports.")
elif any(d and d['delta_points'] < 0 for d in reserved):
    lines.append('Reserved replay gate: **FAIL** on a per-set aggregate decline. Later conditional tests were not run.')
else:
    lines.append('Reserved replay gate: incomplete; no promotion claim.')
for phase in ('screen', 'confirm'):
    r = read(f'combined_v2_{phase}_receipt.json')
    if r:
        a = r['assessment']
        lines += ['', f"Reacting {phase}: baseline {a['all']['baseline']['wins']}W/"
                  f"{a['all']['baseline']['draws']}D/{a['all']['baseline']['losses']}L; candidate "
                  f"{a['all']['candidate']['wins']}W/{a['all']['candidate']['draws']}D/"
                  f"{a['all']['candidate']['losses']}L. Frozen gate: "
                  f"**{'PASS' if a['screen_passed' if phase == 'screen' else 'confirmation_passed'] else 'FAIL'}**. "
                  f"Whole-seed bootstrap95% interval for paired point-rate change: {a['bootstrap_95pct_whole_seed']}."]
        if phase == 'screen' and not a['screen_passed']:
            lines += ['', 'The four new losses replace baseline draws at seed22929006 against cb76 and ae349, '
                      'both seats. All activate Farmers Market/Smoothie route113410114, with zero funded-land '
                      'repair activations; each loses6114 margin. Conditional operational verification and '
                      'the untouched32-seed confirmation were stopped at the failed performance gate. '
                      'The prepared verifier was statically checked, but its game suite was never run.']
operational = read('combined_v2_operational_receipt.json')
if operational:
    lines += ['', f"Native and actual file-loader verification: **{'PASS' if operational['passed'] else 'FAIL'}**."]
else:
    lines += ['', 'Native framework/file-loader qualification for these exact bytes has not been completed.']
confirm = read('combined_v2_confirm_receipt.json')
qualified = bool(confirm and confirm['assessment']['confirmation_passed'] and operational and operational['passed'])
lines += ['', '**Decision: ' + ('independently qualified, but greater-than90% remains unmet.' if qualified else
    'rejected for promotion; preserve the experimental file and retain the incumbent.') + '**', '',
    '## Files and every-case results', '', '- ' + link('Experimental candidate4802aa95', candidate),
    '- ' + link('Exact uploaded baselinecb76fbc4', HERE / 'baseline_cb76fbc4.py'),
    '- ' + link('Frozen overall plan', HERE / 'PLAN.md'),
    '- ' + link('Frozen combinedV2 plan', HERE / 'COMBINATION_V2_PLAN.md'),
    '- ' + link('Public-loss diagnosis', ROOT / 'diagnostics/fresh90_loss_audit_20260929/LATEST_PUBLIC_LOSSES_56680167_AUDIT.md')]
delivery = ROOT / 'main_candidate_fresh_replay_20260930_4802aa95.py'
if delivery.exists():
    assert sha(delivery) == sha(candidate)
    lines.append('- ' + link('Byte-identical experimental candidate in the workspace root', delivery))
for panel in comparisons:
    lines.append('- ' + link(f'{panel}: every seat, rewards, margins, changes and hashes (CSV)', HERE / f'combined_v2_{panel}_comparison.csv'))
for family in (1, 2, 3):
    lines.append('- ' + link(f'Opening family{family}: every pilot case', HERE / f'opening_family{family}_pilot_comparison.csv'))
if (HERE / 'ALL_CASE_ROWS.csv').exists():
    lines += ['- ' + link('All logged case rows across experiments (includes exact reused rows)', HERE / 'ALL_CASE_ROWS.csv'),
              '- ' + link('Case ledger provenance and hashes', HERE / 'ALL_CASE_ROWS_INDEX.json')]
for phase in ('screen', 'confirm'):
    paired = HERE / f'combined_v2_{phase}_paired_cases.csv'
    if paired.exists():
        lines.append('- ' + link(f'Reacting {phase}: every paired case', paired))
leading = read('leading_pilot_decision.json')
if leading:
    lines += ['', '## Final alternative: highest-ranked single-tape controls', '',
              'The complete recorded schedules from ranks1,2,3 were selected and frozen before their pilot. '
              'They score12W/2D/32L,12W/0D/34L and22W/0D/24L versus baseline32W/0D/14L. '
              'All138 cases are clean, but all three controls fail the frozen improvement criteria. '
              'No further source-tape search was made in this bounded experiment.']
    lines.append('')
    for rank in (1, 2, 3):
        lines.append('- ' + link(f'Rank{rank} control: every pilot case', HERE / f'leading_rank{rank}_pilot_comparison.csv'))
lines += ['', f"Candidate SHA-256: `{sha(candidate)}`.",
          f"Report generated: {datetime.now(timezone.utc).isoformat()}.", '']
def readable(line):
    # Add prose spacing without changing filenames, URLs or source hashes.
    pieces = re.split(r'(\]\(H:/[^)]*\))', line)
    for i, piece in enumerate(pieces):
        if piece.startswith('](H:/'):
            continue
        piece = piece.replace('greater-than90%', 'more than 90%')
        piece = re.sub(r'\b(top|all|All|and|is|includes|have|with|The|had|produces|then|vs|fell|to|restored|bootstrap|seed|route|loses|untouched|family|rank|Rank|ranks|score|baseline|candidate|submission|are|newest|exactly|public)(?=\d)', r'\1 ', piece)
        piece = piece.replace('baselinecb76fbc4', 'baseline cb76fbc4').replace('combinedV2', 'combined V2')
        pieces[i] = piece
    return ''.join(pieces)
(HERE / 'RESULTS.md').write_text('\n'.join(readable(line) for line in lines), encoding='utf-8')
print(json.dumps(dict(report=str(HERE / 'RESULTS.md'), qualified=qualified, candidate_sha256=sha(candidate))))
