"""Record a verified upload without altering prior research decisions."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from upload_once import HERE, ROOT, DIGEST, MAIN_DIGEST, read, sha


def replace_paragraph(text, marker, replacement):
    start = text.index(marker)
    end = text.index('\n\n', start)
    return text[:start] + replacement + text[end:]


def main():
    receipt = read(HERE / 'upload_receipt.json')
    loader = read(HERE / 'loader_parity.json')
    assert receipt['upload_returncode'] == 0 and receipt['candidate_sha256'] == DIGEST
    assert receipt['submission_id'] == int(receipt['kaggle_submission']['ref'])
    assert loader['passed'] and loader['action_reward_parity'] and len(loader['rows']) == 8
    assert sha(ROOT / 'main.py') == MAIN_DIGEST and sha(HERE / 'main.py') == DIGEST
    submission = receipt['kaggle_submission']
    submission_id = receipt['submission_id']
    uploaded = datetime.fromisoformat(submission['date']).replace(tzinfo=timezone.utc)
    utc = uploaded.strftime('%Y-%m-%d %H:%M:%S UTC')
    ist = uploaded.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime('%Y-%m-%d %H:%M:%S IST')
    status = submission['status'].split('.')[-1]
    score = submission.get('publicScore')
    score_text = f'public score **{score}**' if score not in (None, '') else 'no score yet'
    memory = ROOT / 'agent.md'
    text = memory.read_text(encoding='utf-8')
    assert f'submission **{submission_id}**' not in text, 'Upload state already recorded.'
    with (HERE / 'agent_before_upload_status.md').open('xb') as stream:
        stream.write(memory.read_bytes())
    current = (
        f'Current fresh-replay research status, **2026-09-30 IST**: experimental candidate '
        f'`main_candidate_fresh_replay_20260930_4802aa95.py` (SHA-256 `{DIGEST}`) remains '
        '**rejected for research promotion**. It improves the newest saved top100 from132/200 to156/200 '
        'and top20 from32/40 to36/40; two reserved sets improve263/400 to269/400. However, the frozen '
        'reacting screen changes baseline34W/30D/0L to34W/26D/4L. The greater-than90% goal is unmet. '
        f'Following the user\'s fresh explicit request, exact4802 was uploaded as experimental submission '
        f'**{submission_id}** at {utc} ({ist}). Root `main.py` remains exact4eeac9c3. '
        'Eight subsequent upload-specific native direct/file-loader games passed in both seats with exact '
        'action/reward parity; this does not reverse the failed performance gate. The historical conditional '
        'research checks were skipped and the untouched32-seed confirmation remains unrun. Research report: '
        '`diagnostics/fresh90_improvement_20260929/RESULTS.md`. Upload evidence: '
        '`diagnostics/upload_fresh_replay_20260930_4802aa95/loader_parity.json` and `upload_receipt.json`.')
    text = replace_paragraph(text, 'Current fresh-replay research status,', current)
    latest = (
        f'Latest user-authorized experimental upload: submission **{submission_id}**, `main.py`, exact '
        f'SHA-256 `{DIGEST}`, uploaded {utc} ({ist}). Authenticated listing verified at '
        f"{receipt['verified_at_utc']} is **{status}**, {score_text}. Root `main.py` remains exact4eeac9c3; "
        'the research-promotion decision remains rejected. Receipt: '
        '`diagnostics/upload_fresh_replay_20260930_4802aa95/upload_receipt.json`. '
        'Previous submission56680167/cb76fbc4 was uploaded2026-09-29 15:22:07UTC; its historical '
        '17:04:25UTC check was COMPLETE at1840.6 with27 public episodes. That score is not the new upload\'s score.')
    text = replace_paragraph(text, 'Latest user-authorized experimental upload:', latest)
    minimum = min(row['minimum_remaining_overage'] for row in loader['rows'])
    finding = (
        f'- **{utc} — exact4802 uploaded once at the user\'s fresh explicit request.** Kaggle accepted '
        f'submission **{submission_id}** as `main.py`; listing verified **{status}**, {score_text}. '
        'All8 bounded native direct/file-loader games passed: both seats on the prior loader control12929001 '
        'and already-exposed regression seed22929006, DONE/DONE/720,719 calls per player, no runtime or '
        f'policy errors, exact full action/reward parity, minimum remaining overage{minimum:.6f} seconds. '
        'The correct last callable is `kaggle_fresh_execution_schedule_entrypoint`. The request '
        '"ok so can you upload that new candidate to the kaggle please" is consumed for this single upload. '
        '**Decision: fulfill the explicitly requested experimental upload; retain research rejection because '
        'the reacting screen added four losses.** No proven rating gain or greater-than90% result. '
        'Root main4ee and all historical research receipts are preserved; untouched confirmation seeds '
        'were not used. Evidence and exact submitted bytes: '
        '`diagnostics/upload_fresh_replay_20260930_4802aa95/loader_parity.json`, `upload_receipt.json`, `main.py`.\n\n')
    marker = '## Mission and operating constraints\n\n'
    assert marker in text
    text = text.replace(marker, marker + finding, 1)
    memory.write_text(text, encoding='utf-8')
    print(f'Recorded submission {submission_id}: {status}; {utc}; {ist}.', flush=True)


if __name__ == '__main__': main()
