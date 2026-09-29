"""Create an immutable, explicit comparison manifest; never executes agents."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'diagnostics/upload_pet_source_guard_20260929_257f941d/main.py'
PANEL = ROOT / 'diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/panel.json'
RECEIPT = ROOT / 'diagnostics/pet_source_guard_20260929/preservation_receipt.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['pilot', 'saved_panel', 'reactive'])
    parser.add_argument('candidate', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    candidate = args.candidate.resolve(strict=True)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    assert not output.exists(), 'Frozen manifests are never overwritten'
    assert sha(BASE) == '257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55'
    assert sha(PANEL) == 'fee3b1d5f93cd295c28dd8d0c04ea672806dbb55e2b59999853a9f969c0fb90d'
    assert sha(RECEIPT) == '4086a1ebd23431efedcbd178a7e5367cc1e84d8999b1843a4e62d891aa5f2997'
    manifest = {
        'schema': 'combined-agent-comparison-v1', 'phase': args.phase,
        'execution_workers': 1,
        'baseline': {'label': 'uploaded257', 'path': str(BASE), 'sha256': sha(BASE)},
        'candidate': {'label': 'new_candidate', 'path': str(candidate), 'sha256': sha(candidate)},
        'research_plan_path': str(HERE / 'PLAN.md'), 'research_plan_sha256': sha(HERE / 'PLAN.md'),
        'cases': [],
    }
    if args.phase == 'reactive':
        opponents = [
            ('research4ee', ROOT / 'main.py', '4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'),
            ('uploaded257', BASE, sha(BASE)),
            ('publicAhmedV35', ROOT / 'diagnostics/public_ahmed_v35_20260927/public_v35_main.py',
             '294e7e4d9d4b97413646960d318043e0f9116ce58f42fe02afd4716614a4e96d'),
        ]
        manifest.update(fresh_native=True, original_shop=True)
        for seed in range(2026092981, 2026092985):
            for name, path, digest in opponents:
                assert sha(path) == digest
                for seat in (0, 1):
                    manifest['cases'].append({
                        'case_id': f'{name}-{seed}-seat{seat}', 'group': 'reactive',
                        'seed': seed, 'candidate_seat': seat,
                        'opponent': {'id': name, 'path': str(path), 'sha256': digest},
                    })
    else:
        panel = json.loads(PANEL.read_text(encoding='utf-8'))
        for row in panel['games'] + panel['controls']:
            fixture = row['fixture']
            seat = row.get('candidate_seat', row.get('seat'))
            fixture_id = fixture['fixture_id']
            if args.phase == 'pilot':
                if fixture_id not in ('live-114218866', 'live-114249897'):
                    continue
                group = 'target' if fixture_id == 'live-114218866' else 'control'
            else:
                group = row.get('panel', 'pet_public_win_control')
            manifest['cases'].append({
                'case_id': f'{fixture_id}-seat{seat}', 'group': group,
                'candidate_seat': seat, 'fixture': fixture,
            })
        manifest['source_panel'] = {'path': str(PANEL), 'sha256': sha(PANEL)}
        if args.phase == 'saved_panel':
            # Reader schema is finalized by the comparison runner before execution.
            manifest['baseline_reference'] = {
                'receipt_path': str(RECEIPT), 'receipt_sha256': sha(RECEIPT),
                'panel_path': str(PANEL), 'panel_sha256': sha(PANEL),
            }
        assert len(manifest['cases']) == (4 if args.phase == 'pilot' else 102)
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=True)
        stream.write('\n')
    print(json.dumps({'path': str(output), 'sha256': sha(output),
                      'candidate_sha256': sha(candidate), 'case_count': len(manifest['cases'])}))


if __name__ == '__main__':
    main()
