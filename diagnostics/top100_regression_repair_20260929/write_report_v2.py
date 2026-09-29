"""Generate the final repair report and every recorded comparison case."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIOR = ROOT / 'diagnostics/submission_top100_compare_20260929_1104'


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8'))


def rows(path):
    return list(map(json.loads, Path(path).read_text(encoding='utf-8').splitlines()))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wdl(records):
    return '/'.join(str(sum(r['result'] == outcome for r in records))
                    for outcome in ('win', 'draw', 'loss'))


def sweeps(records, key):
    return sum(all(r['result'] == 'win' for r in records if r[key] == value)
               for value in {r[key] for r in records})


def main():
    manifest = read('manifest_v2.json')
    digest = manifest['candidate_sha256']
    release = ROOT / 'main_candidate_fixed_20260929_6cd6ff9e.py'
    assert sha(release) == sha(manifest['candidate']) == digest
    saved, screen, confirm, parity, loader, archive = [read(name) for name in (
        'saved_v2_full_receipt.json', 'reactive_v2_screen_receipt.json',
        'reactive_v2_confirm_receipt.json', 'native_checks_v2_receipt.json',
        'loader_v2.json', 'archive_v2_receipt.json')]
    for ledger, receipt in [('saved_v2.jsonl', saved), ('reactive_v2_screen.jsonl', screen),
                            ('reactive_v2_confirm.jsonl', confirm),
                            ('native_checks_v2.jsonl', parity), ('archive_v2.jsonl', archive)]:
        assert sha(HERE / ledger) == receipt['results_sha256']
        assert receipt['candidate_sha256'] == digest
    passed = (saved['regression_gate_passed'] and screen['assessment']['passed']
              and confirm['assessment']['passed'] and parity['passed']
              and loader['passed'] and archive['complete'] and archive['clean'])
    original = rows(PRIOR / 'local_results.jsonl')
    policies = {
        'September 27: 4eeac9c3': [r for r in original if r['label'] == '4eeac9c3'],
        'September 29 upload: ae349d83': [r for r in original if r['label'] == 'ae349d83'],
        'Repair V1: 2c02f9f9': rows(HERE / 'saved_v1.jsonl'),
        'Repair V2: 6cd6ff9e': rows(HERE / 'saved_v2.jsonl'),
    }
    result = ['# Repaired candidate V2 — 29 September 2026', '',
              f'File: [{release.name}]({release.as_posix()}). SHA-256: `{digest}`.', '',
              f'Frozen promotion gates passed: **{passed}**. '
              f'Root main.py SHA-256: `{sha(ROOT / "main.py")}`.', '',
              '## What changed', '',
              'Relative to uploaded ae349d83: restore the original source opening; '
              'remove the automatic donor switch based on rival worker count; '
              'restore original routes for Brunch/Pizza, Yarn/Farmers, and Farmers/Pizza. '
              'Retain the other source scheduling, planting, hiring, production, and market repairs. '
              'The second repair differs from V1 only in two mapping assignments. '
              'No opponent name or game seed is used as a strategy condition.', '',
              'V1 recovered nine saved matchup regressions but failed independent native '
              'confirmation, so it was rejected. Its result and every case remain in '
              '[RESULTS.md](RESULTS.md). V2 was frozen before the new confirmation block.', '',
              '## Current saved top-100 comparison', '',
              'Snapshot: 2026-09-29 11:03:38 UTC / 16:33:38 IST, downloaded before this repair. '
              'Each team is tested in both seats. The 100 teams correspond to 91 distinct '
              'public episodes. Fixed replay actions cannot react to our policy changes. '
              'This panel informed the repair and is development evidence.', '',
              '| Policy | Top 10 W/D/L | Top 20 W/D/L | Top 100 W/D/L | Seat win rate | Teams won in both seats |',
              '|---|---:|---:|---:|---:|---:|']
    for name, records in policies.items():
        wins = sum(r['result'] == 'win' for r in records)
        result.append(f'| {name} | {wdl([r for r in records if r["rank"] <= 10])} | '
                      f'{wdl([r for r in records if r["rank"] <= 20])} | {wdl(records)} | '
                      f'{wins/len(records):.1%} | {sweeps(records, "rank")}/100 |')
    result += ['', f'Recovered original regression teams: {saved["recovered_regressed_teams"]}/9. '
               f'Lost original 4ee seat wins: {len(saved["comparisons"]["4eeac9c3"]["regressed"])}. '
               f'All 200 candidate games clean: {saved["clean"]}.', '',
               '## Reacting opponents', '',
               'All opponents react to each move; shops evolve under the native game rules; '
               'configuration seeds are hidden. Both seats and four opponents stay together '
               'in each bootstrap seed block. Win = 1 point, draw = 0.5. Cash margin is diagnostic.']
    for stage, title, receipt in [
        ('screen', 'Development: eight previously observed seed blocks', screen),
        ('confirm', 'Independent confirmation: 16 untouched native seed blocks', confirm),
    ]:
        records = rows(HERE / f'reactive_v2_{stage}.jsonl')
        assessment = receipt['assessment']
        result += ['', f'### {title}', '',
                   '| Opponent | V2 W/D/L | 4ee W/D/L | Point change |',
                   '|---|---:|---:|---:|']
        for rival, block in assessment['per_opponent'].items():
            result.append(f'| {rival} | {wdl([r for r in records if r["rival"] == rival and r["version"] == "candidate"])} | '
                          f'{wdl([r for r in records if r["rival"] == rival and r["version"] == "4ee"])} | {block["delta"]:+g} |')
        result += ['', f'Total W/D/L: V2 **{wdl([r for r in records if r["version"] == "candidate"])}**; '
                   f'4ee **{wdl([r for r in records if r["version"] == "4ee"])}**. '
                   f'Win-point rate change {assessment["paired_win_point_rate_delta"]*100:+.4f} percentage points. '
                   f'95% whole-seed bootstrap interval [{assessment["paired_whole_seed_bootstrap_95pct"][0]*100:+.4f}, '
                   f'{assessment["paired_whole_seed_bootstrap_95pct"][1]*100:+.4f}] percentage points. '
                   f'Frozen stage gates passed: **{assessment["passed"]}**.']
        if stage == 'screen':
            result += ['', 'The 64 exact 4ee baseline rows were reused from source-bound V1 ledgers '
                       'with their original engine labels. All 64 V2 rows were newly run. '
                       'These selected diagnostic seeds do not establish independent improvement.']
    result += ['', '## Earlier saved public-loss and top-20 archive', '',
               '| Group | Uploaded ae349 both-seat wins | V1 both-seat wins | V2 both-seat wins | V2 W/D/L |',
               '|---|---:|---:|---:|---:|---:|']
    archive_v1 = read('archive_v1_receipt.json')
    original_sweeps = {'loss30': 27, 'top20': 19, 'pet_public_win_control': 1}
    for group, block in archive['groups'].items():
        count = block['games'] // 2
        result.append(f'| {group} | {original_sweeps[group]}/{count} | '
                      f'{archive_v1["groups"][group]["both_seat_wins"]}/{count} | '
                      f'{block["both_seat_wins"]}/{count} | {block["wins"]}/{block["draws"]}/{block["losses"]} |')
    result += ['', 'These older tapes are regression diagnostics, not a second independent '
               'leaderboard or a reason to conceal trades between opponent groups.', '',
               '## Execution and decision', '',
               f'All {parity["games"]} native parity checks passed: {parity["passed"]}. '
               f'Four direct/file-loader games passed: {loader["passed"]}; '
               f'complete action and reward equality: {loader["action_reward_parity"]}. '
               f'Kaggle loader selected `{loader["loaded_name"]}`. '
               f'Minimum remaining overage: {min(r["minimum_remaining_overage"] for r in loader["rows"]):.6f} seconds.', '',
               ('The frozen promotion gates passed on the tested policy set.' if passed else
                'The candidate did not pass every frozen promotion gate. Keep it as an experimental '
                'standalone version and retain 4ee as root main.py; do not call it an independently '
                'proven replacement.'), '',
               'No Kaggle access or upload occurred during this repair. These local results cannot '
               'predict a Kaggle rating or top-10 probability. Backups preserve the exact previous '
               'root file and both repair candidates.', '',
               '## Reproduction and complete cases', '',
               '`build_v2.py`; `run_saved.py v2 full`; `run_reactive_v2.py v2 screen`; '
               '`verify_native.py v2`; `verify_loader.py v2`; '
               '`run_reactive_v2.py v2 confirm`; `run_archive.py v2`; `write_report_v2.py`.', '',
               'Run these sequentially from this directory with the project Python runtime. '
               'The game coordinators share `diagnostics/.shared_game_run.lock`. '
               'Do not edit a candidate and reuse its completed checkpoints.', '',
               'See [every top-100 matchup](TOP100_CASES_V2.md), '
               '[every fresh confirmation scenario](REACTIVE_CASES_V2.md), and '
               '[every archive case](ARCHIVE_CASES_V2.md). All original ledgers, SHA-bound '
               'receipts, and frozen PLAN_V2.md remain beside this report.']
    interruption = HERE / 'confirmation_interruption_20260929.json'
    if interruption.exists():
        interrupted = json.loads(interruption.read_text())
        result += ['', '### Checkpoint recovery', '',
                   f'The confirmation process stopped for an unconfirmed reason after '
                   f'{interrupted["completed_rows"]} clean saved games. The coordinator and '
                   'workers were verified absent, the stale lock was preserved, and every '
                   'saved row was validated against the frozen job/source hashes before '
                   'resuming only missing jobs. No candidate, seed, result, or criterion '
                   'was changed. See `confirmation_interruption_20260929.json` and '
                   '`interrupted_lock_20712.json`. Resume command: `finish_v2.py --resume-confirm`.']
    (HERE / 'RESULTS_V2.md').write_text('\n'.join(result) + '\n', encoding='utf-8')

    indexed = {name: {(r['rank'], r['candidate_seat']): r for r in records}
               for name, records in policies.items()}
    detail = ['# Every saved top-100 matchup — V2', '',
              'Each cell contains outcomes in seat 0 / seat 1; margins are our cash minus rival cash.', '',
              '| Rank / team | 4ee | Uploaded ae349 | V1 | V2 | V2 margins |',
              '|---|---|---|---|---|---:|']
    final = indexed['Repair V2: 6cd6ff9e']
    for rank in range(1, 101):
        zero, one = final[rank, 0], final[rank, 1]
        team = zero['team'].replace('|', '\\|')
        outcomes = [' / '.join(index[rank, seat]['result'] for seat in (0, 1)) for index in indexed.values()]
        detail.append(f'| {rank}. {team} | ' + ' | '.join(outcomes) +
                      f' | {zero["margin"]:+,.0f} / {one["margin"]:+,.0f} |')
    (HERE / 'TOP100_CASES_V2.md').write_text('\n'.join(detail) + '\n', encoding='utf-8')
    for ledger, title, output, field in [
        ('reactive_v2_confirm.jsonl', 'Every independent confirmation scenario', 'REACTIVE_CASES_V2.md', 'job_id'),
        ('archive_v2.jsonl', 'Every archived replay case', 'ARCHIVE_CASES_V2.md', 'case_id'),
    ]:
        detail = [f'# {title}', '', '| Case | Result | Own cash | Rival cash | Margin |',
                  '|---|---|---:|---:|---:|']
        for row in sorted(rows(HERE / ledger), key=lambda r: r[field]):
            detail.append(f'| {row[field]} | {row["result"]} | {row["candidate_reward"]:,.0f} | '
                          f'{row["opponent_reward"]:,.0f} | {row["margin"]:+,.0f} |')
        (HERE / output).write_text('\n'.join(detail) + '\n', encoding='utf-8')
    (HERE / 'release_v2_receipt.json').write_text(json.dumps(dict(
        candidate_sha256=digest, promotion_gates_passed=passed,
        root_main_sha256=sha(ROOT / 'main.py'), release_path=str(release),
        report=str(HERE / 'RESULTS_V2.md')), indent=2), encoding='utf-8')
    print(json.dumps(dict(promotion_gates_passed=passed, report=str(HERE / 'RESULTS_V2.md')), indent=2))


if __name__ == '__main__':
    main()
