"""Conditional holdouts and qualified source integration, without uploads."""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
from run_experiment import sha
from campaign import log,run
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def read(phase):return json.loads((HERE/f'{phase}_receipt.json').read_text())
def write(p,obj):Path(p).write_text(json.dumps(obj,indent=2),encoding='utf-8')

def main():
    screen=read('screen');name=screen['assessment']['screen_survivor'];assert name
    candidate=HERE/f'candidate_{name}.py';assert sha(candidate)==screen['candidate_hashes'][name]
    accepted=[m for m,d in screen['assessment']['decisions'].items() if m!='combined' and d['screen_passed']]
    if len(accepted)>1:
        joint=HERE/'candidate_joint.py'
        if not joint.exists():run('build.py','--name','joint','--modes',*sorted(accepted))
        manifest=json.loads(joint.with_suffix('.manifest.json').read_text());assert manifest['modes']==sorted(accepted)
        run('verify_joint.py')
        run('run_experiment.py','joint','--candidate',joint,'--solo',candidate,'--workers','6')
        r=read('joint');a=r['assessment'];g=a['groups'];d=a['decisions']['candidate']
        better=g['candidate']['points']>g['solo']['points'] or (g['candidate']['points']==g['solo']['points'] and g['candidate']['mean_margin']>g['solo']['mean_margin'])
        # Joint must also preserve each reference relative to the frozen solo.
        per_ok=all(d['per_reference_gain'][ref]>=a['decisions']['solo']['per_reference_gain'][ref] for ref in d['per_reference_gain'])
        use_joint=d['screen_passed'] and better and per_ok
        log('borrowed logic joint development completed.** '+json.dumps(a)+'. **Decision: '+('select frozen joint' if use_joint else 'reject joint; retain preselected solo')+'.** Native reacting evidence in `diagnostics/borrowed_logic_20261001/joint_receipt.json`. No Kaggle actions.')
        if use_joint:name='joint';candidate=joint
    expected_root=sha(ROOT/'main.py');assert expected_root in (sha(HERE/'baseline_4ea1d89a.py'),sha(HERE/'baseline_bbffbe65.py'))
    manifest=json.loads(candidate.with_suffix('.manifest.json').read_text())
    selection={'name':name,'candidate':str(candidate),'candidate_sha256':sha(candidate),'modes':manifest['modes'],'development_passed':True,'expected_incumbent_sha256':expected_root,'frozen_at_utc':datetime.now(timezone.utc).isoformat()}
    if (HERE/'selection.json').exists():assert json.loads((HERE/'selection.json').read_text())['candidate_sha256']==sha(candidate)
    else:write(HERE/'selection.json',selection)
    for phase in ('top20','top100'):
        run('run_experiment.py',phase,'--candidate',candidate,'--workers','6');r=read(phase)
        passed=r['assessment']['decisions']['candidate']['replay_passed']
        log('borrowed logic '+phase+' saved diagnostic completed.** '+json.dumps(r['assessment'])+'. **Decision: '+('preservation passes; advance' if passed else 'reject promotion; preserve incumbent')+'.** Fixed tapes are not independent policy validation. No Kaggle actions.')
        if not passed:run('report.py');return
    run('verify_loader.py','--candidate',candidate)
    log('borrowed logic direct/file native loader gate passes both seats.** Exact actions and rewards match fast-native controls. **Decision: run frozen independent confirmation; no promotion yet.** `diagnostics/borrowed_logic_20261001/loader_receipt.json`. No Kaggle actions.')
    extra=['--bbff-extra'] if expected_root==sha(HERE/'baseline_bbffbe65.py') else []
    run('run_experiment.py','confirm','--candidate',candidate,'--workers','6',*extra)
    run('report.py');decision=json.loads((HERE/'DECISION.json').read_text())
    log('borrowed logic independent native confirmation completed.** '+json.dumps(read('confirm')['assessment'])+'; confidence'+json.dumps(decision['confidence'])+'. **Decision: '+('qualifies for exact-byte integration' if decision['promotion_eligible'] else 'reject promotion; preserve current engine')+'.** All cases in `diagnostics/borrowed_logic_20261001/ALL_CASES.csv`. No Kaggle actions.')
    if not decision['promotion_eligible']:return
    assert sha(ROOT/'main.py')==expected_root,'Incumbent changed; preserve user edits.'
    package=ROOT/'kaggriculture_engine/borrowed';assert not package.exists(),'Preserve existing engine work.'
    package.mkdir();(package/'__init__.py').write_text('"""Competitively qualified donor adapters and exact standalone builder."""\n',encoding='utf-8')
    for file in ('adapters.py','build.py','baseline_4ea1d89a.py','donor_main_b9ef905e.py'):shutil.copyfile(HERE/file,package/file)
    shutil.copytree(HERE/'donor',package/'donor')
    subprocess.run([sys.executable,str(package/'build.py'),'--name',name,'--modes',*manifest['modes']],cwd=ROOT,check=True)
    rebuilt=package/f'candidate_{name}.py';assert sha(rebuilt)==sha(candidate)
    (package/'README.md').write_text('# Qualified borrowed engine components\n\nSelected modes: '+', '.join(manifest['modes'])+'. Builder packages exact frozen incumbent plus source-preserved donor adapters. The standalone candidate requires no workspace imports.\n\nQualification and every result: diagnostics/borrowed_logic_20261001/RESULTS.md and ALL_CASES.csv. Native confirmation keeps both seats together for uncertainty. No guaranteed wins or Kaggle upload.\n',encoding='utf-8')
    backup=ROOT/f'main_before_borrowed_logic_20261001_{expected_root[:8]}.py';frozen=ROOT/f'main_candidate_borrowed_logic_20261001_{sha(candidate)[:8]}.py'
    for source,destination in ((ROOT/'main.py',backup),(candidate,frozen)):
        if destination.exists():assert sha(source)==sha(destination)
        else:shutil.copyfile(source,destination)
    temp=ROOT/'main.borrowed_pending.py';assert not temp.exists();shutil.copyfile(candidate,temp)
    assert sha(temp)==sha(candidate) and sha(ROOT/'main.py')==expected_root
    os.replace(temp,ROOT/'main.py');assert sha(ROOT/'main.py')==sha(candidate)
    decision.update(promoted=True,root_main_sha256=sha(candidate),source_package=str(package),backup=str(backup),promotion_time_utc=datetime.now(timezone.utc).isoformat());write(HERE/'DECISION.json',decision)
    memory=(ROOT/'agent.md').read_text(encoding='utf-8');start=memory.index('Current local competition artifact,');end=memory.index('\n\n',start)
    text='Current local competition artifact, **'+decision['promotion_time_utc']+'**: borrowed logic '+name+' promoted after all frozen gates; exact **'+sha(candidate)+'**. Qualified inspectable source package `kaggriculture_engine/borrowed`; byte-identical rebuild verified. Previous incumbent preserved as `'+backup.name+'`. Full independent native confidence: '+json.dumps(decision['confidence'])+'. All cases `diagnostics/borrowed_logic_20261001/ALL_CASES.csv`; fixed replay panels are only preservation controls. No Kaggle access/upload; universal wins or top10 are not established.'
    (ROOT/'agent.md').write_text(memory[:start]+text+memory[end:],encoding='utf-8')
    log('borrowed logic exact tested winner integrated into engine and locally promoted.** '+sha(candidate)+'; rebuilt bytes match; incumbent and candidate backed up. **Decision: promote qualified modes '+','.join(manifest['modes'])+'.** No Kaggle upload.')
    run('report.py')

if __name__=='__main__':main()
