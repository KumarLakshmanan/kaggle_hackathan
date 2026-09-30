"""Finish already-frozen phases sequentially after the live target worker exits."""
from pathlib import Path
import argparse
import ctypes
import json
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from diagnostics.local_target_20260928.run_lock import exclusive_run


def run(script, *args):
    print('Starting', script, *args, flush=True)
    subprocess.run([sys.executable, '-X', 'utf8', str(HERE / script), *args], cwd=ROOT, check=True)


def main(pid):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    kernel.WaitForSingleObject.restype = ctypes.c_ulong
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x00100000 | 0x1000, 0, pid)
    if handle:
        print(f'Waiting for verified target worker PID{pid} to exit before starting another benchmark.', flush=True)
        try:
            while kernel.WaitForSingleObject(handle, 15000) == 0x102:
                pass
        finally:
            kernel.CloseHandle(handle)
    assert (HERE / 'target.json').exists(), 'Target worker exited without a completed320-game receipt; no follow-up phase starts.'
    target = json.loads((HERE / 'target.json').read_text(encoding='utf-8'))
    assert target['complete'] and target['clean'] and target['game_count'] == 320
    if not (HERE / 'shortlist.json').exists(): run('research.py', 'shortlist')
    if not (HERE / 'matched_features72.json').exists(): run('features.py', 'matched')
    if not (HERE / 'feature_parity.json').exists(): run('audit_features.py')
    assert json.loads((HERE / 'feature_parity.json').read_text(encoding='utf-8'))['passed']
    short = json.loads((HERE / 'shortlist.json').read_text(encoding='utf-8'))
    if not short['passed']:
        print('Frozen representative family rejected: no target rescue. Feature inventory remains available.', flush=True)
        return
    if not (HERE / 'retention.json').exists(): run('research.py', 'retention')
    if not (HERE / 'selection.json').exists(): run('research.py', 'select')
    selection = json.loads((HERE / 'selection.json').read_text(encoding='utf-8'))
    if not selection['passed']:
        print('Frozen representative family rejected: no qualifying win-preserving candidate.', flush=True)
        return
    if not (HERE / 'combined_full.json').exists(): run('full.py')
    print('Frozen development workflow completed. Native/reacting promotion gates remain outside this workflow.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--target-pid', type=int, required=True)
    args = parser.parse_args()
    with exclusive_run(HERE / 'finish.lock'): main(args.target_pid)
