"""Preserve and inspect donor sources without executing the attachment."""
import ast
import hashlib
import json
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SOURCE=Path('C:/Users/Veeramani Selvaraj/Downloads/main(8).py')


def main():
    raw=SOURCE.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    assert digest=='b9ef905e6360006e9e2637bd785b1d6f67adf3f01777a383529ef396d5ebb9b5'
    target=HERE/'donor_main_b9ef905e.py'
    if target.exists():assert target.read_bytes()==raw
    else:target.write_bytes(raw)
    package=HERE/'donor';package.mkdir(exist_ok=True)
    (package/'__init__.py').write_text('',encoding='utf-8')
    sources={};imports={}
    for node in ast.parse(raw.decode()).body:
        if not isinstance(node,ast.Assign):continue
        names=[t.id for t in node.targets if isinstance(t,ast.Name)]
        if len(names)!=1 or not names[0].startswith('_SOURCE_'):continue
        text=ast.literal_eval(node.value);name=names[0][8:].lower()
        (package/f'{name}.py').write_text(text,encoding='utf-8')
        tree=ast.parse(text)
        imports[name]=[ast.unparse(n) for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
        sources[name]=hashlib.sha256(text.encode()).hexdigest()
    core=(ROOT/'kaggriculture_engine/native_core.py').read_text(encoding='utf-8')
    same_core=ast.dump(ast.parse(core),include_attributes=False)==ast.dump(ast.parse((package/'native_core.py').read_text()),include_attributes=False)
    assert same_core,'Native transition rules differ; diagnose before integration.'
    receipt={'donor_sha256':digest,'source':str(SOURCE),'source_hashes':sources,'imports':imports,'native_ast_matches':same_core}
    (HERE/'extraction_receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    shutil.copyfile(ROOT/'diagnostics/professional_engine_20261001/candidate_market.py',HERE/'baseline_4ea1d89a.py')
    shutil.copyfile(ROOT/'diagnostics/professional_engine_20261001/baseline_main_bbffbe65.py',HERE/'baseline_bbffbe65.py')
    print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':main()
