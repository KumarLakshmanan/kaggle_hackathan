"""Package exact baseline executor, native simulator and generated-action search."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zlib

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def packed(text): return repr(base64.b85encode(zlib.compress(text.encode('utf-8'), 9)).decode('ascii'))

def build(output, baseline, nodes=48, depth=3, width=3):
    if output.exists(): raise FileExistsError(output)
    source = baseline.read_text(encoding='utf-8')
    if '_SEARCH_PARENT = agent' in source:
        raise ValueError('Baseline already contains this engine. Use the preserved unwrapped physical executor to avoid recursive wrapping.')
    core = (HERE / 'native_core.py').read_text(encoding='utf-8')
    engine = (HERE / 'engine.py').read_text(encoding='utf-8').replace('from . import native_core as core', '')
    suffix = '\n\n# Bounded generated-action search over exact native transitions.\n'
    suffix += 'import types as _search_types\n'
    suffix += '_SEARCH_CORE = _search_types.ModuleType("kaggriculture_search_native")\n'
    suffix += f'exec(zlib.decompress(base64.b85decode({packed(core)})).decode("utf-8"), _SEARCH_CORE.__dict__)\n'
    suffix += '_SEARCH_ENGINE = {"__name__": "kaggriculture_embedded_search", "core": _SEARCH_CORE}\n'
    suffix += f'exec(zlib.decompress(base64.b85decode({packed(engine)})).decode("utf-8"), _SEARCH_ENGINE)\n'
    suffix += f'_SEARCH_SETTINGS = _SEARCH_ENGINE["SearchConfig"](max_nodes={nodes}, depth={depth}, width={width}, seconds=0.)\n'
    suffix += '''_SEARCH_PARENT = agent
_SEARCH_STATS = {'engine_calls': 0, 'engine_nodes': 0, 'engine_changed_turns': 0,
                 'engine_predicted_scenario_gain': 0., 'engine_errors': 0,
                 'engine_max_seconds': 0., 'engine_budget_stops': 0}
_SEARCH_LAST_REPORT = {}


def agent(observation, configuration=None):
    global _SEARCH_LAST_REPORT
    if int(observation['step']) == 0:
        for key in _SEARCH_STATS: _SEARCH_STATS[key] = 0
    result = _SEARCH_PARENT(observation, configuration)
    try:
        chosen, report = _SEARCH_ENGINE['optimize_market'](observation, result, configuration or {}, _SEARCH_SETTINGS)
        _SEARCH_LAST_REPORT = report
        _SEARCH_STATS['engine_calls'] += 1
        _SEARCH_STATS['engine_nodes'] += report['nodes']
        _SEARCH_STATS['engine_changed_turns'] += int(report['accepted'])
        _SEARCH_STATS['engine_predicted_scenario_gain'] += report['gain']
        _SEARCH_STATS['engine_max_seconds'] = max(_SEARCH_STATS['engine_max_seconds'], report.get('elapsed_seconds', 0.))
        _SEARCH_STATS['engine_budget_stops'] += int(report['budget_exhausted'])
        result = chosen
    except Exception:
        _SEARCH_STATS['engine_errors'] += 1
    agent.telemetry.update(_SEARCH_STATS)
    return result


agent.telemetry = {}


def kaggle_executable_search_entrypoint(observation, configuration=None):
    return agent(observation, configuration)
'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(source+suffix, encoding='utf-8')
    manifest = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), candidate=str(output.resolve()),
                    candidate_sha256=sha(output), baseline=str(baseline.resolve()), baseline_sha256=sha(baseline),
                    engine_sha256=sha(HERE/'engine.py'), simulator_sha256=sha(HERE/'native_core.py'),
                    builder_sha256=sha(__file__), nodes=nodes, depth=depth, width=width,
                    expected_entrypoint='kaggle_executable_search_entrypoint', research_promotion=False,
                    scope='Generated market programs on existing complete production schedule; no guaranteed strength gain.')
    output.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return manifest


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, default=ROOT/'main.py')
    parser.add_argument('--nodes', type=int, default=48);parser.add_argument('--depth', type=int, default=3)
    args=parser.parse_args()
    if not 1<=args.nodes<=256 or not 1<=args.depth<=8: parser.error('Invalid search budget')
    print(json.dumps(build(args.output.resolve(), args.baseline.resolve(), args.nodes, args.depth), indent=2))

if __name__=='__main__': main()
