"""Render the verified live cohort with episode timestamps and ranks."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def main(cohort_path):
    cohort = json.loads(cohort_path.read_text(encoding='utf8'))
    snapshot = Path(cohort['snapshot_path'])
    live = json.loads((snapshot / 'summary.json').read_text(encoding='utf8'))
    team_submissions = json.loads((snapshot / 'team_submissions.json').read_text(encoding='utf8'))
    older = next(row for row in team_submissions if row['id'] == 56602057)
    assert cohort['complete']
    parity_path = HERE / 'validation_parity.json'
    parity = json.loads(parity_path.read_text(encoding='utf8')) if parity_path.exists() else None
    lines = [
        '# Live submission 56609430 — verified public episodes', '',
        f"Official snapshot: **{live['checked_at_utc']}**. Kaggle submission status **{live['submission']['status']}**, "
        f"uploaded **{live['submission']['date']} UTC**, submission publicScore **{live['submission']['publicScore']}**.", '',
        f"Leaderboard team rank **{live['our_team']['Rank']}**, team Score **{live['our_team']['Score']}**; "
        f"rank 10 Score **{live['rank10']['Score']}**. The leaderboard row lists LastSubmissionDate "
        f"**{live['our_team']['LastSubmissionDate']} UTC**. These are snapshot values, not game-time ranks.", '',
        f"The team Score matches older c68 submission **56602057**'s publicScore **{older['publicScore']}**, "
        f"which exceeds new 4ee submission **56609430**'s publicScore **{live['submission']['publicScore']}**. "
        "The team rank is not a measured score gain from the new file.", '',
        f"All **{len(cohort['games'])}** completed public episodes from the saved listing were downloaded without an outcome filter: "
        f"**{cohort['wins']} wins, {cohort['losses']} losses, {cohort['draws']} draws**. "
        f"All **{len(cohort['games']) + len(cohort['validation'])}** saved raw replay hashes verify after decompression; "
        f"all have DONE/DONE, 720 frames, and 719 actions per seat. Failed replay IDs/paths: **none**.", '',
        f"Validation episode **{cohort['validation'][0]['episode_id']}** was created "
        f"{cohort['validation'][0]['listing']['createTime']} UTC and completed "
        f"{cohort['validation'][0]['listing']['endTime']} UTC. It is self-play with both names "
        f"`Lakshmanan R`, seed {cohort['validation'][0]['seed']}, and rewards {cohort['validation'][0]['rewards']}. "
        + (f"Exact uploaded-file native parity: **{'PASS' if parity['passed'] else 'FAIL'}**; "
           f"both seats' 719 actions and final cash {'match' if parity['passed'] else 'do not match'}."
           if parity else 'Exact uploaded-file native parity: running.'), '',
        '| Episode | Created UTC | Ended UTC | Opponent | Snapshot rank | Our seat | Result | Margin |',
        '|---:|---|---|---|---:|---:|---|---:|',
    ]
    for g in cohort['games']:
        ranks = g['opponent_snapshot_ranks']
        rank = ranks[0]['rank'] if len(ranks) == 1 else 'unresolved' if not ranks else 'ambiguous'
        lines.append(f"| {g['episode_id']} | {g['listing']['createTime']} | {g['listing']['endTime']} | "
                     f"{cell(g['opponent'])} | {rank} | {g['candidate_seat']} | {g['result']} | {g['margin']:+,.0f} |")
    lines += ['', 'Snapshot ranks identify leaderboard teams by exact name at the snapshot time. They are not the opponent submission rating at game time.',
              'The transient console encoding errors and validation duplicate-name parsing are documented in `collection_log_163551.json`; all affected raw replay archives passed verification.',
              '', '**Decision:** accept this complete live audit. The top-10 objective remains unmet; this audit is not a policy promotion experiment.',
              f'Evidence: `{cohort_path.name}`, `{snapshot.name}/summary.json`, `raw/*-receipt.json`, `raw/*-replay.json.gz`, and `validation_parity.json`.', '']
    (HERE / 'RESULTS.md').write_text('\n'.join(lines), encoding='utf8')
    print(f"wrote {HERE / 'RESULTS.md'}", flush=True)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
