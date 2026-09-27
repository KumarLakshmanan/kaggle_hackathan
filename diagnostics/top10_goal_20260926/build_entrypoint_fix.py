"""Append a unique final callable for Kaggle's get_last_callable loader."""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "main.py"
OUTPUT = ROOT / "exp_entrypoint_fix_20260926.py"
EXPECTED_SOURCE = "0e2c30f44ca7a6e0181e38a8d378af1f266ffacaaef33983a1673061797d647a"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SOURCE
code = SOURCE.read_text(encoding="utf8")
assert "def kaggle_main_entrypoint(" not in code
addon = '''

# Kaggle's file loader selects the last newly inserted callable in source
# order. Keep this unique entrypoint last, after every helper definition.
def kaggle_main_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
OUTPUT.write_text(code + addon, encoding="utf8")
print("candidate_sha256=" + hashlib.sha256(OUTPUT.read_bytes()).hexdigest())
print(OUTPUT)
