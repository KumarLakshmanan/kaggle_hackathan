"""Build the one-site variant of the public-state-gated early goose experiment."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TAIL = Path(__file__).with_name("early_goose_gated_tail.py")
DEST = ROOT / "exp_early_goose_gated_one_site_20260926.py"

source = TAIL.read_text(encoding="utf8")
before = "_EG_TARGETS = frozenset(((5, 2), (6, 4)))"
after = "_EG_TARGETS = frozenset(((6, 4),))"
assert source.count(before) == 1
DEST.write_text(ROOT.joinpath("main.py").read_text(encoding="utf8")
                + "\n\n" + source.replace(before, after), encoding="utf8")
print(DEST)
