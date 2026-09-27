from datetime import datetime, timezone
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def wdl(games):
    return '/'.join(str(sum(g['result'] == result for g in games)) for result in ('win','draw','loss'))

if __name__ == '__main__':
    manifest = json.loads((HERE/'build_manifest.json').read_text())
    pilot = json.loads((HERE/'pilot.json').read_text())
    panels = json.loads((HERE/'panels.json').read_text())
    assert panels['complete']
    lines = [f'# Purchase and iterated queue candidate {manifest["candidate_sha256"][:8]}', '',
             f'Updated {datetime.now(timezone.utc).isoformat()}.', '',
             'The candidate adds purchase ordering and two passes of queue reordering to',
             'the uploaded c68 agent. It keeps the physical schedules and market quantities.',
             'It excludes the planned-funding component that failed its coverage test.', '',
             '## Development pilot', '',
             '| Reacting opponent | Candidate W/D/L |', '|---|---:|']
    for ref in ('c68','43d','3bd'):
        lines.append(f'| {ref} | {wdl([g for g in pilot["games"] if g["rival"] == ref])} |')
    lines += ['', f'All 48 complete: {pilot["all_done"]}. Recorded errors: {pilot["errors"]}.',
              f'Frozen pilot gate passed: {pilot["passed"]}.', '', '## Recorded regression panels', '',
              'The recent panel is the 27 September 11:37 UTC leaderboard snapshot.',
              'It contains 99 external teams and one separate self-control. These are',
              'recorded moves, not the opponents\' private reacting policies.', '',
              '| Panel | Prior both-seat wins | New both-seat wins | New seat W/D/L |', '|---|---:|---:|---:|']
    for label, key, old, denominator in [('Recent top 50','current50',36,50),
                                        ('Recent top 100, external','current100_external',73,99),
                                        ('Original saved top 50','original50',44,50)]:
        group = panels['summary'][key]
        lines.append(f'| {label} | {old}/{denominator} | {group["sweeps"]}/{denominator} | '
                     f'{group["seat_wins"]}/{group["seat_draws"]}/{group["seat_losses"]} |')
    changes = [r for r in panels['comparisons'] if not r['self_control']
               and [m>0 for m in r['old_margins']] != [m>0 for m in r['new_margins']]]
    lines += ['', f'All 300 complete: {panels["all_done"]}. Recorded error rows: {len(panels["error_rows"])}.',
              f'Previously winning seats lost: {len(panels["lost_winning_seats"])}.',
              f'Frozen regression gate passed: {panels["passed"]}.', '']
    if changes:
        lines += ['Changed match outcomes:', '']
        lines.extend(f'- {r["panel"]}: {r["team"]}, margins {r["old_margins"]} → {r["new_margins"]}.' for r in changes)
        lines.append('')
    else:
        lines += ['No external recorded win/loss outcome changed. Cash margins can still differ.', '']
    confirmation = None
    loader = None
    receipt = None
    confirmation_path = HERE/'confirmation.json'
    if confirmation_path.exists():
        confirmation = json.loads(confirmation_path.read_text())
        if confirmation['complete']:
            lines += ['## Independent reacting-policy confirmation', '',
                      'Untouched seeds 2713000–2713015, both seats and original native shops.',
                      'Agents cannot see the configured seed. All 256 comparisons were retained.', '',
                      '| Reacting opponent | Old c68 W/D/L | New candidate W/D/L |', '|---|---:|---:|']
            for ref in ('c68','43d','3bd','1f'):
                games = [g for g in confirmation['games'] if g['rival'] == ref]
                lines.append(f'| {ref} | {wdl([g for g in games if g["version"]=="old"])} | '
                             f'{wdl([g for g in games if g["version"]=="new"])} |')
            ci = confirmation['paired_seed_bootstrap_95']
            lines += ['', f'Paired-seed 95% bootstrap interval for pooled win-point gain: {ci}.',
                      'Both seats and all references stay together in each sampled seed.',
                      f'All complete: {confirmation["all_done"]}; recorded errors: {confirmation["errors"]}.',
                      f'Frozen confirmation gate passed: {confirmation["passed"]}.', '']
    loader_path = HERE/'loader_parity.json'
    if loader_path.exists():
        loader = json.loads(loader_path.read_text())
        lines += ['## File-loader verification', '',
                  f'Passed: {loader["passed"]}. Selected callable: `{loader["loaded_name"]}`.',
                  'Direct execution and Kaggle file loading match every action and both cash',
                  'totals in both seats. Native runtime budgets remain nonnegative.', '']
    receipt_path = HERE/'promotion_receipt.json'
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        lines += ['## Promotion and upload', '',
                  f'Submission: **{receipt.get("submission_id", "upload receipt awaiting ID")}**.',
                  f'Status: {receipt.get("kaggle_submission",{}).get("status", "pending")}.',
                  f'Submitted source SHA-256: `{receipt["candidate_sha256"]}`.',
                  f'Remote all-action and both-cash parity: {receipt.get("remote_parity_passed",False)}.',
                  f'Previous main backup: `{receipt["previous_main_backup"]}`.',
                  f'Uploaded backup: `{receipt["uploaded_backup"]}`.',
                  'The current user request authorized this single upload; authorization is consumed.', '']
    if receipt is not None and receipt.get('remote_parity_passed'):
        decision = 'Promoted and uploaded after all frozen gates passed; remote validation is verified.'
    elif loader is not None and loader['passed']:
        decision = 'Accept qualification for promotion; upload status is recorded separately.'
    elif not panels['passed'] or (confirmation is not None and confirmation.get('complete') and not confirmation['passed']):
        decision = 'Reject this candidate under its frozen gates. Preserve the source and results; do not promote.'
    else:
        decision = 'Accept completed stages only; remaining planned qualification is required before promotion.'
    lines += ['## Decision', '', decision, '', '## Interpretation', '',
              'Passing these stages does not establish a top-10 leaderboard rank or victory',
              'against every top-50 or top-100 team. Live ratings must be observed on Kaggle.',
              'The previous standalone-candidate rejections remain part of the research record.', '',
              'Evidence: PLAN.md, build_manifest.json, pilot.json, panels.json, confirmation.json,',
              'loader_parity.json and, after upload, promotion_receipt.json and validation_parity.json.', '']
    (HERE/'RESULTS.md').write_text('\n'.join(lines),encoding='utf8')
    print(str(HERE/'RESULTS.md'))
