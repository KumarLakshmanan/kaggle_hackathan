"""Decode only the literal C95 source from the downloaded public notebook."""

import ast
import base64
import hashlib
import json
from pathlib import Path
import zlib

HERE = Path(__file__).resolve().parent
NOTEBOOK = HERE / "kaggriculture-findings-from-zero-to-top-meta.ipynb"
OUTPUT = HERE / "public_c95_main.py"


def main() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    source = "".join(notebook["cells"][54]["source"])
    literals = {}
    for statement in ast.parse(source).body:
        if not isinstance(statement, ast.Assign) or len(statement.targets) != 1:
            continue
        target = statement.targets[0]
        if isinstance(target, ast.Name) and target.id in {
            "_C95_AGENT_B64_PARTS", "EXPECTED_C95_SHA256", "EXPECTED_C95_BYTES"
        }:
            literals[target.id] = ast.literal_eval(statement.value)
    raw = zlib.decompress(base64.b64decode("".join(literals["_C95_AGENT_B64_PARTS"])))
    assert len(raw) == literals["EXPECTED_C95_BYTES"]
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == literals["EXPECTED_C95_SHA256"]
    compile(raw, str(OUTPUT), "exec")
    OUTPUT.write_bytes(raw)
    print(OUTPUT, len(raw), digest)


if __name__ == "__main__":
    main()
