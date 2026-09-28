"""Attach one consistent leaderboard snapshot rank to the final cohort."""
import csv
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
cohort_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / 'cohort_164140.json'
cohort = json.loads(cohort_path.read_text(encoding='utf8'))
snapshot = Path(cohort['snapshot_path'])
with (snapshot / 'leaderboard.csv').open(encoding='utf-8-sig', newline='') as stream:
    board = list(csv.DictReader(stream))
by_name = {}
for team in board:
    by_name.setdefault(team['TeamName'], []).append(dict(rank=team['Rank'], team_id=team['TeamId'],
                                                         score=team['Score']))
changed = 0
for game in cohort['games']:
    old = game['opponent_snapshot_ranks']
    new = by_name.get(game['opponent'], [])
    assert len(new) == 1, (game['episode_id'], game['opponent'], new)
    if old != new:
        changed += 1
        game.setdefault('opponent_initial_snapshot_ranks', old)
    game['opponent_snapshot_ranks'] = new
    game['opponent_rank_snapshot_path'] = str(snapshot.resolve())
cohort_path.write_text(json.dumps(cohort, indent=2, ensure_ascii=False), encoding='utf8')
print(json.dumps(dict(final_snapshot=snapshot.name, games=len(cohort['games']),
                      changed_rank_rows=changed, ambiguous_ranks=0)), flush=True)
