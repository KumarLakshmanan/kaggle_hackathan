"""Build three independent donor agents; verify reused helper dependencies."""
from pathlib import Path
import ast
import base64
import hashlib
import json
import gzip
import symtable
import zlib

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'main_candidate_hire_recovery_integrated_20260928_367d2e76.py'
SOURCE_SHA='367d2e7683472af526bdaee5af80c9e7fe59dfb2136475555a2970ef8beccaa0'
MANIFEST=ROOT/'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
MANIFEST_SHA='524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
FULL=ROOT/'diagnostics/observed_hire_recovery_20260928/native_full.json'
FULL_SHA='1cd02ac25079a1df229ad528c51a94ec467181a4adcd1e6ab13248ff4fd82545'
AUDIT=ROOT/'diagnostics/frozen_reply_donor_audit_20260928/cross_donor_openings.json'
AUDIT_SHA='ffad1dedd4baaf03c99a08842ddaa2a43fbc34f71aa41390c29e7814e1cf6c19'
GROUPS={
 'shared151':[(114232208,'BAKERY|BAKERY'),(114235177,'BAKERY|PIZZA_SHOP'),(114279308,'FARMERS_MARKET|ICE_CREAM_SHOP')],
 'shared150':[(114215872,'BAKERY|BAKERY'),(114289228,'BRUNCH_SPOT|BRUNCH_SPOT')],
 'shared166':[(114260122,'PET_CAFE|FARMERS_MARKET'),(114288168,'ICE_CREAM_SHOP|PET_CAFE')],
}
PILOT=[114232208,114235177,114279308,114215872,114289228,114260122,114288168,114266440,114265033,114263239]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,obj):Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))


BASE='''
_DONOR_SELECTED = _DONOR_DEFAULT
_DONOR_STATS = {'donor_selected': _DONOR_DEFAULT, 'donor_pair144': '', 'donor_default_branch': True}

def _donor_schedule(obs):
    global _DONOR_SELECTED
    step = int(obs['step'])
    if step == 0:
        _DONOR_SELECTED = _DONOR_DEFAULT
        _DONOR_STATS.update(donor_selected=_DONOR_DEFAULT, donor_pair144='', donor_default_branch=True)
    if step == 144:
        pair = '|'.join(obs['town'].get('unlocked_shops', [])[:2])
        _DONOR_SELECTED = _DONOR_MAP.get(pair, _DONOR_DEFAULT)
        _DONOR_STATS.update(donor_selected=_DONOR_SELECTED, donor_pair144=pair, donor_default_branch=pair not in _DONOR_MAP)
    return _DONOR_ROUTES[_DONOR_SELECTED]

def _donor_action(obs, configuration=None):
    return copy.deepcopy(_donor_schedule(obs)[max(0, min(718, int(obs['step'])))])

def _hire_recovery_schedule(obs):
    return _donor_schedule(obs)

_QUEUE_PARENT = _donor_action
_ITERATED_QUEUE_RAW = _donor_action
_HIRE_RECOVERY_PLAN = None
_HIRE_RECOVERY_QUEUES = {}
'''

ENTRY='''
def agent(observation, configuration=None):
    global _HIRE_RECOVERY_PLAN, _HIRE_RECOVERY_QUEUES
    if int(observation['step']) == 0:
        _HIRE_RECOVERY_PLAN = None
        _HIRE_RECOVERY_QUEUES = {}
        for stats in (_QUEUE_STATS, _PURCHASE_QUEUE_STATS, _ITERATED_QUEUE_STATS, _PARTIAL_STATS, _HIRE_RECOVERY_STATS):
            for key in stats:
                stats[key] = 0
        agent.telemetry.clear()
    action = _donor_action(observation, configuration)
    for transform, stats, error in (
        (_queue_optimize, _QUEUE_STATS, 'queue_errors'),
        (_purchase_queue_apply, _PURCHASE_QUEUE_STATS, 'purchase_queue_errors'),
        (_iterated_queue_apply, _ITERATED_QUEUE_STATS, 'iterated_queue_errors'),
        (_partial_plant, _PARTIAL_STATS, 'partial_plant_errors'),
        (_hire_recovery_apply, _HIRE_RECOVERY_STATS, 'hire_recovery_errors'),
    ):
        try:
            action = transform(observation, action, configuration or {})
        except Exception:
            stats[error] += 1
    for stats in (_QUEUE_STATS, _PURCHASE_QUEUE_STATS, _ITERATED_QUEUE_STATS, _PARTIAL_STATS, _HIRE_RECOVERY_STATS, _DONOR_STATS):
        agent.telemetry.update(stats)
    return action

agent.telemetry = {}

def kaggle_donor_opening_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''


def main():
    assert sha(SOURCE)==SOURCE_SHA and sha(MANIFEST)==MANIFEST_SHA and sha(FULL)==FULL_SHA and sha(AUDIT)==AUDIT_SHA
    assert not (HERE/'pool.json').exists()
    source=SOURCE.read_text(encoding='utf-8');tree=ast.parse(source)
    pieces=[]; helper_hashes={}
    for namespace in ('_QUEUE_ENGINE','_PLANT_CORE'):
        pieces.append(namespace+' = {}')
        node=next(n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name)
                  and n.value.func.id=='exec' and len(n.value.args)>1 and isinstance(n.value.args[1],ast.Name) and n.value.args[1].id==namespace)
        text=ast.get_source_segment(source,node);pieces.append(text);helper_hashes[namespace+'_initializer']=hashlib.sha256(text.encode()).hexdigest()
    pieces.append("_QUEUE_ANIMALS = _QUEUE_ENGINE['ANIMALS']")
    names=['_QueueBox','_queue_stock','_queue_signature','_queue_simulate','_queue_optimize','_purchase_queue_apply','_iterated_queue_apply','_partial_plant','_hire_recovery_apply']
    for name in names:
        node=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
        text=ast.get_source_segment(source,node);pieces.append(text);helper_hashes[name]=hashlib.sha256(text.encode()).hexdigest()
    for name in ('_QUEUE_STATS','_PURCHASE_QUEUE_STATS','_ITERATED_QUEUE_STATS','_PARTIAL_STATS','_HIRE_RECOVERY_STATS'):
        node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
        text=ast.get_source_segment(source,node);pieces.append(text);helper_hashes[name]=hashlib.sha256(text.encode()).hexdigest()
    helpers='\n\n'.join(pieces)+'\n'
    symbols=symtable.symtable(helpers,'extracted_helpers.py','exec')
    refs={block.get_name():sorted(s.get_name() for s in block.get_symbols() if s.is_global() and s.is_referenced()) for block in symbols.get_children()}
    forbidden={'_DATA','_FARMICE_TAPE','_FARMICE_ACTIVE','_AC_ROUTE_PARENT','_LOSS_POOL_PARENT','_POOL_PARENT','agent','_HIRE_RECOVERY_PARENT'}
    assert not any(forbidden.intersection(values) for values in refs.values())
    assert '_hire_recovery_schedule' in refs['_hire_recovery_apply'] and '_ITERATED_QUEUE_RAW' in refs['_iterated_queue_apply']
    (HERE/'extracted_helpers.py').write_text(helpers,encoding='utf-8')
    compile(helpers,str(HERE/'extracted_helpers.py'),'exec')
    manifest=read(MANIFEST);fixtures=manifest['live_losses']+manifest['current_top20']
    arms={};donors={}
    for version, group in GROUPS.items():
        routes={};mapping={};bound=[]
        for i,(episode,pair) in enumerate(group):
            fixture=next(f for f in manifest['live_losses'] if f['episode_id']==episode)
            actions=json.loads(gzip.decompress(Path(fixture['source_action_tape_path']).read_bytes()))['actions']
            hashes=[hashlib.sha256(json.dumps(actions,sort_keys=s,separators=(',',':')).encode()).hexdigest() for s in (False,True)]
            assert fixture['source_opponent_action_sha256'] in hashes and len(actions)==719
            key='route'+str(i);routes[key]=actions;mapping[pair]=key
            bound.append(dict(episode_id=episode,route_key=key,observable_pair=pair,fixture_id=fixture['fixture_id'],
                              action_sha256=fixture['source_opponent_action_sha256'],tape_path=fixture['source_action_tape_path'],tape_sha256=sha(fixture['source_action_tape_path'])))
        first=next(iter(routes.values()));assert all(actions[:144]==first[:144] for actions in routes.values())
        payload=base64.b85encode(zlib.compress(json.dumps(routes,separators=(',',':')).encode())).decode()
        code='import copy\nimport json\nimport zlib\nimport base64\n\n'
        code+='_DONOR_ROUTES = json.loads(zlib.decompress(base64.b85decode('+repr(payload)+')))\n'
        code+='_DONOR_DEFAULT = "route0"\n_DONOR_MAP = '+repr(mapping)+'\n'+BASE+'\n'+helpers+'\n'+ENTRY
        path=HERE/('candidate_'+version+'.py');assert not path.exists();path.write_text(code,encoding='utf-8');compile(code,str(path),'exec')
        runtime_tree=ast.parse(code); defs=[n.name for n in runtime_tree.body if isinstance(n,ast.FunctionDef)]
        assert defs[-1]=='kaggle_donor_opening_entrypoint'
        assert not any(isinstance(n,ast.Name) and n.id in forbidden-{'agent'} for n in ast.walk(runtime_tree))
        arms[version]=dict(candidate=str(path),candidate_sha256=sha(path),default='route0',default_episode=group[0][0],mapping=mapping,donors=bound)
        donors[version]=bound
    selected=[next(f for f in fixtures if f['episode_id']==episode) for episode in PILOT]
    pool=dict(source=str(SOURCE),source_sha256=SOURCE_SHA,manifest_sha256=MANIFEST_SHA,native_source_full_sha256=FULL_SHA,
              donor_audit_sha256=AUDIT_SHA,plan_sha256=sha(HERE/'PLAN.md'),build_helper_sha256=sha(__file__),
              extracted_helpers_sha256=sha(HERE/'extracted_helpers.py'),source_helper_hashes=helper_hashes,
              helper_global_references=refs,arms=arms,fixtures=selected,pilot_fixture_count=10,pilot_games=60)
    write(HERE/'pool.json',pool)
    print(json.dumps({version:arm['candidate_sha256'] for version,arm in arms.items()},indent=2))


if __name__=='__main__':
    HERE.mkdir(parents=True,exist_ok=True)
    main()
