"""Build the transparent V30 two-opening counter portfolio."""

from __future__ import annotations

import gzip
import hashlib
import json
import pprint
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _route(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)["actions"]


def _replace_table(text: str, name: str, next_name: str, actions: list[dict]) -> str:
    start = text.index(f"{name} =")
    end = text.index(f"\n{next_name} =", start)
    rendered = f"{name} = {pprint.pformat(actions, width=120, compact=True, sort_dicts=False)}"
    return text[:start] + rendered + text[end:]


def _digest(actions: list[dict]) -> str:
    payload = json.dumps(actions, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def build(destination: Path) -> None:
    primary_path = ROOT / "best_replay/routes/episode-90622597-seat1.json.gz"
    alternate_path = ROOT / "best_replay/routes/episode-90630506-seat0.json.gz"
    primary = _route(primary_path)
    alternate = _route(alternate_path)

    text = (ROOT / "main_v28_wufang_seb_detect.py").read_text(encoding="utf-8")
    text = _replace_table(text, "_PRIMARY_ACTIONS", "_ALTERNATE_ACTIONS", primary)
    text = _replace_table(text, "_ALTERNATE_ACTIONS", "_ACTIONS", alternate)
    text = text.replace(
        "_ROUTE_ACTION_SHA256 = '4a0c36676bc16852de643df803a7fd4406bee6333022634ddd6ff8d50df54e01'",
        f"_ROUTE_ACTION_SHA256 = '{_digest(primary)}'",
    )
    text = text.replace(
        "_ALTERNATE_ACTION_SHA256 = '9d59c1edb498ef988f00187c3a322d26a47490a071413dfeb92d49101ed512f1'",
        f"_ALTERNATE_ACTION_SHA256 = '{_digest(alternate)}'",
    )
    text = text.replace(
        "V17 transparent route, recovery, and all-product market search",
        "V30 transparent two-opening counter portfolio",
    )
    destination.write_text(text, encoding="utf-8", newline="\n")
    print(destination.resolve())
    print(f"bytes={destination.stat().st_size}")


if __name__ == "__main__":
    build(ROOT / "main_v30_counter_portfolio.py")
