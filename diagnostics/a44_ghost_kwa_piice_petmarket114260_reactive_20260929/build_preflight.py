from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PLAN = HERE / 'PLAN.md'
JOBS = HERE / 'jobs.json'
FROZEN = HERE / 'frozen_manifest.json'

CANDIDATE = ROOT / 'diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/candidate.py'
PARENT = ROOT / 'diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/candidate.py'
LAYER = ROOT / 'diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/layer.py'
ROUTE_SOURCE = ROOT / 'diagnostics/public_90_research_20260928/candidates/PET_CAFE_113517834.py'
PRIOR = ROOT / 'diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929'
PASTURE = ROOT / 'diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929'
BASELINE = PASTURE / 'goalpanel_100_retry_20260929'
RUN_HELPER = ROOT / 'diagnostics/opening_probe_v2_20260928/qualify.py'
BENCHMARK = ROOT / 'paired_benchmark.py'
RUN_LOCK = ROOT / 'diagnostics/local_target_20260928/run_lock.py'
UPLOADED = ROOT / 'diagnostics/upload_adaptive_donor_20260928_a44c8c2c/main.py'
REVISION = HERE / 'revisions/64_job_plan_20260929'

REVISION_EXPECTED = {
    'PLAN.md': '177cf6b2e6356e5660a3242078260b0993d8918d6d85da000cb080c079c0a53d',
    'build_preflight.py': 'd74231fb362bb2c334a94d6a40ccf5d49d63f6214d57bfcfce82a5090be40239',
    'run.py': '06dfdf2cf474979090a11153467f8843b764b0adb89e65da3d2176329d8d1fb5',
    'jobs.json': 'ba342a9734c28f47e8e1433819a268bd3025f7c613b7bf4462e3011f6f9daed4',
    'frozen_manifest.json': '3b06dcc2ba468b362543eea49bfc0240de8e62263ad8e0128ff40fd5d9b3dd70',
    'snapshot_manifest.json': 'a11063f86cea27a8c2c97ff96ff78c9a4e4a1206d0a13984fe674385b8ea7a63',
    'SNAPSHOT.md': '33048580dd53c859dc1e490eb7d487a3b0a2d9316752f3ae98d591cfd0ce8b66',
}

EXPECTED = {
    str(CANDIDATE): 'ebfbe6e91008cf39d1929d52a60e3cb140d2b1cffdd3fac8e06c122eb9876bbe',
    str(PARENT): '6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc',
    str(ROOT / 'main.py'): '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed',
    str(UPLOADED): 'a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f',
    str(ROOT / 'diagnostics/public_ahmed_v35_20260927/public_v35_main.py'): '294e7e4d9d4b97413646960d318043e0f9116ce58f42fe02afd4716614a4e96d',
    str(ROOT / 'diagnostics/public_rayk_top_meta/public_c95_main.py'): '489f5d197527f107027626cce79d850fd2ca90edd43d94384b849b6511e27bdb',
    str(LAYER): '2987829c7964671abd84e3b6eee568690096b716de21208bf4d83366e8f020d2',
    str(ROUTE_SOURCE): 'cd6b3ba4526599e93d1125e2143fffb639ce7eebed1d0bf41171be18173f57f8',
    str(PRIOR / 'outcome_receipt.json'): 'ec2f45acfa6a7988868bb13e657a639e546ced46d148c15456e78679b0d7dcb5',
    str(PRIOR / 'outcomes.jsonl'): 'bb1ae8bd2f3a9b892508ce77f101397596fd4d73868791425e6d667fb0bff97a',
    str(PRIOR / 'frozen_manifest.json'): '2e376dcaffbcaf9557b5cade1a84e66e751f64b9cc550a07dbd9604cdeab34dc',
    str(PRIOR / 'static_preflight.json'): '8230bf1c90be2cdb82609c672e7c42ab7cae81d45c5ba9dc77bd9dc0c6a149e3',
    str(BASELINE / 'outcome_receipt.json'): 'f5b962c853b8812f231c85af41a608e6df1b1ede99dd14c22a2bcaebb10bc8b2',
    str(BENCHMARK): '03b51c034cd556057d20efcd95d7ba260e3474e71c1357e37e62cf6ae51e8395',
    str(RUN_HELPER): 'c4bae3c9c6a5b322693baf97303ebac83f21f905d2bc0345bd53a0f1fc779f3c',
    str(RUN_LOCK): '6ae76386c4bfda83a5efff6c0772ad22a4480155126ac9f0ed5616ec68c0d219',
}

SEEDS = (2026092911, 2026092912, 2026092913, 2026092914)
PARENT_SHA = EXPECTED[str(PARENT)]
CANDIDATE_SHA = EXPECTED[str(CANDIDATE)]
UPLOADED_SHA = EXPECTED[str(UPLOADED)]
OPPONENTS = (
    ('current_main', ROOT / 'main.py', EXPECTED[str(ROOT / 'main.py')]),
    ('six_a_parent', PARENT, PARENT_SHA),
    ('public_v35', ROOT / 'diagnostics/public_ahmed_v35_20260927/public_v35_main.py',
     EXPECTED[str(ROOT / 'diagnostics/public_ahmed_v35_20260927/public_v35_main.py')]),
    ('public_c95', ROOT / 'diagnostics/public_rayk_top_meta/public_c95_main.py',
     EXPECTED[str(ROOT / 'diagnostics/public_rayk_top_meta/public_c95_main.py')]),
)
VERSIONS = (
    ('uploaded_a44c8c2c', UPLOADED, UPLOADED_SHA),
    ('parent_6a', PARENT, PARENT_SHA),
    ('pet_candidate', CANDIDATE, CANDIDATE_SHA),
)
OUTPUTS = {
    'outcomes': str((HERE / 'outcomes.jsonl').resolve()),
    'receipt': str((HERE / 'outcome_receipt.json').resolve()),
    'run_manifest': str((HERE / 'run_manifest.json').resolve()),
    'run_lock': str((HERE / 'qualification.lock').resolve()),
}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def engine_source_path() -> Path:
    spec = importlib.util.find_spec('kaggle_environments')
    if spec is None or spec.origin is None:
        raise AssertionError('installed kaggle_environments package is unavailable')
    return (Path(spec.origin).resolve().parent / 'envs/kaggriculture/kaggriculture.py').resolve()


def jobs_for_plan():
    plan_sha = sha(PLAN)
    jobs = []
    for seed in SEEDS:
        for opponent_id, opponent_path, opponent_sha in OPPONENTS:
            for seat in (0, 1):
                for version_id, path, digest in VERSIONS:
                    jobs.append({
                        'job_id': f'{seed}:{opponent_id}:{seat}:{version_id}',
                        'version': version_id,
                        'path': str(path.resolve()),
                        'candidate_sha256': digest,
                        'opponent_id': opponent_id,
                        'opponent': str(opponent_path.resolve()),
                        'opponent_sha256': opponent_sha,
                        'seed': seed,
                        'candidate_seat': seat,
                        'plan_sha256': plan_sha,
                        'original_shop_seeded_episode': True,
                        'fixed_tape': False,
                    })
    return jobs


def external_inputs():
    result = dict(EXPECTED)
    engine_path = engine_source_path()
    engine_sha = sha(engine_path)
    assert engine_sha == 'bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e'
    result[str(engine_path)] = engine_sha
    return {str(Path(path).resolve()): digest for path, digest in sorted(result.items())}


def verify_preserved_64_revision():
    assert set(REVISION_EXPECTED) == {path.name for path in REVISION.iterdir() if path.is_file()}
    assert all(sha(REVISION / name) == digest for name, digest in REVISION_EXPECTED.items())
    snapshot = json.loads((REVISION / 'snapshot_manifest.json').read_text(encoding='utf-8'))
    assert snapshot['complete'] and snapshot['no_games_or_transitions_run']
    assert snapshot['source_manifest_sha256'] == REVISION_EXPECTED['frozen_manifest.json']
    assert snapshot['files'] == {name: digest for name, digest in REVISION_EXPECTED.items()
                                 if name not in ('snapshot_manifest.json', 'SNAPSHOT.md')}
    return snapshot


def internal_files():
    active = ('PLAN.md', 'build_preflight.py', 'run.py', 'jobs.json')
    result = {name: sha(HERE / name) for name in active}
    result.update({f'revisions/64_job_plan_20260929/{name}': digest
                   for name, digest in REVISION_EXPECTED.items()})
    return result


def build():
    verify_preserved_64_revision()
    # The prior staged 64-job plan is immutable in revisions/; only its active
    # plan files are replaced by this pre-outcome 96-job amendment.
    if FROZEN.exists():
        previous = json.loads(FROZEN.read_text(encoding='utf-8'))
        assert (previous.get('schema') == 'pet-reactive-original-shop-three-arm-pilot-frozen-v1'
                and previous.get('complete') is True
                and previous.get('diagnostic_only') is True
                and previous.get('promotion') is False
                and previous.get('planned_game_count') == 96
                and previous.get('candidate_sha256') == CANDIDATE_SHA
                and previous.get('parent_candidate_sha256') == PARENT_SHA
                and previous.get('uploaded_arm_sha256') == UPLOADED_SHA), \
            'only a prior unexecuted three-arm staging manifest may be refrozen'
    if JOBS.exists():
        previous_jobs = json.loads(JOBS.read_text(encoding='utf-8'))
        assert (previous_jobs.get('complete') is True
                and len(previous_jobs.get('jobs', [])) in (64, 96)), \
            'only the preserved two-arm or staged three-arm job list may be replaced'
    assert not any(Path(path).exists() for path in OUTPUTS.values())
    assert sha(CANDIDATE) == CANDIDATE_SHA and sha(PARENT) == PARENT_SHA
    assert sha(UPLOADED) == UPLOADED_SHA
    assert CANDIDATE.read_bytes() == PARENT.read_bytes() + b'\n\n' + LAYER.read_bytes()
    for path, expected_sha in EXPECTED.items():
        assert sha(Path(path)) == expected_sha, path
    for path in (CANDIDATE, PARENT, UPLOADED, *(entry[1] for entry in OPPONENTS)):
        tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
        assert any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == 'agent'
                   for node in tree.body), f'agent() not found: {path}'
    assert len(SEEDS) == len(set(SEEDS)) == 4
    assert max(SEEDS) < 2**31

    jobs = jobs_for_plan()
    identities = [job['job_id'] for job in jobs]
    assert len(jobs) == len(identities) == 96 and len(set(identities)) == 96
    assert len({job['seed'] for job in jobs}) == 4
    JOBS.write_text(json.dumps({'schema': 'pet-reactive-qualification-jobs-v1',
                                'complete': True, 'jobs': jobs}, indent=2) + '\n',
                    encoding='utf-8', newline='\n')
    manifest = {
        'schema': 'pet-reactive-original-shop-three-arm-pilot-frozen-v1',
        'complete': True,
        'diagnostic_only': True,
        'reactive_original_shop_episodes': True,
        'fixed_tape_only': False,
        'promotion': False,
        'engine_version': '1.32.7',
        'engine_source_sha256': 'bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e',
        'candidate_sha256': CANDIDATE_SHA,
        'parent_candidate_sha256': PARENT_SHA,
        'uploaded_arm_sha256': UPLOADED_SHA,
        'comparison_roles': {
            'primary': 'pet_candidate_vs_uploaded_a44c8c2c',
            'incremental': 'pet_candidate_vs_parent_6a',
        },
        'opponents': {name: digest for name, _, digest in OPPONENTS},
        'seed_block': list(SEEDS),
        'candidate_versions': [name for name, _, _ in VERSIONS],
        'planned_game_count': len(jobs),
        'jobs_sha256': sha(JOBS),
        'internal_files': internal_files(),
        'external_inputs': external_inputs(),
        'output_paths': OUTPUTS,
        'one_shot_runner': True,
        'root_release_required_before_any_game': True,
    }
    FROZEN.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    return manifest


def verify():
    verify_preserved_64_revision()
    manifest = json.loads(FROZEN.read_text(encoding='utf-8'))
    job_payload = json.loads(JOBS.read_text(encoding='utf-8'))
    assert manifest['complete'] and manifest['diagnostic_only']
    assert manifest['reactive_original_shop_episodes'] and not manifest['fixed_tape_only']
    assert not manifest['promotion'] and manifest['root_release_required_before_any_game']
    assert manifest['engine_version'] == '1.32.7'
    assert sha(JOBS) == manifest['jobs_sha256']
    assert job_payload['complete'] and job_payload['schema'] == 'pet-reactive-qualification-jobs-v1'
    jobs = job_payload['jobs']
    assert jobs == jobs_for_plan()
    assert len(jobs) == manifest['planned_game_count'] == 96
    assert all(sha(HERE / path) == digest for path, digest in manifest['internal_files'].items())
    assert all(sha(Path(path)) == digest for path, digest in manifest['external_inputs'].items())
    assert sha(CANDIDATE) == manifest['candidate_sha256'] == CANDIDATE_SHA
    assert sha(PARENT) == manifest['parent_candidate_sha256'] == PARENT_SHA
    assert sha(UPLOADED) == manifest['uploaded_arm_sha256'] == UPLOADED_SHA
    assert CANDIDATE.read_bytes() == PARENT.read_bytes() + b'\n\n' + LAYER.read_bytes()
    assert not any(Path(path).exists() for path in manifest['output_paths'].values()), \
        'one-shot output already exists; do not resume this panel'
    return manifest, jobs


if __name__ == '__main__':
    if '--verify' in sys.argv:
        manifest, jobs = verify()
        print(json.dumps({'verified': True, 'frozen': True,
                          'candidate_sha256': manifest['candidate_sha256'],
                          'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                          'uploaded_arm_sha256': manifest['uploaded_arm_sha256'],
                          'seed_block': manifest['seed_block'],
                          'opponent_count': len(manifest['opponents']),
                          'planned_games': len(jobs),
                          'native_game_runs_now': 0,
                          'engine_transitions_now': 0}, indent=2))
    else:
        manifest = build()
        print(json.dumps({'frozen': True,
                          'candidate_sha256': manifest['candidate_sha256'],
                          'parent_candidate_sha256': manifest['parent_candidate_sha256'],
                          'seed_block': manifest['seed_block'],
                          'opponents': list(manifest['opponents']),
                          'planned_games': manifest['planned_game_count'],
                          'engine_source_sha256': manifest['engine_source_sha256'],
                          'native_game_runs_now': 0}, indent=2))
