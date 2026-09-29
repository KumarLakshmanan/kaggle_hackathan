"""Build a readable report from completed, source-bound experiment receipts."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
NEW_SHA = 'ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb'
OLD_SHA = '257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def link(label, path):
    return f'[{label}]({Path(path).resolve().as_posix()})'


def fmt_wdl(value):
    return f"{value['win']}W / {value['draw']}D / {value['loss']}L"


def case_table(rows):
    lines = ['| Case / seat | Uploaded result | New result | Uploaded own / rival cash | New own / rival cash | Margin: uploaded → new | Margin change | Execution |',
             '|---|---|---|---:|---:|---:|---:|---|']
    for row in rows:
        old, new = row['baseline'], row['candidate']
        clean = row['execution_checks']['passed']
        lines.append(f"| {row['case_id'].replace('|', '/')} | {old['result']} | {new['result']} | "
                     f"{old['candidate_reward']:,.0f} / {old['opponent_reward']:,.0f} | "
                     f"{new['candidate_reward']:,.0f} / {new['opponent_reward']:,.0f} | "
                     f"{old['margin']:+,.0f} → {new['margin']:+,.0f} | {row['margin_delta']:+,.0f} | "
                     f"{'DONE/DONE, 720, no errors' if clean else 'FAILED'} |")
    return lines


def main():
    candidate = ROOT / 'main_candidate_improved_20260929.py'
    backup = ROOT / 'main_uploaded_backup_257f941d_20260929.py'
    assert sha(candidate) == NEW_SHA and sha(backup) == OLD_SHA
    assert sha(ROOT / 'main.py') == '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
    assessments, receipts, ledgers = {}, {}, {}
    for phase in ('pizza_pilot', 'saved_panel', 'reactive'):
        folder = HERE / phase
        assessments[phase] = read(folder / 'assessment.json')
        receipts[phase] = read(folder / 'comparison_manifest_receipt.json')
        ledger = folder / 'comparison_manifest_results.jsonl'
        assert receipts[phase]['status'] == 'complete'
        assert receipts[phase]['rows_sha256'] == sha(ledger)
        assert assessments[phase]['candidate_sha256'] == NEW_SHA
        ledgers[phase] = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()]
    loader_dir = HERE / 'loader_pensukesan_dieter_20260929'
    loader = read(loader_dir / 'receipt.json')
    assert loader['passed'] and loader['candidate_sha256'] == NEW_SHA
    loader_runs = [json.loads(line) for line in (loader_dir / 'runs.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(loader_runs) == 8
    saved_by_case = {(row['fixture_id'], row['candidate_seat']): row['candidate']
                     for row in ledgers['saved_panel']}
    for run in loader_runs:
        expected = saved_by_case[(run['fixture_id'], run['candidate_seat'])]
        assert run['candidate_reward'] == expected['candidate_reward']
        assert run['opponent_reward'] == expected['opponent_reward']
        assert run['result'] == expected['result']
        assert run['telemetry'] == expected['candidate_telemetry']
    saved, fresh = assessments['saved_panel'], assessments['reactive']
    assert assessments['pizza_pilot']['passed'] and saved['passed']
    output = ROOT / 'NEW_MAIN_TEST_REPORT_20260929.md'
    lines = [
        '# New standalone competition agent — 29 September 2026', '',
        '## Result', '',
        'The new file improves one saved matchup’s cash margin and preserves every saved win. '
        'It does not add a win on that panel. The fresh reacting comparison below determines whether '
        'there is evidence of a broader win-rate gain.', '',
        f"- New standalone file: {link('main_candidate_improved_20260929.py', candidate)}.",
        f"- Exact uploaded-version backup: {link('main_uploaded_backup_257f941d_20260929.py', backup)}.",
        '- Root research `main.py` remains unchanged. No Kaggle check or upload was performed.', '',
        '| Version | SHA-256 | Role |', '|---|---|---|',
        f'| New candidate | `{NEW_SHA}` | Tested separate file |',
        f'| Uploaded257 | `{OLD_SHA}` | Exact last uploaded baseline, submission 56662188 |',
        '| Root research main | `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed` | Preserved; also a reacting opponent |', '',
        '## What changed', '',
        'The candidate retains the uploaded agent’s market-order adjustments, planting and hiring repairs, '
        'animal-cash handling, donor scheduling, and the Ghost, Kwa, Pizza/Ice Cream, pasture and Pet Cafe route repairs. '
        'One new guard prevents the optional Goose4 Pizza route when the existing source-branch production category '
        'has at least 12 visible rival melon plots at step 72. It leaves the pre-existing route map in place in that case. '
        'The same route remains available for the 10-melon Dieter control.', '',
        'This threshold was fitted to a sparse saved example. It uses public farm observations, '
        'not player names, replay IDs or hidden seeds. That does not establish generalization.', '',
        '## Experiments and decisions', '',
        '| Experiment | Test | Result / decision |', '|---|---|---|',
        '| Public production guard | Static review of 208 stored observation rows | 2 target activations; Dieter and top20/public-win controls excluded from fallback. Proceed to gameplay. |',
        '| Guard target/control pilot | 4 paired scenarios, 8 full games | Both Pensukesan deficits improve by 45,291; both Dieter wins/rewards exact; clean execution. Passed. |',
        '| Guard full saved panel | 102 new games against source-bound prior baseline rows | 94W/0D/8L for both versions; total margin +90,582; no regressions. Passed the saved margin gate. |',
        '| Mirrored Brunch/Pizza route swap | Static state/schedule audit; 0 games | Rejected: matching farm tiles does not establish worker/inventory compatibility; schedules diverge on 575 later turns. |',
        '| Late melon delivery | Separate concurrent experiment | Not included in this frozen file; treatment validation was incomplete at selection time. No benefit attributed to it here. |',
        f"| Final fresh reacting comparison | 24 paired scenarios, 48 full games | Uploaded: {fmt_wdl(fresh['baseline_wdl'])}; new: {fmt_wdl(fresh['candidate_wdl'])}; margin change {fresh['total_margin_delta']:+,.0f}. |",
        '| Loader checker preparation | 0 games started | Checker import-path error; archived and fixed before the native run. Candidate unchanged. |',
        '| Actual Kaggle file-loader check | 4 fixture/seat cases × direct/file mode = 8 full games | Correct callable; all 719 two-player actions, rewards and telemetry match; all clean DONE/DONE/720. |', '',
        'A total of 166 full game executions were run for this candidate. Repeated fixture checks are not '
        'independent opponents. The 102 saved baseline outcomes were reused only after four fresh baseline '
        'pilot runs exactly reproduced their rewards, status and prior telemetry.', '',
        '## Saved opponent results', '',
        '| Group | Uploaded257 | New candidate | Both-seat opponent sweeps |', '|---|---|---|---|',
        '| Archived 30-loss set | 54W / 0D / 6L | 54W / 0D / 6L | 27/30 → 27/30 (90%) |',
        '| Saved top20 set | 38W / 0D / 2L | 38W / 0D / 2L | 19/20 → 19/20 (95%) |',
        '| Pet public-win control | 2W / 0D / 0L | 2W / 0D / 0L | 1/1 → 1/1 |', '',
        'Pensukesan’s own/rival cash changes from 120,144 / 174,100 to 107,828 / 116,493. '
        'Our cash falls by 12,316 while the rival’s falls by 57,607, reducing the deficit '
        'from 53,956 to 8,665 in each seat. This remains a loss. All other 100 saved seat results '
        'and margins are unchanged.', '',
        'Remaining losses: Pensukesan (−8,665 each seat), 吃白饭的大肥鱼 (−33,224), '
        'Roman (−18,815), and top20 DECEM (−9,085). These were not solved by this change.', '',
        '## Final fresh reacting test', '',
        'The seeds 2026092981–2026092984 and all three opponent sources were frozen before new outcomes. '
        'Each policy played both seats against each opponent with original native shops and hidden seeds. '
        'The four complete seed blocks, not individual seats, are the units for the declared consistency check.', '',
        '| Reacting opponent | Uploaded257 | New candidate | Point change | Margin change |',
        '|---|---|---|---:|---:|',
    ]
    for name, group in fresh['groups'].items():
        lines.append(f"| {name} | {fmt_wdl(group['baseline_wdl'])} | {fmt_wdl(group['candidate_wdl'])} | "
                     f"{group['point_delta']:+g} | {group['total_margin_delta']:+,.0f} |")
    lines += ['', f"New guard activations: **{len(fresh['pizza_guard_activations'])}/24 candidate games**.",
              f"Whole-seed point changes: `{fresh['whole_seed_point_deltas']}`.",
              f"Predeclared strict win-rate improvement gate: **{'passed' if fresh['passed'] else 'not passed'}**.", '',
              ('The fresh screen supports a gain under the declared small-sample gate; wider confirmation is still needed.'
               if fresh['passed'] else 'There is no demonstrated fresh win-rate gain. Retain this as a tested experimental margin repair; do not promote it as a stronger general policy.'), '',
              'These local results do not provide a reliable Kaggle score estimate or a probability of reaching top10. '
              'Saved action tapes cannot reproduce the full responses of their original opponents.', '',
              '## Every executed comparison case', '',
              '### Focused pilot (each row runs both versions)', '']
    lines += case_table(ledgers['pizza_pilot'])
    lines += ['', '### Full saved panel (new candidate run; uploaded reference reproduced and reused)', '']
    lines += case_table(ledgers['saved_panel'])
    lines += ['', '### Fresh reacting comparison (each row runs both versions)', '']
    lines += case_table(ledgers['reactive'])
    lines += ['', '### File-loader test details', '',
              '| Case / seat | Mode | Result | Own / rival cash | Margin | Minimum overage left | Completion |',
              '|---|---|---|---:|---:|---:|---|']
    for run in loader_runs:
        lines.append(f"| {run['fixture_id']} / {run['candidate_seat']} | {run['mode']} | {run['result']} | "
                     f"{run['candidate_reward']:,.0f} / {run['opponent_reward']:,.0f} | "
                     f"{run['candidate_reward'] - run['opponent_reward']:+,.0f} | "
                     f"{run['candidate_remaining_overage_min_seconds']:.3f}s | DONE/DONE, 720 |")
    lines += ['', 'All eight native loader runs also reproduce the saved-panel rewards and complete policy telemetry.', '',
              link('Eight native run records', loader_dir / 'runs.jsonl'), '',
              link('Four direct/file parity outcomes', loader_dir / 'outcomes.jsonl'), '',
              link('Source-bound loader receipt', loader_dir / 'receipt.json'), '',
              'The final callable must be `kaggle_a44_pet_market_gate_entrypoint`. Actual Kaggle loading is compared '
              'with direct `agent` execution, including both players’ complete action sequences. This checks the '
              'earlier helper-selection/PASS failure mode.', '',
              '## Evidence and reproduction', '',
              link('Frozen research plan', HERE / 'PLAN.md'), '',
              link('Pilot assessment', HERE / 'pizza_pilot/assessment.json'), '',
              link('Saved-panel assessment', HERE / 'saved_panel/assessment.json'), '',
              link('Fresh reacting assessment', HERE / 'reactive/assessment.json'), '',
              link('Archived loader preparation error', HERE / 'loader_checker_import_fix/failure.json'), '',
              'Each comparison folder contains its immutable manifest, source hashes, JSONL ledger and receipt. '
              'Use `run_comparison.py` for saved cases, `run_reactive_comparison.py` for the native phase, '
              'and `check_loader.py` for the operational check. Existing output paths are intentionally refused; '
              'make a new manifest/output directory for a reproduction. Both compared policy hashes and all '
              'case/seed/opponent bindings must remain unchanged.', '']
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('\n'.join(lines))
    summary = {'report_path': str(output), 'report_sha256': sha(output), 'candidate_sha256': NEW_SHA,
               'uploaded_baseline_sha256': OLD_SHA, 'full_games_executed': 166,
               'saved': saved, 'reactive': fresh, 'loader_receipt_sha256': sha(loader_dir / 'receipt.json'),
               'loader_runs': len(loader_runs), 'kaggle_contacted': False,
               'research_promotion': False, 'fresh_screen_gate_passed': bool(fresh['passed'])}
    with (HERE / 'FINAL_SUMMARY.json').open('x', encoding='utf-8') as stream:
        json.dump(summary, stream, indent=2, ensure_ascii=True)
    print(json.dumps({k: v for k, v in summary.items() if k not in ('saved', 'reactive')}, indent=2))


if __name__ == '__main__':
    main()
