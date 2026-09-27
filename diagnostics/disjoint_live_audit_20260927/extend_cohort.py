"""Audit every episode in a saved live listing, preserving verified history."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import json
from pathlib import Path
import sys
from collect import collect, HERE


if __name__ == '__main__':
    snapshot, previous_path, label = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    source = snapshot / 'episodes.json'
    previous = json.loads(previous_path.read_text(encoding='utf8'))
    assert previous['complete']
    listing = json.loads(source.read_text(encoding='utf8'))
    chosen = [e for e in listing if 'PUBLIC' in str(e['type']) and str(e['state']).endswith('COMPLETED')]
    old_ids = {g['episode_id'] for g in previous['games']}
    assert old_ids <= {e['id'] for e in chosen}
    for g in previous['games']:
        assert hashlib.sha256(gzip.decompress(Path(g['replay_path']).read_bytes())).hexdigest() == g['replay_sha256']
    target = HERE / ('cohort_' + label + '.json')
    assert not target.exists()
    out = dict(started_at_utc=datetime.now(timezone.utc).isoformat(), submission_id=56602057,
               listing=str(source.resolve()), listing_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
               selection=f'All {len(chosen)} completed public episodes in the saved listing; no outcome filter',
               reused_verified_episodes=len(old_ids), complete=False, games=previous['games'].copy())
    def save():
        target.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf8')
    save()
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(collect, e) for e in chosen if e['id'] not in old_ids]):
            g = future.result()
            out['games'].append(g)
            out['games'].sort(key=lambda g: (g['listing']['createTime'], g['episode_id']))
            save()
            print(f"{len(out['games'])}/{len(chosen)} {g['episode_id']} {g['result']} {g['margin']:+} vs {g['opponent']}", flush=True)
    assert len(out['games']) == len(chosen)
    out.update(complete=True, completed_at_utc=datetime.now(timezone.utc).isoformat(),
               wins=sum(g['result'] == 'win' for g in out['games']),
               losses=sum(g['result'] == 'loss' for g in out['games']),
               draws=sum(g['result'] == 'draw' for g in out['games']),
               all_done=all(g['statuses'] == ['DONE','DONE'] and g['frames'] == 720 for g in out['games']))
    save()
    with (snapshot / 'leaderboard.csv').open(encoding='utf-8-sig', newline='') as f:
        board = list(csv.DictReader(f))
    context = []
    for g in out['games']:
        teams = [t for t in board if t['TeamName'] == g['opponent']]
        context.append(dict(episode_id=g['episode_id'], opponent=g['opponent'], matches=teams))
    (HERE / ('opponent_context_' + label + '.json')).write_text(json.dumps(context, indent=2, ensure_ascii=False), encoding='utf8')
    live = json.loads((snapshot / 'summary.json').read_text())
    lines = [f'# Live c68 cohort — {live["checked_at_utc"]}', '',
             f"All {len(chosen)} completed public episodes: **{out['wins']} wins, {out['losses']} losses, {out['draws']} draws**.",
             f"All DONE/DONE/720: {out['all_done']}. Reused {len(old_ids)} prior replays only after hash verification;",
             'downloaded every newly listed game without outcome filtering.', '',
             f"Official team rank **{live['our_team']['Rank']}**, c68 score **{live['new_submission']['publicScore']}**.",
             f"Rank-10 score: {live['rank10']['Score']}. Top-10 objective remains unachieved.", '',
             '| Episode | Opponent | Result | Margin | Snapshot team rank |', '|---|---|---|---:|---:|']
    for g, c in zip(out['games'], context):
        rank = c['matches'][0]['Rank'] if len(c['matches']) == 1 else 'unresolved'
        name = g['opponent'].replace('|','\\|')
        lines.append(f"| {g['episode_id']} | {name} | {g['result']} | {g['margin']:+,} | {rank} |")
    lines += ['', 'Ranks are team ranks at the snapshot, not opposing submission ratings at game time.',
              '**Decision:** accept the verified live audit. No candidate promotion or new upload.',
              f'Evidence: cohort_{label}.json, opponent_context_{label}.json, raw receipts and {snapshot.name}.', '']
    (HERE / ('RESULTS_' + label + '.md')).write_text('\n'.join(lines), encoding='utf8')
    print(json.dumps({k:v for k,v in out.items() if k != 'games'}, indent=2), flush=True)
