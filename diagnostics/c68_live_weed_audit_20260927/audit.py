from collections import Counter
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def command(action,actor):
    if actor==0:return action.get('farmer') or ['PASS']
    hands=action.get('hands') or []
    return hands[actor-1] if actor<=len(hands) else ['PASS']


if __name__=='__main__':
    source=ROOT/'diagnostics/disjoint_live_audit_20260927/cohort_0929.json'
    cohort=json.loads(source.read_text());assert cohort['complete'] and len(cohort['games'])==34
    target=HERE/'audit.json';assert not target.exists()
    out=dict(started_at_utc=datetime.now(timezone.utc).isoformat(),source_cohort_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
             main_sha256='c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad',
             complete=False,independent_strength_evidence=False,games=[])
    def save():target.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
    save()
    for live in cohort['games']:
        raw=gzip.decompress(Path(live['replay_path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==live['replay_sha256']
        replay=json.loads(raw);seat=live['candidate_seat'];frames=replay['steps']
        blocked=[];plant_requests=Counter()
        for step in range(719):
            frame=frames[step];obs=dict(frame[0]['observation']);obs.update(frame[seat]['observation'])
            farm=obs['farms'][seat];action=frames[step+1][seat]['action']
            positions=[farm['farmer']]+farm['hands']
            for actor,pos in enumerate(positions):
                cmd=command(action,actor)
                if not cmd or cmd[0]!='PLANT' or len(cmd)<2:continue
                crop=cmd[1];plant_requests[crop]+=1
                tile=farm['tiles'][pos[1]][pos[0]]
                if not isinstance(tile,dict) or tile.get('kind')!='WEED':continue
                seed_stock=obs['private']['seeds'].get(crop,0)
                eligible=crop=='STRAWBERRY' and seed_stock>0 and step+3<719 and (step+3)//24==step//24
                if eligible:
                    future=[frames[step+i+1][seat]['action'] for i in range(3)]
                    eligible=command(future[1],actor)==['WATER'] and command(future[2],actor)==['PASS']
                    for act in future:
                        for other,c in enumerate([act.get('farmer') or ['PASS']]+(act.get('hands') or [])):
                            if other!=actor and c and (c[0]=='PLANT' or c[0].startswith('BUILD')):eligible=False
                blocked.append(dict(step=step,actor=actor,position=pos,crop=crop,seed_stock=seed_stock,
                                    strict_same_day_window=bool(eligible)))
        row=dict(episode_id=live['episode_id'],opponent=live['opponent'],result=live['result'],margin=live['margin'],
                 replay_sha256=live['replay_sha256'],plant_requests=dict(plant_requests),weed_blocked_requests=blocked,
                 strict_windows=sum(r['strict_same_day_window'] for r in blocked))
        out['games'].append(row);save()
        print(f"{len(out['games'])}/34 {live['episode_id']} weed_blocked={len(blocked)} strict_windows={row['strict_windows']}",flush=True)
    out.update(complete=True,completed_at_utc=datetime.now(timezone.utc).isoformat(),
               total_plant_requests=sum(sum(g['plant_requests'].values()) for g in out['games']),
               total_weed_blocked=sum(len(g['weed_blocked_requests']) for g in out['games']),
               total_strict_windows=sum(g['strict_windows'] for g in out['games']))
    save();print('RESULT '+json.dumps({k:v for k,v in out.items() if k!='games'}),flush=True)
