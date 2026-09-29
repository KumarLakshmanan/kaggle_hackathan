"""Run the remaining frozen V2 checks sequentially, one game coordinator at a time."""
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def main():
    saved = json.loads((HERE / 'saved_v2_full_receipt.json').read_text())
    assert saved['regression_gate_passed']
    commands = [
        ['run_reactive_v2.py', 'v2', 'screen'],
        ['verify_native.py', 'v2'],
        ['verify_loader.py', 'v2'],
        ['run_reactive_v2.py', 'v2', 'confirm'],
        ['run_archive.py', 'v2'],
        ['write_report_v2.py'],
    ]
    if sys.argv[1:] == ['--resume-confirm']:
        commands = commands[3:]
    else:
        assert not sys.argv[1:]
    for command in commands:
        print('STAGE', ' '.join(command), flush=True)
        subprocess.run([sys.executable, '-X', 'utf8', '-u', '-B', *command], cwd=HERE, check=True)


if __name__ == '__main__':
    main()
