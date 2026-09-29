"""Final repair report, including every top100, native and archive case."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIOR = ROOT / 'diagnostics/submission_top100_compare_20260929_1104'


def read(name): return json.loads((HERE / name).read_text(encoding='utf-8'))
def rows(path): return list(map(json.loads, Path(path).read_text(encoding='utf-8').splitlines()))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def wdl(records): return '/'.join(str(sum(r['result'] == x for r in records)) for x in ('win', 'draw', 'loss'))
def sweeps(records, key): return sum(all(r['result'] == 'win' for r in records if r[key] == k) for k in {r[key] for r in records})


def main():
    manifest = read('manifest_v3.json')
    digest = manifest['candidate_sha256']
    release = ROOT / 'main_candidate_minimal_repair_20260929_cb76fbc4.py'
    assert sha(release) == sha(manifest['candidate']) == digest
    saved, screen, confirm, parity, loader, archive = [read(n) for n in (
        'saved_v3_full_receipt.json', 'reactive_v3_screen_receipt.json',
        'reactive_v3_confirm_receipt.json', 'native_checks_v3_receipt.json',
        'loader_v3.json', 'archive_v3_receipt.json')]
    for ledger, receipt in [('saved_v3.jsonl', saved), ('reactive_v3_screen.jsonl', screen),
                            ('reactive_v3_confirm.jsonl', confirm), ('native_checks_v3.jsonl', parity),
                            ('archive_v3.jsonl', archive)]:
        assert sha(HERE / ledger) == receipt['results_sha256']
        assert receipt['candidate_sha256'] == digest
    passed = (saved['regression_gate_passed'] and screen['assessment']['passed']
              and confirm['assessment']['passed'] and parity['passed'] and loader['passed']
              and archive['complete'] and archive['clean'])
    originals = rows(PRIOR / 'local_results.jsonl')
    policies = {name: [r for r in originals if r['label'] == name] for name in ('4eeac9c3', 'ae349d83')}
    policies.update({f'repair {v}': rows(HERE / f'saved_{v}.jsonl') for v in ('v1', 'v2', 'v3')})
    report = ['# Final minimal route repair — 29 September 2026', '',
              f'Standalone candidate: [{release.name}]({release.as_posix()}).', '',
              f'SHA-256: `{digest}`. Frozen promotion gates passed: **{passed}**. '
              f'Root main.py promoted: **{sha(ROOT / "main.py") == digest}**.', '',
              '## Changes', '',
              'Start from exact 4eeac9c3 (September 27). Preserve its opening and core '
              'queue, quantity, purchase and market logic. Add complete schedule choices '
              'for Brunch/Brunch, Brunch/Smoothie, and IceCream/Pet after both shops '
              'have appeared. Their earlier schedule prefixes match the original. '
              'Carry forward the existing repair that retains executable planting requests '
              'when there are too few seeds for all requested plantings.', '',
              'This avoids the later automatic donor opening and production-fingerprint '
              'controllers. It does not select routes using opponent identities or game seeds. '
              'A final explicit entrypoint ensures the file loader selects the intended agent.', '',
              '## Current saved top100', '',
              'Same frozen snapshot for every file: September 29, 11:03:38 UTC / 16:33:38 IST. '
              'The 100 teams correspond to 91 distinct episodes. Each tape is tested in both '
              'seats. Fixed actions cannot react to changed markets; this is development '
              'and regression evidence, not independent validation.', '',
              '| Version | Top10 W/D/L | Top20 W/D/L | Top100 W/D/L | Seat win rate | Both-seat team wins |',
              '|---|---:|---:|---:|---:|---:|']
    for name, rs in policies.items():
        report.append(f'| {name} | {wdl([r for r in rs if r["rank"] <= 10])} | '
                      f'{wdl([r for r in rs if r["rank"] <= 20])} | {wdl(rs)} | '
                      f'{sum(r["result"] == "win" for r in rs)/len(rs):.1%} | {sweeps(rs,"rank")}/100 |')
    report += ['', f'V3 recovered **{saved["recovered_regressed_teams"]}/9** regression teams; '
               f'lost 4ee seat wins: **{len(saved["comparisons"]["4eeac9c3"]["regressed"])}**. '
               f'Every V3 game clean: {saved["clean"]}.', '',
               'The complete table includes every changed and unchanged team: [TOP100_CASES_V3.md](TOP100_CASES_V3.md).', '',
               '## Reacting-policy tests', '',
               'Original native shop generation, hidden configuration seed, both seats, '
               'and four reacting opponents. Win = 1 point; draw = 0.5. The bootstrap '
               'keeps both seats and all four opponents in each complete seed block.']
    for stage, title, receipt in [('screen', 'Selected development cases', screen),
                                  ('confirm', 'Independent 32-seed native confirmation', confirm)]:
        rs = rows(HERE / f'reactive_v3_{stage}.jsonl'); a = receipt['assessment']
        report += ['', f'### {title}', '', '| Opponent | V3 W/D/L | 4ee W/D/L | Point difference |',
                   '|---|---:|---:|---:|']
        for rival, block in a['per_opponent'].items():
            report.append(f'| {rival} | {wdl([r for r in rs if r["rival"] == rival and r["version"] == "candidate"])} | '
                          f'{wdl([r for r in rs if r["rival"] == rival and r["version"] == "4ee"])} | {block["delta"]:+g} |')
        report += ['', f'Totals: V3 **{wdl([r for r in rs if r["version"] == "candidate"])}**; '
                   f'4ee **{wdl([r for r in rs if r["version"] == "4ee"])}**. '
                   f'Win-point-rate change **{a["paired_win_point_rate_delta"]*100:+.4f} percentage points**; '
                   f'95% whole-seed bootstrap interval **[{a["paired_whole_seed_bootstrap_95pct"][0]*100:+.4f}, '
                   f'{a["paired_whole_seed_bootstrap_95pct"][1]*100:+.4f}]**. Stage passed: **{a["passed"]}**.']
        if stage == 'screen':
            report += ['', 'Development seeds were chosen from earlier experiments. Only the '
                       '64 source-bound 4ee baseline rows were reused, with original engine '
                       'labels and provenance. Every V3 game was newly run.']
    confirmation_rows = rows(HERE / 'reactive_v3_confirm.jsonl')
    candidate_rows = [r for r in confirmation_rows if r['version'] == 'candidate']
    active = [r for r in candidate_rows if r['candidate_telemetry'].get('minimal_route_turns',0)]
    report += ['', f'New route activations in confirmation: **{len(active)}/{len(candidate_rows)} candidate games** '
               f'across **{len({r["seed"] for r in active})}/32 seed blocks**. '
               f'Partial planting activated in {sum(bool(r["candidate_telemetry"].get("partial_plant_turns")) for r in candidate_rows)} games.', '',
               '| New route pair | Activated games | W/D/L |', '|---|---:|---:|']
    for pair in ('BRUNCH_SPOT|BRUNCH_SPOT','BRUNCH_SPOT|SMOOTHIE_SHOP','ICE_CREAM_SHOP|PET_CAFE'):
        chosen = [r for r in active if r['candidate_telemetry']['minimal_route_pair144'] == pair]
        report.append(f'| {pair.replace("|", " / ")} | {len(chosen)} | {wdl(chosen)} |')
    report += ['', 'Complete native outcomes: [REACTIVE_CASES_V3.md](REACTIVE_CASES_V3.md).', '',
               '## Earlier loss30 and top20 archive', '',
               'These are older saved tapes, distinct from today’s top20. They measure '
               'retained and lost earlier fixes. They are not fresh validation.', '',
               '| Group | Uploaded ae349 | V1 | V2 | V3 | V3 W/D/L |',
               '|---|---:|---:|---:|---:|---:|']
    previous = {v: read(f'archive_{v}_receipt.json') for v in ('v1', 'v2')}
    original_sweeps = {'loss30': 27, 'top20': 19, 'pet_public_win_control': 1}
    for group, block in archive['groups'].items():
        n = block['games'] // 2
        report.append(f'| {group} | {original_sweeps[group]}/{n} | '
                      f'{previous["v1"]["groups"][group]["both_seat_wins"]}/{n} | '
                      f'{previous["v2"]["groups"][group]["both_seat_wins"]}/{n} | '
                      f'{block["both_seat_wins"]}/{n} | {block["wins"]}/{block["draws"]}/{block["losses"]} |')
    report += ['', 'Every archive comparison: [ARCHIVE_CASES_V3.md](ARCHIVE_CASES_V3.md).', '',
               '## Execution and recommendation', '',
               f'Native parity: {parity["games"]} cases, passed={parity["passed"]}. '
               f'Four direct/file-loader games passed={loader["passed"]}, with exact actions '
               f'and rewards in both seats. Loader callable: `{loader["loaded_name"]}`. '
               f'Minimum remaining overage: {min(r["minimum_remaining_overage"] for r in loader["rows"]):.6f} seconds.', '',
               ('V3 passed the prospectively frozen promotion gates on these tested policies. '
                'This supports a local improvement; it does not establish superiority to every opponent.' if passed else
                'V3 did not pass every prospectively frozen promotion gate. Keep root main.py '
                'at 4ee and retain this standalone candidate as experimental. Do not claim '
                'independently established overall superiority.'), '',
               'V1 and V2 were both rejected because their untouched native blocks were '
               'worse than 4ee. Their reports and exact files remain preserved. No Kaggle '
               'access or upload occurred during these repairs. No local test can provide '
               'a reliable rating forecast or top10 probability.', '',
               '## Reproduce', '',
               '`build_v3.py`; `finish_v3.py` (sequential saved, development, native parity, '
               'loader, native confirmation, archive); `write_report_v3.py`.', '',
               'Use the project Python runtime from this directory. The shared game lock '
               'prevents concurrent coordinators. All plans, source manifests, jobs, JSONL '
               'results and SHA-bound receipts are preserved. The prior main.py backup is '
               '`H:/hackathan/main_before_regression_repair_20260929_4eeac9c3.py`.']
    (HERE / 'RESULTS_V3.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
    indexed = {name: {(r['rank'], r['candidate_seat']): r for r in rs} for name, rs in policies.items()}
    lines = ['# Every top100 comparison — V3', '', 'Outcomes are seat 0 / seat 1.', '',
             '| Rank/team | 4ee | ae349 | V1 | V2 | V3 | V3 margins |', '|---|---|---|---|---|---|---:|']
    for rank in range(1,101):
        pair = [indexed['repair v3'][rank,s] for s in (0,1)]
        team = pair[0]['team'].replace('|','\\|')
        cells = [' / '.join(index[rank,s]['result'] for s in (0,1)) for index in indexed.values()]
        lines.append(f'| {rank}. {team} | ' + ' | '.join(cells) + f' | {pair[0]["margin"]:+,.0f} / {pair[1]["margin"]:+,.0f} |')
    (HERE / 'TOP100_CASES_V3.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    reactive = rows(HERE / 'reactive_v3_confirm.jsonl')
    indexed = {(r['seed'],r['rival'],r['candidate_seat'],r['version']):r for r in reactive}
    lines = ['# Every native confirmation scenario — V3', '',
             '| Seed | Opponent | Seat | 4ee | V3 | 4ee margin | V3 margin |', '|---|---|---:|---|---|---:|---:|']
    for seed,rival,seat in sorted({(r['seed'],r['rival'],r['candidate_seat']) for r in reactive}):
        a,b = indexed[seed,rival,seat,'4ee'],indexed[seed,rival,seat,'candidate']
        lines.append(f'| {seed} | {rival} | {seat} | {a["result"]} | {b["result"]} | {a["margin"]:+,.0f} | {b["margin"]:+,.0f} |')
    (HERE / 'REACTIVE_CASES_V3.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    reference = {r['case_id']:r['candidate'] for r in rows(ROOT/'diagnostics/combined_agent_257f_20260929/saved_panel/comparison_manifest_results.jsonl')}
    indexed = {v:{r['case_id']:r for r in rows(HERE/f'archive_{v}.jsonl')} for v in ('v1','v2','v3')}
    lines = ['# Every archive case — V3', '', '| Case | ae349 | V1 | V2 | V3 | V3 margin |', '|---|---|---|---|---|---:|']
    for case in sorted(reference):
        cells = [reference[case]['result']] + [indexed[v][case]['result'] for v in indexed]
        lines.append(f'| {case} | '+' | '.join(cells)+f' | {indexed["v3"][case]["margin"]:+,.0f} |')
    (HERE / 'ARCHIVE_CASES_V3.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    receipt = dict(candidate_sha256=digest,promotion_gates_passed=passed,
                   root_main_sha256=sha(ROOT/'main.py'),release_path=str(release),report=str(HERE/'RESULTS_V3.md'))
    (HERE/'release_v3_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__ == '__main__': main()
