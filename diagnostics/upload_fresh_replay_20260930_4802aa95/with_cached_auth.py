"""Use Kaggle's cached OAuth login without printing or persisting an access token."""
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from upload_once import KAGGLE, COMPETITION, _run_json, write, now, submit_once


def main():
    assert sys.argv[1:] in (['--check'], ['--submit-once'])
    refreshed = subprocess.run([KAGGLE, 'auth', 'print-access-token'], capture_output=True,
                               text=True, encoding='utf-8', errors='replace', timeout=60)
    token = refreshed.stdout.strip()
    if refreshed.returncode != 0 or len(token) < 40 or any(char.isspace() for char in token):
        print(json.dumps(dict(auth_restored=False, oauth_command_returncode=refreshed.returncode,
                              reason='Cached OAuth did not produce a usable token. No token output was logged.')))
        raise SystemExit(1)
    previous = os.environ.get('KAGGLE_API_TOKEN')
    os.environ['KAGGLE_API_TOKEN'] = token
    try:
        if sys.argv[1:] == ['--submit-once']:
            submit_once()
        else:
            listing = _run_json(KAGGLE, ['competitions', 'submissions', COMPETITION, '--page-size', '10'])
            write(HERE / 'authenticated_probe.json', dict(checked_at_utc=now(), submissions=listing))
            print(json.dumps(dict(auth_restored=True, latest_submission_ids=[row['ref'] for row in listing[:3]],
                                  upload_attempted=False)))
    finally:
        if previous is None:
            os.environ.pop('KAGGLE_API_TOKEN', None)
        else:
            os.environ['KAGGLE_API_TOKEN'] = previous
        token = None


if __name__ == '__main__': main()
