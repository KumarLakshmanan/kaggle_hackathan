from pathlib import Path
import base64
import hashlib
import json
import zlib

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    sources={
        'main':(ROOT/'main.py','4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed'),
        'route':(ROOT/'diagnostics/compatible_route_pool_20260928/candidates/B_113349962.py',
                 'd271754e609f1f089ea80d60186c24b4d14e357720ace34a47aa584c081504ed'),
    }
    core=ROOT/'diagnostics/physical_route_rollout_20260928/native_core.py'
    manifest=ROOT/'diagnostics/loss_class_20260927/local_target_manifest_180951.json'
    assert sha(manifest)=='524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20'
    data=json.loads(manifest.read_text(encoding='utf-8'))
    fixtures=[f for f in data['live_losses'] if f['fixture_id']=='live-114283577']
    assert len(fixtures)==1 and fixtures[0]['team']=='Yaroslav'
    fixtures.extend(f for f in data['current_top20'] if f['team'] in ('DECEM','Boey','Majkel1337') or f['team'].startswith('Kaggledew'))
    assert len(fixtures)==5
    assert sha(core)=='5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795'
    packed=repr(base64.b85encode(zlib.compress(core.read_bytes(),9)).decode())
    embedding='\n_PLANT_CORE = {}\nexec(zlib.decompress(base64.b85decode('+packed+')).decode(), _PLANT_CORE)\n'
    variants=[]
    for version,(source,digest) in sources.items():
        assert sha(source)==digest
        target=HERE/f'candidate_{version}.py';assert not target.exists()
        blob=source.read_bytes()+embedding.encode()+(HERE/'layer.py').read_bytes()
        compile(blob,str(target),'exec');target.write_bytes(blob)
        variants.append(dict(version=version,candidate=str(target),candidate_sha256=sha(target),source_sha256=digest))
    info=dict(variants=variants,fixtures=fixtures,manifest_sha256=sha(manifest),
              plan_sha256=sha(HERE/'PLAN.md'),layer_sha256=sha(HERE/'layer.py'),core_sha256=sha(core))
    (HERE/'pool.json').write_text(json.dumps(info,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in info.items() if k!='fixtures'},indent=2))


if __name__=='__main__':main()
