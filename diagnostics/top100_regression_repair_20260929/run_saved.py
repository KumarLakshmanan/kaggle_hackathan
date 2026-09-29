"""Checkpointed regression panel; opponent tapes are development evidence only."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIOR = ROOT / 'diagnostics/submission_top100_compare_20260929_1104'
sys.path[:0] = [str(ROOT), str(PRIOR)]
from fast_game_current import play
from diagnostics.local_target_20260928.run_lock import exclusive_run

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def execute(job):
    entry, seat, path, digest = job
    fixture = dict(fixture_id=str(entry['team_id']), seed=int(entry['seed']),
                   source_replay_path=entry['replay_path'], source_replay_sha256=entry['replay_sha256'],
                   source_action_tape_path=entry['path'], source_opponent_action_sha256=entry['action_sha256'])
    try:
        row = play(fixture, path, digest, seat)
    except Exception as error:
        row = dict(candidate_seat=seat, error_type=type(error).__name__, error=str(error))
    return dict(rank=entry['rank'], team_id=entry['team_id'], team=entry['team'],
                seed=entry['seed'], episode_id=entry['episode_id'], **row)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('version')
    parser.add_argument('phase', choices=('pilot', 'full'))
    args = parser.parse_args()
    manifest = json.loads((HERE / f'manifest_{args.version}.json').read_text())
    assert sha(manifest['candidate']) == manifest['candidate_sha256']
    assert sha(PRIOR / 'local_results.jsonl') == '7ba72ea62b9b399ccc8dc1099a2d86c09ec9e8670b0a63b068d58fd309596832'
    originals = [json.loads(line) for line in (PRIOR / 'local_results.jsonl').read_text(encoding='utf-8').splitlines()]
    baselines = {name: {(r['rank'], r['candidate_seat']):r for r in originals if r['label']==name}
                 for name in ('4eeac9c3', 'ae349d83')}
    entries = json.loads((PRIOR / 'routes/summary.json').read_text(encoding='utf-8'))
    flipped = {rank for rank, seat in baselines['4eeac9c3']
               if baselines['4eeac9c3'][rank,seat]['result'] != baselines['ae349d83'][rank,seat]['result']}
    if args.phase == 'pilot':
        entries = [entry for entry in entries if entry['rank'] in flipped]
    path = HERE / f'saved_{args.version}.jsonl'
    with exclusive_run(ROOT / 'diagnostics/.shared_game_run.lock'):
        previous = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
        assert all(r['candidate_sha256'] == manifest['candidate_sha256'] for r in previous)
        done = {(r['rank'], r['candidate_seat']) for r in previous}
        jobs = [(entry, seat, manifest['candidate'], manifest['candidate_sha256'])
                for entry in entries for seat in (0,1) if (entry['rank'],seat) not in done]
        start = datetime.now(timezone.utc).isoformat()
        rows = list(previous)
        with path.open('a', encoding='utf-8', newline='\n') as stream:
            with ProcessPoolExecutor(max_workers=4) as pool:
                pending = {pool.submit(execute, job): job for job in jobs}
                for future in as_completed(pending):
                    row = future.result()
                    stream.write(json.dumps(row, ensure_ascii=True)+'\n'); stream.flush()
                    rows.append(row)
                    if len(rows)%10 == 0 or len(rows)==len(entries)*2:
                        print(f"{len(rows)}/{len(entries)*2} rank={row['rank']} seat={row['candidate_seat']} {row.get('result', row.get('error_type'))}", flush=True)
        selected = [r for r in rows if r['rank'] in {e['rank'] for e in entries}]
        clean = all(not r.get('error') and not r.get('candidate_errors') and
                    r['frames']==720 and r['candidate_status']==r['opponent_status']=='DONE' for r in selected)
        assert len(selected)==len(entries)*2
        outcome = {'complete': True, 'started_at_utc':start, 'finished_at_utc':datetime.now(timezone.utc).isoformat(),
                   'candidate_sha256':manifest['candidate_sha256'], 'phase':args.phase,
                   'plan_sha256':manifest['plan_sha256'], 'results_sha256':sha(path),
                   'games':len(selected), 'clean':clean,
                   'wins':sum(r.get('result')=='win' for r in selected),
                   'draws':sum(r.get('result')=='draw' for r in selected),
                   'losses':sum(r.get('result')=='loss' for r in selected),
                   'both_seat_wins':sum(all(r.get('result')=='win' for r in selected if r['rank']==e['rank']) for e in entries),
                   'comparisons': {}}
        for name, baseline in baselines.items():
            improved, regressed = [], []
            for row in selected:
                old=baseline[row['rank'],row['candidate_seat']]
                item=dict(rank=row['rank'],team=row['team'],seat=row['candidate_seat'],old_result=old['result'],
                          new_result=row.get('result'),old_margin=old['margin'],new_margin=row.get('margin'))
                if row.get('result')=='win' and old['result']!='win': improved.append(item)
                elif row.get('result')!='win' and old['result']=='win': regressed.append(item)
            outcome['comparisons'][name]={'improved':improved,'regressed':regressed}
        target_ranks={rank for rank,seat in baselines['4eeac9c3'] if baselines['4eeac9c3'][rank,seat]['result']=='win' and baselines['ae349d83'][rank,seat]['result']=='loss'}
        outcome['recovered_regressed_teams']=sum(all(r.get('result')=='win' for r in selected if r['rank']==rank) for rank in target_ranks)
        outcome['regression_gate_passed']=(clean and outcome['recovered_regressed_teams']==9 and
                                           not outcome['comparisons']['4eeac9c3']['regressed'])
        if args.phase=='full': outcome['regression_gate_passed'] &= outcome['wins']>141
        (HERE / f'saved_{args.version}_{args.phase}_receipt.json').write_text(json.dumps(outcome,indent=2),encoding='utf-8')
        print(json.dumps(outcome,indent=2),flush=True)

if __name__=='__main__': main()
