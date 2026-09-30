from pathlib import Path
import base64
import hashlib
import json
import zlib

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    core=ROOT/'diagnostics/physical_route_rollout_20260928/native_core.py'
    flow=core.with_name('observable_flow.py')
    assert sha(ROOT/'main.py')=='4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
    assert sha(core)=='5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795'
    assert sha(flow)=='5b84b59edd362b31696e1941a607fcb60aaf6c8084d5f35e985991c1d9af0c0d'
    assert not (HERE/'candidate.py').exists()
    core_text=core.read_text(encoding='utf-8')
    flow_text=flow.read_text(encoding='utf-8').replace('from . import native_core as core','')
    pack=lambda text:repr(base64.b85encode(zlib.compress(text.encode(),9)).decode())
    embedding='\n\nimport types as _flow_types\n_FLOW_CORE = {}\n'
    embedding+='exec(zlib.decompress(base64.b85decode('+pack(core_text)+')).decode(), _FLOW_CORE)\n'
    embedding+='_FLOW_LOGIC = {"core": _flow_types.SimpleNamespace(**_FLOW_CORE)}\n'
    embedding+='exec(zlib.decompress(base64.b85decode('+pack(flow_text)+')).decode(), _FLOW_LOGIC)\n'
    blob=(ROOT/'main.py').read_bytes()+embedding.encode()+(HERE/'layer.py').read_bytes()
    target=HERE/'candidate.py';compile(blob,str(target),'exec');target.write_bytes(blob)
    manifest=dict(candidate=str(target),candidate_sha256=sha(target),source_sha256=sha(ROOT/'main.py'),
        plan_sha256=sha(HERE/'PLAN.md'),layer_sha256=sha(HERE/'layer.py'),core_sha256=sha(core),flow_sha256=sha(flow))
    (HERE/'candidate.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
