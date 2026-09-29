"""Sequential orchestration only; all strategy gates live in frozen study.py."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.local_target_20260928.run_lock import exclusive_run


def read(name): return json.loads((HERE/name).read_text(encoding='utf-8'))
def sha(name): return hashlib.sha256((HERE/name).read_bytes()).hexdigest()


def main():
    controls=read('controls.json')
    assert controls['complete'] and controls['clean'] and controls['pool_sha256']==sha('pool.json')
    bindings=read('finish_manifest.json')
    for name,digest in bindings.items(): assert sha(name)==digest, name
    for phase,receipt in [('conditional','conditional.json'),('select','selection.json'),('full','full.json')]:
        if not (HERE/receipt).exists():
            print('Starting unchanged stage:',phase,flush=True)
            subprocess.run([sys.executable,'-X','utf8',str(HERE/'study.py'),phase],cwd=ROOT,check=True)
        completed=read(receipt)
        assert completed['complete'] and completed['pool_sha256']==sha('pool.json')
    if not (HERE/'decision.json').exists():
        subprocess.run([sys.executable,'-X','utf8',str(HERE/'report.py')],cwd=ROOT,check=True)
    print('All frozen production-leaf stages terminal; inspect decision.json. No promotion or upload.',flush=True)


if __name__=='__main__':
    with exclusive_run(HERE/'finish.lock'): main()
