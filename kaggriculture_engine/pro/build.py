"""Freeze a standalone candidate with source/model identities; never uploads."""
import base64
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[2]
MODULES = ('native_core', 'engine', 'pro.simulation', 'pro.scheduler', 'pro.beliefs',
           'pro.scenarios', 'pro.value', 'pro.planner', 'pro.optimizer', 'pro.runtime')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(output, baseline, model_path, physical=False):
    output, baseline = Path(output).resolve(), Path(baseline).resolve()
    if output.exists(): raise FileExistsError(output)
    source = baseline.read_text(encoding='utf-8')
    if '_PRO_CONTROLLER =' in source: raise ValueError('Already wrapped by professional engine.')
    sources = {name: (ROOT/'kaggriculture_engine'/Path(*name.split('.'))).with_suffix('.py').read_text(encoding='utf-8') for name in MODULES}
    model = json.loads(Path(model_path).read_text())
    runtime_model = {k: v for k, v in model.items() if k not in ('sources', 'train_episodes', 'holdout_episodes')}
    payload = base64.b85encode(zlib.compress(json.dumps({'sources': sources, 'model': runtime_model}).encode(), 9)).decode()
    suffix = '''
# Scenario-aware executable professional engine v2.
import base64 as _pro_base64
import zlib as _pro_zlib
import json as _pro_json
import sys as _pro_sys
import types as _pro_types
_PRO_PARENT = agent
_PRO_PAYLOAD = _pro_json.loads(_pro_zlib.decompress(_pro_base64.b85decode(PAYLOAD)))
_PRO_PACKAGE_NAME = PACKAGE_NAME
_pro_package = _pro_types.ModuleType(_PRO_PACKAGE_NAME)
_pro_package.__path__ = []
_pro_sys.modules[_PRO_PACKAGE_NAME] = _pro_package
_pro_subpackage = _pro_types.ModuleType(_PRO_PACKAGE_NAME+'.pro')
_pro_subpackage.__path__ = []
_pro_sys.modules[_PRO_PACKAGE_NAME+'.pro'] = _pro_subpackage
for _pro_name, _pro_source in _PRO_PAYLOAD['sources'].items():
    _pro_module = _pro_types.ModuleType(_PRO_PACKAGE_NAME+'.'+_pro_name)
    _pro_module.__package__ = _pro_module.__name__.rsplit('.',1)[0]
    _pro_sys.modules[_pro_module.__name__] = _pro_module
    exec(compile(_pro_source, '<embedded '+_pro_name+'>', 'exec'), _pro_module.__dict__)
_PRO_CONTROLLER = _pro_sys.modules[_PRO_PACKAGE_NAME+'.pro.runtime'].Controller(
    _PRO_PARENT, _DATA, _PRO_PAYLOAD['model'], physical=PHYSICAL)


def agent(observation, configuration=None):
    result = _PRO_CONTROLLER(observation, configuration)
    agent.telemetry.update(_PRO_CONTROLLER.telemetry)
    return result


agent.telemetry = {}


def kaggle_professional_engine_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''.replace('PAYLOAD)))', repr(payload)+')))').replace('PACKAGE_NAME\n', repr('_kgpro_'+sha(baseline)[:8]+('_full' if physical else '_market'))+'\n').replace('physical=PHYSICAL', 'physical='+repr(physical))
    # Replacement tokens must leave _PRO_PAYLOAD and _PRO_PACKAGE_NAME names intact.
    compile(source+suffix, str(output), 'exec')
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(source+suffix, encoding='utf-8')
    manifest = {'candidate_sha256': sha(output), 'baseline_sha256': sha(baseline), 'baseline': str(baseline),
        'model_sha256': sha(model_path), 'physical_controller': physical, 'expected_entrypoint': 'kaggle_professional_engine_entrypoint',
        'source_hashes': {str((ROOT/'kaggriculture_engine'/Path(*n.split('.'))).with_suffix('.py')): sha((ROOT/'kaggriculture_engine'/Path(*n.split('.'))).with_suffix('.py')) for n in MODULES},
        'builder_sha256': sha(__file__), 'market_nodes': 12, 'macro_transition_budget': 4096,
        'forecast_scope': 'Twelve-day native scenarios; immutable itinerary baseline, heuristic rivals and fitted tail. No guaranteed wins.'}
    output.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest
