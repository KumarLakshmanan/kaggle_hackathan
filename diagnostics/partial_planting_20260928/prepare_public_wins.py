from datetime import datetime,timezone
from pathlib import Path
import gzip
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    source=ROOT/'diagnostics/new_live_56609430_20260927/cohort_180951.json'
    raw=source.read_bytes()
    assert sha(raw)=='2e37cf158c4e28edcc3e044c6b7d3fd84d4bfc5a983b31e1aeeee5a2986f0116'
    cohort=json.loads(raw)
    wins=[g for g in cohort['games'] if g['result']=='win'];assert len(wins)==54
    tapes=HERE/'public_win_tapes';tapes.mkdir(exist_ok=True)
    fixtures=[]
    for game in sorted(wins,key=lambda g:int(g['episode_id'])):
        path=Path(game['replay_path']);raw=gzip.decompress(path.read_bytes())
        assert sha(raw)==game['replay_sha256']
        replay=json.loads(raw)
        assert replay['module_version']=='1.32.7' and len(replay['steps'])==720
        seat=int(game['candidate_seat']);episode=int(game['episode_id'])
        actions=[frame[1-seat].get('action') or {} for frame in replay['steps'][1:]]
        action_sha=sha(json.dumps(actions,separators=(',',':')).encode())
        assert float(replay['rewards'][seat])==float(game['own_cash'])
        assert float(replay['rewards'][1-seat])==float(game['opponent_cash'])
        assert float(game['own_cash'])>float(game['opponent_cash'])
        tape=tapes/f'win-{episode}.json.gz'
        payload=dict(actions=actions,source_episode=episode,source_replay_sha256=game['replay_sha256'])
        if tape.exists():assert json.loads(gzip.decompress(tape.read_bytes()))==payload
        else:tape.write_bytes(gzip.compress(json.dumps(payload,separators=(',',':')).encode(),mtime=0))
        fixtures.append(dict(fixture_id=f'public-win-{episode}',episode_id=episode,team=game['opponent'],
            seed=int(game['seed']),source_candidate_seat=seat,source_replay_path=str(path.resolve()),
            source_replay_sha256=game['replay_sha256'],source_action_tape_path=str(tape.resolve()),
            source_opponent_action_sha256=action_sha,source_candidate_reward=float(game['own_cash']),
            source_opponent_reward=float(game['opponent_cash'])))
    target=HERE/'public_win_manifest.json'
    result=dict(complete=True,cohort_sha256=sha(source.read_bytes()),plan_sha256=sha((HERE/'PUBLIC_WIN_PLAN.md').read_bytes()),
                created_at_utc=datetime.now(timezone.utc).isoformat(),fixtures=fixtures,
                scope='All 54 saved source wins; opposite-seat baselines have not been inferred or evaluated here.')
    assert not target.exists();target.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Verified local public-win fixtures:',len(fixtures),'manifest SHA',sha(target.read_bytes()))


if __name__=='__main__':main()
