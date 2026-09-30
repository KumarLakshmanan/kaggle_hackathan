from pathlib import Path
p=Path('diagnostics/fresh90_current_opening_20260929/README.md')
s=p.read_text(encoding='utf-8').replace('fc5fe0ea48c6400a7c444a501f388a76e9588343baf7027cef522b7e7e381621','04bc8d1df1bae5f13cec33417b3e3e4f7ee71174b9a9f530c6ed06599f375571')
p.write_text(s,encoding='utf-8')
p=Path('diagnostics/fresh90_current_opening_20260929/write_hashes.py')
s=p.read_text(encoding='utf-8').replace("    base / 'candidate_manifest.json',", "    base / 'candidate_manifest.json',\n    base / 'README.md',")
p.write_text(s,encoding='utf-8')
