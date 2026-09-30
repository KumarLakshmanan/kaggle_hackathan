"""Static early-melon command scan over selected latest-episode tape payloads."""
import glob, hashlib, json, runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = []
for candidate_path in sorted(HERE.glob('candidate_*.py')):
    if candidate_path.name.endswith('.previous'):
        continue
    module = runpy.run_path(str(candidate_path))
    candidate_sha = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    for rank, tape in sorted(module['_TAPES'].items()):
        first_seed = None
        first_plant = None
        for action_index, action in enumerate(tape['actions']):
            for order in action.get('market', []) or []:
                if (isinstance(order, list) and len(order) >= 2 and
                        order[0] == 'BUY_SEED' and order[1] == 'MELON' and first_seed is None):
                    first_seed = action_index
            worker_actions = [action.get('farmer', [])] + (action.get('hands', []) or [])
            for worker_action in worker_actions:
                if (isinstance(worker_action, list) and len(worker_action) >= 2 and
                        worker_action[0] == 'PLANT' and worker_action[1] == 'MELON' and first_plant is None):
                    first_plant = action_index
        rows.append({
            'candidate_file': candidate_path.name,
            'candidate_sha256': candidate_sha,
            'frozen_rank': int(rank),
            'first_buy_seed_melon_action_offset': first_seed,
            'first_plant_melon_action_offset': first_plant,
            'interpretation': 'recorded action command only; no claim that the action succeeded in the source replay',
        })
report = {
    'scope': 'Read only selected candidate action payloads; no outcomes, reserved tapes, games, or network calls.',
    'turns_per_day': 24,
    'offsets_are_zero_based': True,
    'records': rows,
    'all_selected_tapes_issue_melon_seed_and_plant_commands_by_action_offsets': [
        min((r['first_buy_seed_melon_action_offset'], r['first_plant_melon_action_offset'])
            for r in rows),
        max((r['first_buy_seed_melon_action_offset'], r['first_plant_melon_action_offset'])
            for r in rows),
    ],
    'game_runs': 0,
}
(HERE / 'melon_support.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'path': str((HERE / 'melon_support.json').resolve()), 'records': len(rows),
                  'offsets': [(r['frozen_rank'], r['first_buy_seed_melon_action_offset'],
                               r['first_plant_melon_action_offset']) for r in rows]}, indent=2))
