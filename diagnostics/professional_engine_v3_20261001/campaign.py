"""Sequential conditional gates and exact-byte local promotion; never uploads."""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()
def log(text):
    with (ROOT/'agent.md').open('a', encoding='utf-8') as out:
        out.write('\n\n- **'+now()+' — '+text+'\n')


def run(script, *args):
    subprocess.run([sys.executable, str(HERE/script), *map(str, args)], cwd=ROOT, check=True)


def main():
    print('Waiting for frozen v2 campaign to finish; full-game lock remains respected.',flush=True)
    prior=ROOT/'diagnostics/professional_engine_20261001/DECISION.json'
    while True:
        try:
            previous=json.loads(prior.read_text())
            complete=json.loads((prior.parent/'confirm_receipt.json').read_text())['complete']
            if complete and not (ROOT/'diagnostics/.shared_game_run.lock').exists() and (not previous['promotion_eligible'] or previous['promoted']): break
        except (FileNotFoundError,json.JSONDecodeError): pass
        time.sleep(20)
    run('run_experiment.py','screen','--workers','6')
    screen = json.loads((HERE/'screen_receipt.json').read_text())
    assert screen['complete']; survivor = screen['assessment']['screen_survivor']
    if survivor is None:
        run('report.py'); log('professional engine v3 rejects both variants at the frozen reacting screen.** No conditional panels run; incumbent preserved. Evidence: `diagnostics/professional_engine_v3_20261001/screen_receipt.json`. No Kaggle actions.')
        return
    candidate = HERE/f'candidate_{survivor}_r3.py'
    assert sha(candidate) == screen['candidate_hashes'][survivor]
    log('professional engine passes the96-game fresh reacting development screen.** '+json.dumps(screen['assessment']['groups'])+'. **Decision: advance exact'+sha(candidate)[:8]+' to saved preservation and native/loader gates; no promotion yet.** Physical planning requires actual activation; inactive full and market variants cannot establish its strength. Frozen report: `diagnostics/professional_engine_20261001/screen_receipt.json`. No Kaggle actions.')
    for phase in ('top20', 'top100'):
        run('run_experiment.py', phase, '--candidate', candidate, '--workers', '6')
        receipt = json.loads((HERE/f'{phase}_receipt.json').read_text())
        passed = receipt['assessment']['decisions']['candidate']['replay_passed']
        log('professional engine v3 '+phase+' diagnostic completed.** '+json.dumps(receipt['assessment']['groups'])+'. **Decision: '+('pass preservation gate; continue frozen validation' if passed else 'reject promotion at saved preservation gate; retain incumbent')+'.** Fixed tapes are correlated controls, not adaptive-policy validation. Every case: `diagnostics/professional_engine_v3_20261001/'+phase+'_results.jsonl`. No Kaggle actions.')
        if not passed: run('report.py'); return
    run('verify_loader.py', '--candidate', candidate)
    loader = json.loads((HERE/'loader_receipt.json').read_text())
    log('professional engine passes native direct/file-loader parity in both seats.** All four controls match complete actions/rewards and the frozen fast-native rewards; explicit final callable'+loader['entrypoint']+'. **Decision: pass operation gate and run untouched256-game native confirmation; no promotion.** `diagnostics/professional_engine_20261001/loader_receipt.json`. No Kaggle actions.')
    run('run_experiment.py', 'confirm', '--candidate', candidate, '--workers', '6')
    run('report.py')
    decision = json.loads((HERE/'DECISION.json').read_text())
    receipt = json.loads((HERE/'confirm_receipt.json').read_text())
    log('professional engine v3 independent native confirmation completed.** '+json.dumps(receipt['assessment']['groups'])+'. Whole-seed paired95% interval'+str(decision['confidence']['whole_seed_95_percent_interval'])+'. **Decision: '+('all frozen promotion gates pass' if decision['promotion_eligible'] else 'reject promotion; preserve incumbent')+'.** Saved panels remain diagnostic; no universal win/top10 claim. Evidence: `diagnostics/professional_engine_v3_20261001/RESULTS.md`, `ALL_CASES.csv`, `DECISION.json`. No Kaggle actions.')
    if not decision['promotion_eligible']: return
    expected = '4ea1d89ac99758c6219bcd7d07b729de4dc5836260a25037ca973343b46c6289'
    if sha(ROOT/'main.py') != expected:
        log('v3 passes comparison with4ea but current root is a different incumbent.** **Decision: preserve root pending separately frozen direct incumbent qualification.** No Kaggle actions.')
        return
    assert sha(ROOT/'main.py') == expected, 'Root edited during campaign; preserve it.'
    digest = sha(candidate); backup = ROOT/f'main_candidate_professional_engine_v3_20261001_{digest[:8]}.py'
    if backup.exists(): assert sha(backup) == digest
    else: shutil.copyfile(candidate, backup)
    incumbent_backup=ROOT/'main_before_professional_engine_v3_20261001_4ea1d89a.py'
    if incumbent_backup.exists(): assert sha(incumbent_backup)==expected
    else: shutil.copyfile(ROOT/'main.py',incumbent_backup)
    temporary = ROOT/'main.professional_promoted_pending.py'; assert not temporary.exists()
    shutil.copyfile(candidate, temporary); assert sha(temporary) == digest
    assert sha(ROOT/'main.py') == expected
    os.replace(temporary, ROOT/'main.py'); assert sha(ROOT/'main.py') == digest
    date = datetime.now(timezone.utc); local = date.astimezone(timezone(timedelta(hours=5, minutes=30)))
    memory = (ROOT/'agent.md').read_text(encoding='utf-8'); start = memory.index('Current local competition artifact,'); end = memory.index('\n\n', start)
    groups = receipt['assessment']['groups']; ours = groups['candidate']; previous = groups['baseline']
    summary = ('Current local competition artifact, **'+date.strftime('%Y-%m-%d %H:%M UTC')+' / '+local.strftime('%H:%M IST')+'**: professional-engine v3 market candidate promoted to root `main.py`, exact **'+digest+'**. Previous4ea preserved as `main_before_professional_engine_v3_20261001_4ea1d89a.py`; candidate copy `'+backup.name+'`. Independent native confirmation: '+str(ours['wins'])+'W/'+str(ours['draws'])+'D/'+str(ours['losses'])+'L versus '+str(previous['wins'])+'W/'+str(previous['draws'])+'D/'+str(previous['losses'])+'L over128 cases each. Whole-seed95% point-rate gain interval'+str(decision['confidence']['whole_seed_95_percent_interval'])+'. Frozen saved-preservation, native and both-seat loader gates pass. Broader order-program search uses native market-phase factorization, preserved physical commitments and modeled supply equality. Physical investment planning remains experimental. **Universal wins and a top10 rank are not established.** No Kaggle access/upload. Evidence: `diagnostics/professional_engine_v3_20261001/RESULTS.md`, `DECISION.json`, `ALL_CASES.csv`.')
    (ROOT/'agent.md').write_text(memory[:start]+summary+memory[end:], encoding='utf-8')
    decision.update(promoted=True, root_main_sha256=digest, promotion_time_utc=now(), root_candidate_backup=str(backup))
    (HERE/'DECISION.json').write_text(json.dumps(decision, indent=2), encoding='utf-8')
    with (HERE/'RESULTS.md').open('a', encoding='utf-8') as out:
        out.write('\n## Exact-byte local promotion\n\nPromoted '+digest+' to root main.py after every frozen gate. Old bbff and candidate preserved in root. No Kaggle upload.\n')
    log('professional engine exact tested candidate promoted locally.** '+digest+'; root backup'+backup.name+'. **Decision: promote qualified market execution; retain experimental physical planner as a separate tool.** Every test case and final confidence evidence in `diagnostics/professional_engine_20261001/`. No Kaggle upload.')
    print('PROMOTED '+digest, flush=True)


if __name__ == '__main__': main()
