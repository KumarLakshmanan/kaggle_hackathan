"""Minimal repair: source-bound diagnostics and a fresh 32-seed native block."""
import json
import sys
import run_reactive as runner

DEVELOPMENT = (12929001, 12929008, 12929107, 12929108,
               12929115, 12929201, 12929209, 12929210)
ORIGINAL_MAKE_JOBS = runner.make_jobs


def make_jobs(manifest, stage):
    template = ORIGINAL_MAKE_JOBS(manifest, stage)
    prototypes = [j for j in template if j['seed'] == min(r['seed'] for r in template)]
    seeds = DEVELOPMENT if stage == 'screen' else range(12929301, 12929333)
    jobs = []
    reference = {}
    if stage == 'screen':
        for version, name in [('v1', 'screen'), ('v1', 'confirm'), ('v2', 'confirm')]:
            path = runner.HERE / f'reactive_{version}_{name}.jsonl'
            receipt = json.loads((runner.HERE / f'reactive_{version}_{name}_receipt.json').read_text())
            assert runner.sha(path) == receipt['results_sha256']
            for row in map(json.loads, path.read_text().splitlines()):
                if row['version'] == '4ee' and row['seed'] in DEVELOPMENT:
                    reference[row['job_id']] = dict(row, reused_from=str(path),
                                                   reused_ledger_sha256=runner.sha(path))
    for seed in seeds:
        for proto in prototypes:
            job = dict(proto, seed=seed,
                       job_id=f"{seed}:{proto['rival']}:{proto['candidate_seat']}:{proto['version']}")
            if job['job_id'] in reference:
                job['method'] = reference[job['job_id']]['method']
            jobs.append(job)
    if stage == 'screen':
        output = runner.HERE / 'reactive_v3_screen.jsonl'
        if not output.exists():
            assert len(reference) == 64
            with output.open('x', encoding='utf-8', newline='\n') as stream:
                for job in jobs:
                    if job['job_id'] not in reference:
                        continue
                    row = reference[job['job_id']]
                    assert all(row[k] == job[k] for k in
                               ('candidate_sha256', 'opponent_sha256', 'method'))
                    stream.write(json.dumps(row, ensure_ascii=True) + '\n')
    return jobs


if __name__ == '__main__':
    assert sys.argv[1] == 'v3'
    runner.make_jobs = make_jobs
    runner.main()
