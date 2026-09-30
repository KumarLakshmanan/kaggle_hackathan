"""Bind two standalone bridge variants and all prefix inputs before outcomes."""
from pathlib import Path
from datetime import datetime,timezone
import base64
import hashlib
import importlib.util
import json
import zlib

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'main_candidate_animal_liquidity_20260928_32e299fe.py'
SOURCE_SHA='32e299fe047a79290d5025b4e2be455ae13d948020beae2d77cb44a7c17dc31e'
DONOR=ROOT/'diagnostics/donor_opening_agents_20260928'
INPUT=ROOT/'diagnostics/stream_replay_io_20260928'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path,obj):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,ensure_ascii=False)
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def main():
    assert sha(SOURCE)==SOURCE_SHA
    donor=read(DONOR/'pool.json')
    assert sha(DONOR/'pool.json')=='df180024fc540f5341fbfde7b164c99b0d98f9e9130faab1030ac143e22eb7d5'
    assert read(INPUT/'cached_helper_parity.json')['passed']
    manifest_path=ROOT/'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
    assert sha(manifest_path)=='524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
    manifest=read(manifest_path);fixtures=manifest['live_losses']+manifest['current_top20']
    fixture=lambda episode:next(f for f in fixtures if f['episode_id']==episode)
    donor_code={}
    for name in ('shared151','shared150'):
        arm=donor['arms'][name]
        assert sha(arm['candidate'])==arm['candidate_sha256']
        donor_code[name]=Path(arm['candidate']).read_text(encoding='utf-8')
    payload=base64.b85encode(zlib.compress(json.dumps(donor_code).encode())).decode()
    bridge_prefix='\n_BRIDGE_DONOR_CODE = json.loads(zlib.decompress(base64.b85decode('+repr(payload)+')))\n'
    arms={};checks=[]
    for variant in ('five_hand','five_or_zero'):
        path=HERE/('candidate_'+variant+'.py')
        code=SOURCE.read_bytes()+bridge_prefix.encode()+('_BRIDGE_VARIANT = '+repr(variant)+'\n').encode()+(HERE/'layer.py').read_bytes()
        compile(code,str(path),'exec')
        with path.open('xb') as f:f.write(code)
        mod=module(path,'bridge_preflight_'+variant)
        assert mod._DATA['opening'][0]==mod._BRIDGE_COMMON and mod._DATA['opening'][1]==mod._BRIDGE_SOURCE_ONE
        assert mod._PLANT_CORE['_parse_order'](['SELL','STRAWBERRY',0]) is None
        assert mod._ITERATED_QUEUE_RAW.__globals__ is mod.__dict__
        for name,ns in mod._BRIDGE_DONORS.items():
            assert ns['_ITERATED_QUEUE_RAW'] is ns['_donor_action'] and ns['_QUEUE_PARENT'] is ns['_donor_action']
            assert ns['_donor_action'].__globals__ is ns and ns['_hire_recovery_schedule'].__globals__ is ns
            assert all(route[0]==mod._BRIDGE_COMMON for route in ns['_DONOR_ROUTES'].values())
            for turn in (1,2,8,9,23):
                obs={'step':turn,'town':{'unlocked_shops':[]}}
                assert ns['_hire_recovery_schedule'](obs) is ns['_donor_schedule'](obs)
                assert ns['_ITERATED_QUEUE_RAW'](obs)==ns['_donor_schedule'](obs)[turn]
            if name=='shared150':
                original=module(donor['arms'][name]['candidate'],'preflight_original150')
                for key,route in ns['_DONOR_ROUTES'].items():
                    old=original._DONOR_ROUTES[key]
                    for turn in range(2,24):
                        for worker,action in enumerate(old[turn]['hands']):
                            assert route[turn]['hands'][mod._BRIDGE_PERMUTATION[worker]-1]==action
            else:
                original=module(donor['arms'][name]['candidate'],'preflight_original151')
                for key,route in ns['_DONOR_ROUTES'].items():
                    old=original._DONOR_ROUTES[key]
                    for turn in range(2,9):assert route[turn]['hands'][4]==old[turn-1]['hands'][4]
                    assert route[9:]==old[9:]
            checks.append(dict(variant=variant,donor=name,raw_action_queue_and_hire_schedule_share_executable_routes=True))
        arms[variant]=dict(candidate=str(path),candidate_sha256=sha(path))
        del mod
        import gc
        gc.collect()
    market=ROOT/'public_market_smart_f6a756cf_20260927.py'
    assert sha(market)=='f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2'
    common=fixture(114283577)
    classes=[dict(name='idle',kind='idle',fixture=common),dict(name='source',kind='policy',path=str(SOURCE),sha256=SOURCE_SHA,fixture=common)]
    classes += [dict(name=name,kind='policy',path=donor['arms'][name]['candidate'],sha256=donor['arms'][name]['candidate_sha256'],fixture=common) for name in ('shared151','shared150')]
    classes.append(dict(name='market',kind='policy',path=str(market),sha256=sha(market),fixture=common))
    classes += [dict(name=name,kind='tape',fixture=fixture(episode)) for name,episode in [('DECEM',114267880),('Boey',114266440),('Yaroslav',114283577)]]
    paths=[SOURCE,HERE/'PLAN.md',HERE/'layer.py',HERE/'build.py',HERE/'prefix.py',DONOR/'pool.json',DONOR/'INITIAL_OBLIGATIONS.md',DONOR/'initial_obligations.json',
           INPUT/'cached_input.py',INPUT/'initial_states.json',INPUT/'fast_game_cached.py',INPUT/'cached_helper_parity.json',
           ROOT/'diagnostics/physical_route_rollout_20260928/native_core.py',manifest_path,market]
    paths += [Path(donor['arms'][name]['candidate']) for name in ('shared151','shared150')]
    paths += [Path(c['fixture']['source_action_tape_path']) for c in classes if c['kind']=='tape']
    bindings={str(p):sha(p) for p in paths}
    write(HERE/'pool.json',dict(arms=arms,classes=classes,source=str(SOURCE),source_sha256=SOURCE_SHA,
                               donor_arms={name:donor['arms'][name] for name in ('shared151','shared150')},
                               bindings=bindings,created_at_utc=datetime.now(timezone.utc).isoformat()))
    write(HERE/'preflight.json',dict(passed=True,engineering_only=True,full_games=0,checks=checks,
                                    pool_sha256=sha(HERE/'pool.json'),created_at_utc=datetime.now(timezone.utc).isoformat()))
    print(json.dumps(arms,indent=2))


if __name__=='__main__':main()
