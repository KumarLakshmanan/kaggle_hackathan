"""Create immutable fixed-replay job manifests from collection summaries."""
import argparse
import json
from pathlib import Path
from run_panel import sha, HERE, ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('entries', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--max-rank', type=int, default=100)
    parser.add_argument('--ranks', default='')
    parser.add_argument('--traces', action='store_true')
    parser.add_argument('--trace-max-rank', type=int, default=100000)
    args = parser.parse_args()
    assert not args.output.exists(), 'Never overwrite a frozen job manifest'
    entries = json.loads(args.entries.read_text(encoding='utf-8'))
    ranks = set(map(int, args.ranks.split(','))) if args.ranks else None
    entries = [e for e in entries if int(e['rank']) <= args.max_rank and (ranks is None or int(e['rank']) in ranks)]
    digest = sha(args.source)
    jobs = []
    for entry in sorted(entries, key=lambda e: (int(e['rank']), int(e['episode_id']))):
        fixture = f"{entry['team_id']}:{entry['episode_id']}"
        for seat in (0, 1):
            job = dict(job_id=f"{args.label}:{fixture}:{seat}", fixture_id=fixture,
                       label=args.label, path=str(args.source.resolve()), candidate_sha256=digest,
                       candidate_seat=seat, rank=int(entry['rank']), team=entry['team'],
                       team_id=int(entry['team_id']), episode_id=int(entry['episode_id']),
                       seed=int(entry['seed']), action_sha256=entry['action_sha256'],
                       replay_sha256=entry['replay_sha256'], entry=entry)
            if args.traces and int(entry['rank']) <= args.trace_max_rank:
                trace_dir = args.output.parent / (args.output.stem + '_traces')
                trace_dir.mkdir(exist_ok=True)
                job['trace_path'] = str(trace_dir / f"rank{entry['rank']}_ep{entry['episode_id']}_s{seat}.jsonl.gz")
            jobs.append(job)
    assert jobs and len({j['job_id'] for j in jobs}) == len(jobs)
    args.output.write_text(json.dumps(jobs, indent=2), encoding='utf-8')
    print(json.dumps(dict(jobs=len(jobs), candidate_sha256=digest, entries_sha256=sha(args.entries),
                          jobs_sha256=sha(args.output)), indent=2))


if __name__ == '__main__':
    main()
