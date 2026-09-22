from pathlib import Path
import hashlib
import io
import tarfile
import urllib.request

COMMIT = "7fcf729c06d69f6e14f4d8e50fc89ecb657bdc8f"
EXPECTED = "e363125093463d1f7a63a01aecb70646344dae5b318952e13a1b1641e2043e58"
URL = f"https://raw.githubusercontent.com/woahwhattheheck/commons/{COMMIT}/revenue/kaggriculture/cloud-execution-lab/exports/titan-current.tar.gz"

with urllib.request.urlopen(URL, timeout=60) as response:
    payload = response.read()
if hashlib.sha256(payload).hexdigest() != EXPECTED:
    raise RuntimeError("Release archive does not match the pinned source.")
with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
    names = archive.getnames()
    if "main.py" not in names or "TITAN-CONFIG.json" not in names:
        raise RuntimeError("Required agent entrypoint or configuration is missing.")

output = Path("/kaggle/working/titan-current.tar.gz")
output.write_bytes(payload)
print(f"TITAN ready: {output.name} ({len(payload):,} bytes)")
print("SHA256:", EXPECTED)
