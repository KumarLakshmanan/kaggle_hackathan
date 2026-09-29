from __future__ import annotations
import ast, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'main_candidate_pet_source_guard_20260929_257f941d.py'
OUTPUT = HERE / 'candidate_257f_melon_delivery.py'
EXPECTED_SOURCE_SHA256 = '257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55'
WRAPPER_BUILDER = ROOT / 'diagnostics' / 'a44_melon_delivery_margin_20260929' / 'build_candidate.py'
EXPECTED_WRAPPER_BUILDER_SHA256 = '52fd610e8a6578369e7feaf81412dbbd944a045af04dbdaa257775ecfb914e83'
EXPECTED_REBASED_WRAPPER_SHA256 = 'de237a9928b6bde20f8f882d75128491d591d5098384bdc105973c8cf38dde2e'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    actual = sha(SOURCE)
    if actual != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f'source hash mismatch: {actual}')
    wrapper_builder_sha = sha(WRAPPER_BUILDER)
    if wrapper_builder_sha != EXPECTED_WRAPPER_BUILDER_SHA256:
        raise SystemExit(f'wrapper builder hash mismatch: {wrapper_builder_sha}')
    tree = ast.parse(WRAPPER_BUILDER.read_text(encoding='utf-8'))
    wrapper = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'APPEND' for t in node.targets):
            wrapper = ast.literal_eval(node.value)
            break
    if not isinstance(wrapper, str) or '_A44_MELON' not in wrapper:
        raise SystemExit('could not extract hash-reviewed melon wrapper')
    wrapper = wrapper.replace('_A44_MELON', '_P257_MELON')
    wrapper = wrapper.replace('Isolated wrapper: frozen step-713 selector plus a player-keyed route latch.',
                              'Isolated 257f wrapper: frozen step-713 selector plus a player-keyed route latch.')
    wrapper_sha = hashlib.sha256(wrapper.encode('utf-8')).hexdigest()
    if wrapper_sha != EXPECTED_REBASED_WRAPPER_SHA256:
        raise SystemExit(f'rebased wrapper hash mismatch: {wrapper_sha}')
    source_bytes = SOURCE.read_bytes()
    OUTPUT.write_bytes(source_bytes + wrapper.encode('utf-8'))
    digest = sha(OUTPUT)
    manifest = {
        'schema': '257f-melon-margin-candidate-v1',
        'source_path': str(SOURCE.relative_to(ROOT)),
        'source_sha256': actual,
        'wrapper_builder_source': str(WRAPPER_BUILDER.relative_to(ROOT)),
        'wrapper_builder_sha256': wrapper_builder_sha,
        'wrapper_sha256': wrapper_sha,
        'candidate_path': str(OUTPUT.relative_to(ROOT)),
        'candidate_sha256': digest,
        'uses_exact_257f_parent_agent': True,
        'root_main_modified': False,
        'outcome_games_run': False,
    }
    (HERE / 'build_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    main()
