"""Freeze individual additions without modifying current artifacts or donor."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(name,modes):
    baseline=HERE/'baseline_4ea1d89a.py';donor=HERE/'donor_main_b9ef905e.py';output=HERE/f'candidate_{name}.py'
    assert sha(baseline)=='4ea1d89ac99758c6219bcd7d07b729de4dc5836260a25037ca973343b46c6289'
    assert sha(donor)=='b9ef905e6360006e9e2637bd785b1d6f67adf3f01777a383529ef396d5ebb9b5'
    if output.exists():raise FileExistsError(output)
    source=baseline.read_text(encoding='utf-8')
    donor_source=donor.read_text(encoding='utf-8').replace("'_kaggriculture_general_v3'",repr('_kaggriculture_borrow_'+name))
    suffix='\n\n# Isolated borrowed logic experiment.\n_BORROW_PARENT=agent\n'
    suffix+='_BORROW_NAMESPACE={"__name__":'+repr('_borrow_host_'+name)+'}\n'
    suffix+='exec(compile('+repr(donor_source)+', "<borrowed donor>", "exec"), _BORROW_NAMESPACE)\n'
    suffix+='_BORROW_PACKAGE=_BORROW_NAMESPACE["_PACKAGE"]\n'
    suffix+=(HERE/'adapters.py').read_text(encoding='utf-8').replace('BORROW_MODES',repr(tuple(modes)))
    text=source+suffix;compile(text,str(output),'exec');output.write_text(text,encoding='utf-8')
    manifest={'candidate_sha256':sha(output),'baseline_sha256':sha(baseline),'donor_sha256':sha(donor),
        'modes':list(modes),'expected_entrypoint':'kaggle_borrowed_logic_entrypoint',
        'source_hashes':{str(p):sha(p) for p in (HERE/'adapters.py',Path(__file__),donor,baseline)},
        'scope':'Experimental individual donor transplant; no measured strength yet; no Kaggle upload.'}
    output.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest


def main():
    p=argparse.ArgumentParser();p.add_argument('--name');p.add_argument('--modes',nargs='+');args=p.parse_args()
    if args.name:
        assert args.modes;print(json.dumps(build(args.name,args.modes),indent=2))
    else:
        for mode in ('belief','feed','accounting','dynamic','endgame','combined'):
            manifest=build(mode,[mode]);print(json.dumps({'mode':mode,'sha256':manifest['candidate_sha256']}),flush=True)


if __name__=='__main__':main()
