"""Run the final bounded repair checks sequentially under the shared lock."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def main():
    commands = [
        ['run_saved.py', 'v3', 'full'],
        ['run_reactive_v3.py', 'v3', 'screen'],
        ['verify_native.py', 'v3'],
        ['verify_loader.py', 'v3'],
        ['run_reactive_v3.py', 'v3', 'confirm'],
        ['run_archive.py', 'v3'],
    ]
    if sys.argv[1:] == ['--resume-confirm']:
        commands = commands[4:]
    else:
        assert not sys.argv[1:]
    for command in commands:
        print('STAGE', ' '.join(command), flush=True)
        subprocess.run([sys.executable, '-X', 'utf8', '-u', '-B', *command], cwd=HERE, check=True)


if __name__ == '__main__':
    main()
