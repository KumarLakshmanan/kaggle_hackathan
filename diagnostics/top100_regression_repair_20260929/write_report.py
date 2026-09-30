"""Produce a factual release report from completed, source-bound receipts."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
PRIOR=ROOT/'diagnostics/submission_top100_compare_20260929_1104'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def rows(path):return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines()]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def wdl(rs):return '/'.join(str(sum(r['result']==v for r in rs)) for v in ('win','draw','loss'))

def main():
    manifest=read(HERE/'manifest_v1.json')
    saved=read(HERE/'saved_v1_full_receipt.json')
    screen=read(HERE/'reactive_v1_screen_receipt.json')
    confirm=read(HERE/'reactive_v1_confirm_receipt.json')
    native=read(HERE/'native_checks_v1_receipt.json')
    loader=read(HERE/'loader_v1.json')
    archive=read(HERE/'archive_v1_receipt.json')
    current=rows(HERE/'saved_v1.jsonl')
    old=rows(PRIOR/'local_results.jsonl')
    assert sha(manifest['candidate'])==manifest['candidate_sha256']
    assert sha(HERE/'saved_v1.jsonl')==saved['results_sha256']
    for name,receipt in [('reactive_v1_screen.jsonl',screen),('reactive_v1_confirm.jsonl',confirm),('native_checks_v1.jsonl',native),('archive_v1.jsonl',archive)]:
        assert sha(HERE/name)==receipt['results_sha256']
    promoted=sha(ROOT/'main.py')==manifest['candidate_sha256']
    new_path=ROOT/'main_candidate_regression_repair_20260929_2c02f9f9.py'
    assert sha(new_path)==manifest['candidate_sha256']
    promotion_gates=(saved['regression_gate_passed'] and screen['assessment']['passed'] and confirm['assessment']['passed']
                     and native['passed'] and loader['passed'] and archive['clean'])
    text=['# Regression-repaired main.py — 29 September 2026','',
          f"Exact candidate: `{manifest['candidate_sha256']}`.",
          f"Standalone file: [{new_path.name}]({new_path.as_posix()}).",'',
          'The candidate restores the original 4ee opening, removes the automatic donor switch based on rival worker count, and restores the original Brunch/Pizza route. Other source-route, planting, hiring and production repairs remain.', '',
          f"Frozen promotion gates passed: **{promotion_gates}**. Root main.py promoted: **{promoted}**. No Kaggle access or upload occurred during this repair.", '',
          '## Current saved top-100 panel','',
          'Leaderboard snapshot: 2026-09-29 11:03:38 UTC / 16:33:38 IST. This panel informed the repair and is development evidence. Every opponent is a fixed public replay action tape; it cannot react to changed markets or our moves. Each team is tested in both seats.', '',
          '| Policy | Top 10 W/D/L | Top 20 W/D/L | Top 50 W/D/L | Top 100 W/D/L | Top 100 both-seat wins |',
          '|---|---:|---:|---:|---:|---:|']
    policies={'4eeac9c3':[r for r in old if r['label']=='4eeac9c3'],
              'ae349d83':[r for r in old if r['label']=='ae349d83'], 'new 2c02f9f9':current}
    for label,rs in policies.items():
        parts=[wdl([r for r in rs if r['rank']<=limit]) for limit in (10,20,50,100)]
        sweeps=sum(all(r['result']=='win' for r in rs if r['rank']==rank) for rank in range(1,101))
        text.append('| '+label+' | '+' | '.join(parts)+f' | {sweeps}/100 |')
    text+=['', 'All 200 repaired-policy games were DONE/DONE/720 with zero recorded candidate errors. All nine regressed team pairs were recovered and all 141 old-policy seat wins were preserved. The new policy adds six wins over 4ee. Relative to ae349 it recovers 18 seats and loses two seats against Attention Is All You Seed, for a net +16 wins.', '',
           '## Fresh reacting comparisons','',
           'The policies played the same seeds, opponents and both seats, with original endogenous shops and hidden configuration seeds. Wins earn 1 point; draws earn 0.5. Seed blocks keep both seats and all four opponents together. The screen used native transitions; the independent confirmation used the full native framework.']
    for title,receipt,ledger in [('8-seed screen',screen,'reactive_v1_screen.jsonl'),('16-seed native confirmation',confirm,'reactive_v1_confirm.jsonl')]:
        rs=rows(HERE/ledger);a=receipt['assessment']
        text+=['',f'### {title}','',
               '| Reacting opponent | New W/D/L | 4ee W/D/L | New minus 4ee points |',
               '|---|---:|---:|---:|']
        for rival,block in a['per_opponent'].items():
            text.append(f"| {rival} | {wdl([r for r in rs if r['rival']==rival and r['version']=='candidate'])} | {wdl([r for r in rs if r['rival']==rival and r['version']=='4ee'])} | {block['delta']:+g} |")
        text+=['',f"Totals: new **{wdl([r for r in rs if r['version']=='candidate'])}**, 4ee **{wdl([r for r in rs if r['version']=='4ee'])}** (W/D/L). Paired win-point-rate change: **{a['paired_win_point_rate_delta']*100:+.2f} percentage points**. Whole-seed bootstrap 95% interval: **[{a['paired_whole_seed_bootstrap_95pct'][0]*100:+.2f}, {a['paired_whole_seed_bootstrap_95pct'][1]*100:+.2f}] percentage points**. Gate passed: **{a['passed']}**."]
    text+=['','## Earlier saved 30-loss/top-20 archive','',
           'This supplementary 102-case diagnostic checks whether restoring the older opening undoes earlier targeted repairs. It is not fresh validation.', '',
           '| Group | Previous ae349 both-seat wins | New both-seat wins | New W/D/L |',
           '|---|---:|---:|---:|']
    baseline_sweeps={'loss30':'27/30','top20':'19/20','public_win_control':'1/1','public_win':'1/1','pet_public_win_control':'1/1'}
    for group,b in archive['groups'].items():
        text.append(f"| {group} | {baseline_sweeps.get(group,'see source ledger')} | {b['both_seat_wins']}/{b['games']//2} | {b['wins']}/{b['draws']}/{b['losses']} |")
    text+=['',f"Changed archived seat outcomes: {len(archive['flips'])}. All archived cases clean: {archive['clean']}. Full changes are recorded in `archive_v1_receipt.json`.", '',
           '## Execution verification','',
           f"All {native['games']} completed native parity cases matched candidate/rival rewards, outcomes, statuses, frames and complete candidate telemetry. Four direct/file-loader runs covered both seats; every action and final reward matched. The intended callable was `{loader['loaded_name']}`. Minimum remaining overage was {min(r['minimum_remaining_overage'] for r in loader['rows']):.6f} seconds.", '',
           'The first native-verifier attempt had an `expected` metadata-key collision with the shared helper after gameplay; it produced no accepted result rows. The verifier was fixed and the entire 14-case check rerun. Original code and failure metadata are preserved under `revisions/native_expected_key_collision/`; no candidate change or gate waiver was involved.', '',
           'A positive result against these local reacting policies would support an incremental improvement on this opponent set; it cannot determine a live Kaggle rating or guarantee top 10. The two prior uploaded ae349 copies are identical; new code here has not been uploaded.', '',
           '## Files and reproduction','',
           '`build.py` created the exact candidate from the downloaded ae349 source. `run_saved.py v1 pilot` then `run_saved.py v1 full` produced the regression ledger. `run_reactive.py v1 screen`, `verify_native.py v1`, `verify_loader.py v1`, and `run_reactive.py v1 confirm` produced reacting and operational results. `run_archive.py v1` checks the earlier archive. Completed checkpoints are preserved; never change source bytes and reuse a prior ledger.', '',
           'Evidence: `PLAN.md`, `ARCHIVE_CHECK_PLAN.md`, `manifest_v1.json`, all `*_receipt.json` files, `loader_v1.json`, and the detailed JSONL game ledgers. The old root file is backed up as `H:/hackathan/main_before_regression_repair_20260929_4eeac9c3.py`.']
    (HERE/'RESULTS.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    by_label={label:{(r['rank'],r['candidate_seat']):r for r in rs} for label,rs in policies.items()}
    details=['# Every current top-100 matchup','',
             'Margins are our cash minus opponent cash. Seats 0 and 1 are shown together. This is a fixed-replay development panel.', '',
             '| Rank / team | 4ee seat 0 / 1 | ae349 seat 0 / 1 | New seat 0 / 1 | New margin seat 0 / 1 |',
             '|---|---|---|---|---:|']
    for rank in range(1,101):
        new=[by_label['new 2c02f9f9'][rank,s] for s in (0,1)]
        values=[' / '.join(by_label[label][rank,s]['result'] for s in (0,1)) for label in policies]
        team=new[0]['team'].replace('|','\\|')
        details.append(f"| {rank}. {team} | {' | '.join(values)} | {new[0]['margin']:+,.0f} / {new[1]['margin']:+,.0f} |")
    (HERE/'TOP100_CASES.md').write_text('\n'.join(details)+'\n',encoding='utf-8')
    print(json.dumps({'promotion_gates_passed':promotion_gates,'root_promoted':promoted,
                      'report':str(HERE/'RESULTS.md'),'cases':str(HERE/'TOP100_CASES.md')},indent=2))

if __name__=='__main__':main()
