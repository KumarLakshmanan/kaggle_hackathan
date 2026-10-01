"""Build isolated variants from frozen v2; preserve every original source."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT/'diagnostics/professional_engine_20261001/candidate_market.py'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert sha(BASE) == '4ea1d89ac99758c6219bcd7d07b729de4dc5836260a25037ca973343b46c6289'
    source = BASE.read_text(encoding='utf-8')
    tree = ast.parse(source)
    assignment = next(n for n in tree.body if isinstance(n, ast.Assign) and
                      any(isinstance(t, ast.Name) and t.id == '_PRO_PAYLOAD' for t in n.targets))
    old_encoded = assignment.value.args[0].args[0].args[0].value
    original = json.loads(zlib.decompress(base64.b85decode(old_encoded)))
    runtime = original['sources']['pro.runtime']
    runtime = runtime.replace("'pro_physical_turns': 0,", "'pro_physical_turns': 0, 'pro_stress_cases': 0,")
    runtime = runtime.replace("self.previous_action = copy.deepcopy(chosen)",
        "self.telemetry['pro_stress_cases'] += report.get('stress_cases', 0)\n        self.previous_action = copy.deepcopy(chosen)")
    (HERE/'runtime.py').write_text(runtime, encoding='utf-8')
    for name, guard in (('wide', False), ('guard', True)):
        output = HERE/f'candidate_{name}_r3.py'
        if output.exists(): raise FileExistsError(output)
        payload = dict(original)
        sources = {}
        for key, text in original['sources'].items():
            if key == 'pro.optimizer':
                sources['pro.projection'] = (HERE/'projection.py').read_text(encoding='utf-8')
                text = (HERE/'optimizer.py').read_text(encoding='utf-8').replace('GUARD = False', 'GUARD = '+repr(guard))
            elif key == 'pro.runtime': text = runtime
            sources[key] = text
        payload['sources'] = sources
        encoded = base64.b85encode(zlib.compress(json.dumps(payload).encode(), 9)).decode()
        assert source.count(repr(old_encoded)) == 1
        generated = source.replace(repr(old_encoded), repr(encoded))
        generated = generated.replace("_PRO_PACKAGE_NAME = '_kgpro_bbffbe65_market'",
                                      "_PRO_PACKAGE_NAME = '_kgpro_v3_"+name+"_bbffbe65'")
        assert "_PRO_PACKAGE_NAME = '_kgpro_v3_"+name in generated
        insertion = (HERE/'fast_parent.py').read_text(encoding='utf-8')+'\n\n'
        generated = generated.replace('_PRO_CONTROLLER = ', insertion+'_PRO_CONTROLLER = ', 1)
        generated = generated.replace('agent.telemetry.update(_PRO_CONTROLLER.telemetry)',
            'agent.telemetry.update(_PRO_CONTROLLER.telemetry)\n    agent.telemetry.update(_FAST_STATS)')
        compile(generated, str(output), 'exec')
        output.write_text(generated, encoding='utf-8')
        manifest = {'candidate_sha256': sha(output), 'baseline_sha256': sha(BASE), 'baseline': str(BASE),
            'source_hashes': {str(p): sha(p) for p in (HERE/'projection.py', HERE/'optimizer.py', HERE/'runtime.py', HERE/'fast_parent.py', Path(__file__))},
            'inherited_sources_sha256': hashlib.sha256(json.dumps(original['sources'], sort_keys=True).encode()).hexdigest(),
            'model_sha256': sha(ROOT/'diagnostics/professional_engine_20261001/value_model.json'),
            'expected_entrypoint': 'kaggle_professional_engine_entrypoint', 'nodes': 36, 'depth': 2,
            'guard': guard, 'physical_controller': False, 'kaggle_upload': False}
        output.with_suffix('.manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print(json.dumps({'variant': name, 'sha256': sha(output)}), flush=True)


if __name__ == '__main__': main()
