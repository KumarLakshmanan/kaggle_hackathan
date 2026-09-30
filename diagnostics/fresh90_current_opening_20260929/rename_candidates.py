import json, os
from pathlib import Path
folder = Path('diagnostics/fresh90_current_opening_20260929').resolve()
analysis_path = folder / 'family_analysis.json'
data = json.loads(analysis_path.read_text(encoding='utf-8'))
for item in data['selected_candidates']:
    old = Path(item['candidate_path'])
    new = folder / f"candidate_{int(item['candidate_id']):02d}_family{int(item['candidate_id']):02d}_rank{int(item['base_rank'])}.py"
    if old.resolve() != new.resolve() and old.exists():
        previous = old.with_suffix(old.suffix + '.previous')
        if previous.exists():
            raise FileExistsError(previous)
        os.replace(old, previous)
    item['candidate_path'] = str(new)
analysis_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print('updated candidate filenames', [x['candidate_path'] for x in data['selected_candidates']])
