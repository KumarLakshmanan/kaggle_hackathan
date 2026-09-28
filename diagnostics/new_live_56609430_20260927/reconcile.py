"""Verify the complete saved cohort after a console encoding interruption."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat()


def main(cohort_path):
    cohort = json.loads(cohort_path.read_text(encoding='utf8'))
    snapshot = Path(cohort['snapshot_path'])
    listing = json.loads((snapshot / 'episodes.json').read_text(encoding='utf8'))
    by_id = {int(e['id']): e for e in listing}
    raw_dir = HERE / 'raw'
    receipts = {}
    for receipt_path in raw_dir.glob('episode-*-receipt.json'):
        row = json.loads(receipt_path.read_text(encoding='utf8'))
        eid = int(row['episode_id'])
        assert eid not in receipts, eid
        assert row['listing'] == by_id[eid], eid
        archive = Path(row['replay_path'])
        raw = gzip.decompress(archive.read_bytes())
        assert hashlib.sha256(raw).hexdigest() == row['replay_sha256'], eid
        replay = json.loads(raw)
        assert int(replay['info']['EpisodeId']) == eid, eid
        assert row['action_counts'] == [719, 719] and row['frames'] == 720 and row['statuses'] == ['DONE', 'DONE'], eid
        receipts[eid] = row
    public_ids = set(cohort['expected_public_ids'])
    assert set(receipts) == public_ids, (sorted(public_ids - set(receipts)), sorted(set(receipts) - public_ids))
    validation = []
    for eid in cohort['expected_validation_ids']:
        archive = raw_dir / f'episode-{eid}-replay.json.gz'
        raw = gzip.decompress(archive.read_bytes())
        replay = json.loads(raw)
        assert int(replay['info']['EpisodeId']) == eid
        frames = replay['steps']
        statuses = [x['status'] for x in frames[-1]]
        rewards = [x['reward'] for x in frames[-1]]
        action_counts = [sum(frame[seat].get('action') is not None for frame in frames[1:]) for seat in (0, 1)]
        assert len(frames) == 720 and statuses == ['DONE', 'DONE'] and action_counts == [719, 719]
        row = dict(episode_id=eid, listing=by_id[eid], replay_path=str(archive.resolve()),
                   replay_sha256=hashlib.sha256(raw).hexdigest(), source_bytes=len(raw),
                   team_names=replay['info']['TeamNames'], rewards=rewards, statuses=statuses,
                   action_counts=action_counts, frames=len(frames), seed=replay['info']['seed'],
                   module_version=replay['module_version'])
        assert row['team_names'] == ['Lakshmanan R', 'Lakshmanan R']
        (raw_dir / f'episode-{eid}-receipt.json').write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding='utf8')
        validation.append(row)
    (HERE / ('collection_log_' + cohort_path.stem.split('_')[-1] + '.json')).write_text(
        json.dumps(dict(original_failures=cohort['failures'], reconciled_at_utc=now(),
                        explanation='Three console encoding errors occurred after receipts were written; validation self-play has two identical team labels.'),
                   indent=2, ensure_ascii=False), encoding='utf8')
    cohort['games'] = sorted(receipts.values(), key=lambda r: (r['listing']['createTime'], r['episode_id']))
    cohort['validation'] = validation
    cohort['transient_collection_errors'] = cohort['failures']
    cohort['failures'] = []
    cohort['complete'] = True
    cohort['reconciled_at_utc'] = now()
    cohort['wins'] = sum(g['result'] == 'win' for g in cohort['games'])
    cohort['losses'] = sum(g['result'] == 'loss' for g in cohort['games'])
    cohort['draws'] = sum(g['result'] == 'draw' for g in cohort['games'])
    cohort['all_done_720_719'] = True
    cohort_path.write_text(json.dumps(cohort, indent=2, ensure_ascii=False), encoding='utf8')
    print(json.dumps(dict(complete=True, public=len(cohort['games']), wins=cohort['wins'],
                          losses=cohort['losses'], draws=cohort['draws'], validation=len(validation),
                          hash_verified=len(cohort['games']) + len(validation), failed_replay_ids=[])), flush=True)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
