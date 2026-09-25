import shutil
import tarfile
from pathlib import Path

WORK = Path('/kaggle/working')
INPUT = Path('/kaggle/input')

# --- Resilient file discovery (Kaggle mounts datasets inconsistently) ---
def find_file(name, search_root=INPUT):
    """Find a file by name under search_root, with rglob fallback."""
    # Try the expected direct path first
    direct = search_root / 'kaggriculture-high-performance-agent' / name
    if direct.exists():
        return direct
    # rglob fallback
    matches = list(search_root.rglob(name))
    if matches:
        return matches[0]
    return None

# Try submission.tar.gz first (pre-built, fastest)
src_tar = find_file('submission.tar.gz')
dst = WORK / 'submission.tar.gz'

if src_tar:
    shutil.copy2(src_tar, dst)
    print(f'Loaded agent: {dst} ({dst.stat().st_size / 1024:.1f} KB)')
else:
    # Fallback: build tar from main.py
    main_src = find_file('main.py')
    if main_src:
        main_dst = WORK / 'main.py'
        shutil.copy2(main_src, main_dst)
        with tarfile.open(dst, 'w:gz') as tar:
            tar.add(main_dst, arcname='main.py')
        main_dst.unlink()
        print(f'Built from main.py: {dst} ({dst.stat().st_size / 1024:.1f} KB)')
    else:
        # Fail-fast with directory listing for debugging
        print('ERROR: Agent not found. Contents of /kaggle/input:')
        for p in sorted(INPUT.rglob('*'))[:50]:
            print(f'  {p}')
        raise FileNotFoundError(
            'Neither submission.tar.gz nor main.py found under /kaggle/input. '
            'Make sure the dataset "kaggriculture-high-performance-agent" is attached.'
        )

# Validate: make sure main.py is in the archive
with tarfile.open(dst, 'r:gz') as tar:
    members = tar.getnames()
    print(f'Archive contents: {members}')
    assert 'main.py' in members, 'main.py not found in archive!'

print(f'Size: {dst.stat().st_size / 1024:.1f} KB')
print('\nReady to submit. Go to Output tab -> Submit to Competition.')