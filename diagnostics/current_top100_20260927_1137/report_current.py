"""Report all snapshot rows; exclude our self-control from strength counts."""
from collections import Counter
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def write(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf8')


if __name__=='__main__':
    manifest=json.loads((HERE/'manifest.json').read_text())
    assessment=json.loads((HERE/'assessment.json').read_text())
    context=json.loads((HERE/'source_context.json').read_text())
    assert manifest['complete'] and assessment['complete'] and context['complete']
    entries=[e for e in manifest['rows'] if 'action_sha256' in e]
    games=assessment['games']
    assert len(games)==2*len(entries)
    shops={r['team_id']:r['states']['144']['shops'] for r in context['rows']}
    errors=Counter()
    for g in games:
        for k,v in (g.get('candidate_telemetry') or {}).items():
            if k.endswith('errors') or k=='integration_gate_collisions':
                errors[k]+=int(v or 0)
    rows=[]
    for e in entries:
        pair=sorted([g for g in games if g['team_id']==e['team_id']],key=lambda g:g['candidate_seat'])
        assert [g['candidate_seat'] for g in pair]==[0,1]
        rows.append(dict(rank=e['rank'],team=e['team'],team_id=e['team_id'],
                         self_control=e.get('self_control',False),source_episode_id=e['episode_id'],
                         source_time_utc=e['create_time'],margins=[g['margin'] for g in pair],
                         results=[g['result'] for g in pair],sweep=all(g['result']=='win' for g in pair)))
    external=[r for r in rows if not r['self_control']]
    failed=[r for r in external if not r['sweep']]
    self_rows=[r for r in rows if r['self_control']]
    assert len(self_rows)==1
    failed_ids={r['team_id'] for r in failed}
    source_differences={g['team_id'] for g in games if not g.get('self_control') and g['candidate_capture']['shops']!=shops[g['team_id']]}
    prior0730=json.loads((ROOT/'diagnostics/current_top100_20260927_0730/manifest.json').read_text())['rows']
    prior50=json.loads((ROOT/'diagnostics/top50_refresh_20260927_2303/routes/summary.json').read_text())
    overlaps={name:dict(team_ids=len({r['team_id'] for r in entries}&{r['team_id'] for r in prior}),
                        episode_ids=len({r['episode_id'] for r in entries}&{r['episode_id'] for r in prior}))
              for name,prior in (('today_0727',prior0730),('original50',prior50))}
    group=assessment['groups']['top100']
    live_cohort=json.loads((ROOT/'diagnostics/disjoint_live_audit_20260927/cohort_1137.json').read_text())
    live_by_episode={g['episode_id']:g for g in live_cohort['games']}
    live_checks=[]
    for e in entries:
        live=live_by_episode.get(e['episode_id'])
        if not live or e.get('self_control') or e['team']!=live['opponent']:
            continue
        g=next(g for g in games if g['team_id']==e['team_id'] and g['candidate_seat']==live['candidate_seat'])
        assert g['candidate_reward']==live['own_cash'] and g['opponent_reward']==live['opponent_cash']
        live_checks.append(dict(episode_id=e['episode_id'],team=e['team'],seat=live['candidate_seat'],
                               own_cash=g['candidate_reward'],rival_cash=g['opponent_reward'],both_cash_match=True))
    passed=(group['teams_completed']==group['both_seat_sweeps']==99 and group['seat_wins']==198
            and group['all_done'] and not any(errors.values()))
    summary=dict(candidate_sha256=assessment['candidate_sha256'],leaderboard_snapshot_utc=manifest['leaderboard_snapshot_utc'],
                 groups=assessment['groups'],downloaded_snapshot_rows=len(entries),external_teams=len(external),
                 unique_episodes=manifest['unique_episodes'],self_controls=self_rows,
                 oldest_replay_utc=min(e['create_time'] for e in entries),newest_replay_utc=max(e['create_time'] for e in entries),
                 prior_panel_overlap=overlaps,prior_results_reused=0,error_counts=dict(errors),
                 all_200_done=all(g['candidate_status']==g['opponent_status']=='DONE' and g['frames']==720 for g in games),
                 external_teams_with_shop_prefix_difference_at_144=len(source_differences),
                 all_current_external_top100_target_passed=passed,non_swept_teams=failed,
                 completed_at_utc=assessment['completed_at_utc'])
    summary['overlapping_live_cash_checks']=live_checks
    write(HERE/'summary.json',summary)
    write(HERE/'non_swept_routes.json',[e for e in entries if e['team_id'] in failed_ids])
    write(HERE/'non_swept_context.json',[dict(rank=g['rank'],team=g['team'],seed=g['seed'],seat=g['candidate_seat'],
          margin=g['margin'],native_capture_144=g['candidate_capture'],source_shops_144=shops[g['team_id']],
          telemetry=g.get('candidate_telemetry')) for g in games if g['team_id'] in failed_ids])
    lines=['# Current top100 assessment — 11:37 UTC, 27 September 2026','',
           f"Exact uploaded c68fa46f wins **{group['both_seat_sweeps']}/99 external matchups in both seats** and **{group['seat_wins']}/198 external games**.",
           f"Draws: {group['seat_draws']}; losses: {group['seat_losses']}. All-current-opponent target {'passes this recorded panel' if passed else 'remains unachieved'}.",'',
           '| Snapshot group | External teams tested | Both-seat sweeps | Wins | Draws | Losses |',
           '|---|---:|---:|---:|---:|---:|']
    for limit in (10,50,100):
        g=assessment['groups'][f'top{limit}'];n=g['teams_requested']
        lines.append(f"| Top {limit} | {g['teams_completed']}/{n} | {g['both_seat_sweeps']}/{n} | {g['seat_wins']}/{2*n} | {g['seat_draws']} | {g['seat_losses']} |")
    control=self_rows[0]
    lines+=['','Our own team is rank98 in this snapshot. Its recorded tape is a separate self-control,',
            f"with results {control['results']} and margins {control['margins']}; it is excluded from the external counts.",
            f"All100 snapshot rows were covered and all200 total games finished DONE/DONE/720: **{summary['all_200_done']}**.",
            f"Recorded error totals: {dict(errors)}.",'','## Freshness and interpretation','',
            f"Official snapshot: **{manifest['leaderboard_snapshot_utc']}**.",
            f"All sources were freshly queried and downloaded. Their games were created between **{summary['oldest_replay_utc']}** and **{summary['newest_replay_utc']} UTC**; {manifest['unique_episodes']} distinct raw episodes cover100 team tapes.",
            f"Episode overlap with the07:27 panel: {overlaps['today_0727']['episode_ids']}; with the original50: {overlaps['original50']['episode_ids']}. No earlier game outcomes were reused.",'',
            'Each source is the latest complete public episode of the higher-scoring active submission, selected without looking at rewards. Both seats use the recorded seed and original native shops. The candidate stayed frozen.',
            f"The native shop prefix differs from the recording at turn144 for {len(source_differences)}/99 external teams in at least one seat.",'',
            f"For the{len(live_checks)} selected episodes also present in our complete live audit, both final cash totals exactly match the real Kaggle game in the original seat. No extra games or previous test outcomes were reused for this comparison.",'',
            "These are recorded action tapes, not private reacting policies. They cannot adapt to our decisions. The new and earlier panels have different games and membership; their scores do not measure an improvement to unchanged c68. Native reactive checks remain necessary for a new candidate, and this panel cannot predict live rank.",'',
            '## External matchups not won in both seats','',
            '| Snapshot rank | Team | Seat0 margin | Seat1 margin |','|---:|---|---:|---:|']
    for r in failed:
        name=r['team'].replace('|','\\|')
        lines.append(f"| {r['rank']} | {name} | {r['margins'][0]:+,.0f} | {r['margins'][1]:+,.0f} |")
    lines+=['','## Decision','',
            'Accept the complete fresh assessment. '+('The recorded-opponent goal passes on this snapshot only.' if passed else 'Reject the claim that c68 beats every current top100 opponent.'),
            'Preserve all failures and prior panels. No policy change, promotion or additional upload. Live top10 remains a separate unfinished objective.','',
            'Evidence: PLAN.md, snapshot.json, manifest.json, listings/, raw_archive/, assessment.json, source_context.json, summary.json and MATCHUPS.md.']
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    lines=['# All100 fresh snapshot matchups','',f"Snapshot: {manifest['leaderboard_snapshot_utc']}; candidate c68fa46f.",'',
           '| Rank | Team | Role | Replay | Created UTC | Seat0 margin | Seat1 margin | Both seats won |',
           '|---:|---|---|---:|---|---:|---:|---|']
    for r in rows:
        name=r['team'].replace('|','\\|');role='Self-control' if r['self_control'] else 'External opponent'
        lines.append(f"| {r['rank']} | {name} | {role} | {r['source_episode_id']} | {r['source_time_utc']} | {r['margins'][0]:+,.0f} | {r['margins'][1]:+,.0f} | {'Yes' if r['sweep'] else 'No'} |")
    (HERE/'MATCHUPS.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('non_swept_teams','self_controls')},indent=2),flush=True)
