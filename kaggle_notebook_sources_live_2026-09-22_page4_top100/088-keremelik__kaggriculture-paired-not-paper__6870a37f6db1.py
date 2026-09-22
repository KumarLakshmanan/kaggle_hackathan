import json, math, os, subprocess, sys
from pathlib import Path

def ensure_env(min_ver=(1, 32, 7)):
    try:
        from importlib.metadata import version
        inst = version("kaggle-environments")
    except Exception:
        inst = "0"
    parts = []
    for p in inst.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    while len(parts) < 3:
        parts.append(0)
    if tuple(parts[:3]) < min_ver:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-U", "kaggle-environments>=1.32.7"])
    import kaggle_environments
    print("kaggle-environments", kaggle_environments.__version__)
    return kaggle_environments

ke = ensure_env()
from kaggle_environments import make
WORK = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path.cwd()
WORK.mkdir(exist_ok=True)
print("work", WORK)


def wilson_lo(w, n, z=1.96):
    if n <= 0:
        return 0.0
    p = w / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - margin) / den

def invert(p, Ra):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return Ra - 400 * math.log10((1 - p) / p)

rows = [
    ("Thomas@3143 16-4", 16, 20, 3143),
    ("Thomas@3143 14-6", 14, 20, 3143),
    ("peikopon@2985 17-3", 17, 20, 2985),
    ("kaito dump@1316 20-0", 20, 20, 1316),
]
print(f"{'anchor':22} {'WR':6} {'R_hat':8} {'R_lo':8}")
out = []
for name, w, n, ra in rows:
    p = w / n
    plo = wilson_lo(w, n)
    rec = {"name": name, "W": w, "n": n, "R_hat": round(invert(p, ra), 1), "R_lo": round(invert(plo, ra), 1)}
    out.append(rec)
    print(f"{name:22} {p:5.2f} {rec['R_hat']:8.1f} {rec['R_lo']:8.1f}")

rlo = [r["R_lo"] for r in out]
card = {
    "R_lo_win_tapes": rlo[:3],
    "R_lo_min_with_dump": min(rlo),
    "spread_with_dump": round(max(rlo) - min(rlo), 1),
    "term717": (max(rlo) - min(rlo)) > 400,
    "submit": False,
}
(WORK / "evidence_paired_not_paper.json").write_text(json.dumps({"rows": out, "card": card}, indent=2))
print(json.dumps(card, indent=2))

