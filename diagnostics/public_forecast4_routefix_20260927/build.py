"""Reconstruct only reviewed literal source substitutions; do not run cells."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_DIR = ROOT / 'diagnostics/public_refresh_20260927_0812/leoprovorov'
UPSTREAM = '4f8637a3e33348b98f531de246d353f5d2955b2f85480e3fd02bf4a7874f0d01'


if __name__ == '__main__':
    notebook = SOURCE_DIR / 'four-turn-forecast-notebook-version-2.ipynb'
    document = json.loads(notebook.read_text(encoding='utf8'))
    source = (SOURCE_DIR / 'extracted_upstream/main.py').read_bytes()
    assert hashlib.sha256(source).hexdigest() == UPSTREAM
    cell = ''.join(document['cells'][5]['source'])
    wanted = {'_anchor1', '_replacement1', '_anchor2', '_replacement2'}
    strings = {}
    for node in ast.walk(ast.parse(cell)):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in wanted:
                assert name not in strings
                strings[name] = ast.literal_eval(node.value)
    assert set(strings) == wanted and all(isinstance(x, str) for x in strings.values())
    text = source.decode('utf8')
    assert '_HH_REMAP_20260924' not in text
    for number in (1, 2):
        anchor, replacement = strings[f'_anchor{number}'], strings[f'_replacement{number}']
        assert text.count(anchor) == 1
        text = text.replace(anchor, replacement, 1)
    tree = ast.parse(text)
    last_function = [n for n in tree.body if isinstance(n, ast.FunctionDef)][-1].name
    assert last_function == 'herdsafe_forecast_agent'
    payload = text.encode('utf8')
    digest = hashlib.sha256(payload).hexdigest()
    candidate = ROOT / 'exp_public_forecast4_routefix_20260927.py'
    backup = ROOT / ('main_candidate_public_forecast4_routefix_20260927_' + digest[:8] + '.py')
    assert not candidate.exists() and not backup.exists()
    candidate.write_bytes(payload)
    backup.write_bytes(payload)
    licenses = {}
    for name in ('LICENSE.txt', 'NOTICE.txt'):
        content = (SOURCE_DIR / 'extracted_upstream' / name).read_bytes()
        (HERE / name).write_bytes(content)
        (ROOT / (backup.stem + '.' + name)).write_bytes(content)
        licenses[name] = hashlib.sha256(content).hexdigest()
    manifest = dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
                    notebook=str(notebook), notebook_sha256=hashlib.sha256(notebook.read_bytes()).hexdigest(),
                    upstream_sha256=UPSTREAM, candidate=str(candidate), candidate_sha256=digest,
                    backup=str(backup), entrypoint=last_function, literal_patch=strings,
                    license_hashes=licenses, notebook_cells_executed=False,
                    plan_sha256=hashlib.sha256((HERE / 'PLAN.md').read_bytes()).hexdigest())
    (HERE / 'build_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    print(json.dumps({k:v for k,v in manifest.items() if k != 'literal_patch'}, indent=2))
