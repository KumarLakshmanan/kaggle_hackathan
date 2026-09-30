"""Continue the frozen stages after the currently running regression panel."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

if __name__ == '__main__':
    receipt = HERE / 'qualification_progress.json'
    assert not receipt.exists()
    out = dict(started_at_utc=datetime.now(timezone.utc).isoformat(), phase='waiting_for_panels', complete=False)
    def save():
        out['updated_at_utc'] = datetime.now(timezone.utc).isoformat()
        receipt.write_text(json.dumps(out,indent=2),encoding='utf8')
    save()
    while True:
        try:
            panel = json.loads((HERE / 'panels.json').read_text())
        except json.JSONDecodeError:
            time.sleep(2)
            continue
        if panel['complete']:
            break
        time.sleep(15)
    if not panel['passed']:
        out.update(phase='panels_rejected', complete=True, passed=False)
        save()
        raise SystemExit(0)
    for phase, arguments in [('confirmation',['native.py','confirmation']), ('loader',['verify_loader.py'])]:
        out['phase'] = phase
        save()
        response = subprocess.run([sys.executable,'-B','-X','utf8',str(HERE/arguments[0]),*arguments[1:]],cwd=str(ROOT))
        if response.returncode:
            out.update(phase=phase+'_harness_stopped',complete=True,passed=False,returncode=response.returncode)
            save()
            raise SystemExit(response.returncode)
        filename = 'confirmation.json' if phase == 'confirmation' else 'loader_parity.json'
        result = json.loads((HERE / filename).read_text())
        if not result['passed']:
            out.update(phase=phase+'_rejected',complete=True,passed=False)
            save()
            raise SystemExit(0)
    out.update(phase='qualified_for_review',complete=True,passed=True)
    save()
    print('All frozen qualification stages passed. No upload was performed by this runner.',flush=True)
