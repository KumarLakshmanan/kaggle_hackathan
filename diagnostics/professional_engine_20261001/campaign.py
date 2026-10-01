"""Sequential conditional gates and exact-byte local promotion; never uploads."""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def log(text):
    with (ROOT/'agent.md').open('a', encoding='utf-8') as out:
        out.write('\n\n- **'+now()+' — '+text+'\n')


def run(script, *args):
    subprocess.run([sys.executable, str(HERE/script), *map(str, args)], cwd=ROOT, check=True)


def main():
    screen = json.loads((HERE/'screen_receipt.json').read_text())
    assert screen['complete']; survivor = screen['assessment']['screen_survivor']
    if survivor is None:
        run('report.py'); log('professional engine rejects both variants at the frozen reacting screen.** No conditional panels run; root bbff preserved. Evidence: `diagnostics/professional_engine_20261001/screen_receipt.json`. No Kaggle actions.')
        return
    candidate = HERE/f'candidate_{survivor}.py'
    assert sha(candidate) == screen['candidate_hashes'][survivor]
    log('professional engine passes the96-game fresh reacting development screen.** '+json.dumps(screen['assessment']['groups'])+'. **Decision: advance exact'+sha(candidate)[:8]+' to saved preservation and native/loader gates; no promotion yet.** Physical planning requires actual activation; inactive full and market variants cannot establish its strength. Frozen report: `diagnostics/professional_engine_20261001/screen_receipt.json`. No Kaggle actions.')
    for phase in ('top20', 'top100'):
        run('run_experiment.py', phase, '--candidate', candidate, '--workers', '6')
        receipt = json.loads((HERE/f'{phase}_receipt.json').read_text())
        passed = receipt['assessment']['decisions']['candidate']['replay_passed']
        log('professional engine '+phase+' diagnostic completed.** '+json.dumps(receipt['assessment']['groups'])+'. **Decision: '+('pass preservation gate; continue frozen validation' if passed else 'reject promotion at saved preservation gate; retain bbff')+'.** Fixed tapes are correlated controls, not adaptive-policy validation. Every case: `diagnostics/professional_engine_20261001/'+phase+'_results.jsonl`. No Kaggle actions.')
        if not passed: run('report.py'); return
    run('verify_loader.py', '--candidate', candidate)
    loader = json.loads((HERE/'loader_receipt.json').read_text())
    log('professional engine passes native direct/file-loader parity in both seats.** All four controls match complete actions/rewards and the frozen fast-native rewards; explicit final callable'+loader['entrypoint']+'. **Decision: pass operation gate and run untouched256-game native confirmation; no promotion.** `diagnostics/professional_engine_20261001/loader_receipt.json`. No Kaggle actions.')
    run('run_experiment.py', 'confirm', '--candidate', candidate, '--workers', '6')
    run('report.py')
    decision = json.loads((HERE/'DECISION.json').read_text())
    receipt = json.loads((HERE/'confirm_receipt.json').read_text())
    log('professional engine independent native confirmation completed.** '+json.dumps(receipt['assessment']['groups'])+'. Whole-seed paired95% interval'+str(decision['confidence']['whole_seed_95_percent_interval'])+'. **Decision: '+('all frozen promotion gates pass' if decision['promotion_eligible'] else 'reject promotion; preserve incumbent bbff')+'.** Saved panels remain diagnostic; no universal win/top10 claim. Evidence: `diagnostics/professional_engine_20261001/RESULTS.md`, `ALL_CASES.csv`, `DECISION.json`. No Kaggle actions.')
    if not decision['promotion_eligible']: return
    expected = 'bbffbe65dee6e0dc4dd0147fec897df74e16760b76ec7d2a2b38f636bc90555f'
    assert sha(ROOT/'main.py') == expected, 'Root edited during campaign; preserve it.'
    digest = sha(candidate); backup = ROOT/f'main_candidate_professional_engine_20261001_{digest[:8]}.py'
    if backup.exists(): assert sha(backup) == digest
    else: shutil.copyfile(candidate, backup)
    assert sha(ROOT/'main_before_professional_engine_20260930_bbffbe65.py') == expected
    temporary = ROOT/'main.professional_promoted_pending.py'; assert not temporary.exists()
    shutil.copyfile(candidate, temporary); assert sha(temporary) == digest
    assert sha(ROOT/'main.py') == expected
    os.replace(temporary, ROOT/'main.py'); assert sha(ROOT/'main.py') == digest
    date = datetime.now(timezone.utc); local = date.astimezone(timezone(timedelta(hours=5, minutes=30)))
    memory = (ROOT/'agent.md').read_text(encoding='utf-8'); start = memory.index('Current local competition artifact,'); end = memory.index('\n\n', start)
    groups = receipt['assessment']['groups']; ours = groups['candidate']; previous = groups['baseline']
    summary = ('Current local competition artifact, **'+date.strftime('%Y-%m-%d %H:%M UTC')+' / '+local.strftime('%H:%M IST')+'**: professional-engine market candidate promoted to root `main.py`, exact **'+digest+'**. Previous bbff is preserved in root `main_before_professional_engine_20260930_bbffbe65.py`; candidate copy `'+backup.name+'`. Source/model-bound fresh native confirmation: '+str(ours['wins'])+'W/'+str(ours['draws'])+'D/'+str(ours['losses'])+'L versus '+str(previous['wins'])+'W/'+str(previous['draws'])+'D/'+str(previous['losses'])+'L over128 paired cases per version. Whole-seed95% point-rate gain interval'+str(decision['confidence']['whole_seed_95_percent_interval'])+'. All frozen saved-preservation, native and both-seat file-loader gates pass. The added market search uses public-state rival beliefs, reacting hypotheses and native cash/physical-state safeguards. Whole-portfolio physical planning and fitted tails remain experimental; its strength is not established by market-only wins. **Universal wins and a top10 rank are not established.** No Kaggle access/upload occurred. Evidence and every case: `diagnostics/professional_engine_20261001/RESULTS.md`, `DECISION.json`, `ALL_CASES.csv`.')
    (ROOT/'agent.md').write_text(memory[:start]+summary+memory[end:], encoding='utf-8')
    decision.update(promoted=True, root_main_sha256=digest, promotion_time_utc=now(), root_candidate_backup=str(backup))
    (HERE/'DECISION.json').write_text(json.dumps(decision, indent=2), encoding='utf-8')
    with (HERE/'RESULTS.md').open('a', encoding='utf-8') as out:
        out.write('\n## Exact-byte local promotion\n\nPromoted '+digest+' to root main.py after every frozen gate. Old bbff and candidate preserved in root. No Kaggle upload.\n')
    log('professional engine exact tested candidate promoted locally.** '+digest+'; root backup'+backup.name+'. **Decision: promote qualified market execution; retain experimental physical planner as a separate tool.** Every test case and final confidence evidence in `diagnostics/professional_engine_20261001/`. No Kaggle upload.')
    print('PROMOTED '+digest, flush=True)


if __name__ == '__main__': main()
