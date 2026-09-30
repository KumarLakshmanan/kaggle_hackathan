"""Measure old archived fixture tradeoffs without changing promotion criteria."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
ARCHIVE=ROOT/'diagnostics/combined_agent_257f_20260929/saved_panel'
sys.path.insert(0,str(ROOT))
from diagnostics.stream_replay_io_20260928.fast_game_cached import play
from diagnostics.local_target_20260928.run_lock import exclusive_run

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def execute(job):
    case,path,digest=job
    row=play(case['fixture'],path,digest,case['candidate_seat'])
    return dict(case_id=case['case_id'],group=case['group'],**row)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('version');args=parser.parse_args()
    manifest=json.loads((HERE/f'manifest_{args.version}.json').read_text())
    assert sha(manifest['candidate'])==manifest['candidate_sha256']
    reference_receipt=json.loads((ARCHIVE/'comparison_manifest_receipt.json').read_text())
    assert sha(ARCHIVE/'comparison_manifest_results.jsonl')==reference_receipt['rows_sha256']
    source=json.loads((ARCHIVE/'comparison_manifest.json').read_text())
    assert sha(ARCHIVE/'comparison_manifest.json')==reference_receipt['manifest_sha256']
    reference={r['case_id']:r for r in map(json.loads,(ARCHIVE/'comparison_manifest_results.jsonl').read_text().splitlines())}
    assert len(reference)==len(source['cases'])==102
    path=HERE/f'archive_{args.version}.jsonl'
    with exclusive_run(ROOT/'diagnostics/.shared_game_run.lock'):
        rows=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
        done={r['case_id'] for r in rows}
        with path.open('a',encoding='utf-8',newline='\n') as stream:
            with ProcessPoolExecutor(max_workers=4) as pool:
                pending={pool.submit(execute,(case,manifest['candidate'],manifest['candidate_sha256'])):case
                         for case in source['cases'] if case['case_id'] not in done}
                for future in as_completed(pending):
                    row=future.result();rows.append(row)
                    stream.write(json.dumps(row,ensure_ascii=True)+'\n');stream.flush()
                    if len(rows)%10==0:print(f"{len(rows)}/102 {row['case_id']} {row['result']}",flush=True)
        groups={}
        for name in sorted({r['group'] for r in rows}):
            chosen=[r for r in rows if r['group']==name];ids={r['fixture_id'] for r in chosen}
            groups[name]=dict(games=len(chosen),wins=sum(r['result']=='win' for r in chosen),
                draws=sum(r['result']=='draw' for r in chosen),losses=sum(r['result']=='loss' for r in chosen),
                both_seat_wins=sum(all(r['result']=='win' for r in chosen if r['fixture_id']==fid) for fid in ids))
        flips=[dict(case_id=r['case_id'],group=r['group'],old=reference[r['case_id']]['candidate']['result'],
                    new=r['result'],old_margin=reference[r['case_id']]['candidate']['margin'],new_margin=r['margin'])
               for r in rows if reference[r['case_id']]['candidate']['result']!=r['result']]
        receipt=dict(complete=len(rows)==102,candidate_sha256=manifest['candidate_sha256'],groups=groups,flips=flips,
            clean=all(r['candidate_status']==r['opponent_status']=='DONE' and r['frames']==720 and not r['candidate_errors'] for r in rows),
            source_manifest_sha256=sha(ARCHIVE/'comparison_manifest.json'),
            reference_results_sha256=sha(ARCHIVE/'comparison_manifest_results.jsonl'),
            results_sha256=sha(path),completed_at_utc=datetime.now(timezone.utc).isoformat(),
            development_diagnostic_only=True)
        (HERE/f'archive_{args.version}_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        print(json.dumps(receipt,indent=2),flush=True)

if __name__=='__main__':main()
