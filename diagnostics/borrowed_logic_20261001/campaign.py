"""Sequential offline qualification. Never accesses Kaggle."""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def log(message):
    with (ROOT/'agent.md').open('a',encoding='utf-8') as out:
        out.write('\n\n- **'+datetime.now(timezone.utc).isoformat()+' — '+message+'\n')

def run(script,*args):
    subprocess.run([sys.executable,str(HERE/script),*map(str,args)],cwd=ROOT,check=True)

def main():
    prior=ROOT/'diagnostics/professional_engine_20261001/DECISION.json'
    while True:
        if prior.exists():
            d=json.loads(prior.read_text())
            if d.get('confidence') and (not d['promotion_eligible'] or d.get('promoted')):
                break
        print('Waiting for the frozen prior confirmation to finish.',flush=True)
        time.sleep(20)
    run('run_experiment.py','screen','--workers','6')
    r=json.loads((HERE/'screen_receipt.json').read_text())
    log('borrowed logic fresh development comparison completed.** '+json.dumps(r['assessment'])+'. **Decision: '+('advance survivor through frozen conditional gates' if r['assessment']['screen_survivor'] else 'reject all six additions; preserve qualified incumbent')+'.** Exact skipped cases and futility bounds in `diagnostics/borrowed_logic_20261001/screen_receipt.json`. No Kaggle actions.')
    run('report.py')
    if r['assessment']['screen_survivor']:
        run('advance.py')

if __name__=='__main__':main()
