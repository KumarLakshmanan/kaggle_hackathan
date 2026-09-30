from pathlib import Path
import base64
import hashlib
import json
import zlib

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    source=ROOT/'diagnostics/compatible_route_pool_20260928/candidates/B_113349962.py'
    core=ROOT/'diagnostics/physical_route_rollout_20260928/native_core.py'
    assert sha(source)=='d271754e609f1f089ea80d60186c24b4d14e357720ace34a47aa584c081504ed'
    assert sha(core)=='5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795'
    assert sha(ROOT/'main.py')=='4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'
    assert not (HERE/'candidate.py').exists()
    packed=repr(base64.b85encode(zlib.compress(core.read_bytes(),9)).decode())
    embedding='\n_ANIMAL_CORE = {}\nexec(zlib.decompress(base64.b85decode('+packed+')).decode(), _ANIMAL_CORE)\n'
    blob=source.read_bytes()+embedding.encode()+(HERE/'layer.py').read_bytes()
    target=HERE/'candidate.py';compile(blob,str(target),'exec');target.write_bytes(blob)
    manifest=dict(candidate=str(target),candidate_sha256=sha(target),source_sha256=sha(source),
                  plan_sha256=sha(HERE/'PLAN.md'),layer_sha256=sha(HERE/'layer.py'),core_sha256=sha(core))
    (HERE/'candidate.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
