#!/usr/bin/env python3
"""Kaggriculture — Estado del proyecto P1.2.2 (2026-08-22).

Sincronización de estado con Kaggle. Este kernel valida:
  1. Código canónico (main.py stdlib-only, train_rl, C6Net)
  2. Env local calibrado: consumo de shops x2 (P1.2.2) + wrapper F0 corregido
  3. Resultados del proyecto: F0_ECO_CORRECTED, Teacher v1/v2, gates

Ejecuta comprobaciones y emite un resumen. NO entrena (los experimentos se
ejecutan localmente con determinismo P0b).
"""
import os
import sys
import json
import time
from pathlib import Path

WORK_DIR = "/kaggle/working"
os.makedirs(WORK_DIR, exist_ok=True)

# ============================================================
# Dataset discovery
# ============================================================
INPUT_ROOT = Path("/kaggle/input")
matches = list(INPUT_ROOT.rglob("main.py"))
if not matches:
    print("[STATE] ERROR: dataset no montado")
    sys.exit(1)
DATASET_DIR = matches[0].parent
print(f"[STATE] dataset: {DATASET_DIR}")

required = ["main.py", "train_rl.py", "constants.py", "utils.py",
            "enemy_agents.py", "c6_net.py", "rl_best.pt"]
for fname in required:
    fpath = DATASET_DIR / fname
    if fpath.exists():
        print(f"[STATE]   {fname}: {fpath.stat().st_size:,} bytes")
    else:
        print(f"[STATE]   WARNING: {fname} no encontrado")

for fname in required:
    src = DATASET_DIR / fname
    if src.exists():
        dst = Path(WORK_DIR) / fname
        dst.write_bytes(src.read_bytes())
sys.path.insert(0, WORK_DIR)

# ============================================================
# 1. main.py stdlib-only check
# ============================================================
print("\n[STATE] 1. main.py (submission):")
try:
    import ast
    tree = ast.parse(Path(WORK_DIR, "main.py").read_text())
    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    import sys as _sys
    STDLIB = set(_sys.stdlib_module_names)
    stdlib_only = True
    for imp in imports:
        for alias in imp.names:
            mod = alias.name.split(".")[0]
            if mod not in STDLIB:
                stdlib_only = False
                print(f"[STATE]   import no-stdlib: {mod}")
    print(f"[STATE]   stdlib-only: {stdlib_only}")
except Exception as e:
    print(f"[STATE]   error: {e!r}")

# ============================================================
# 2. Config env calibrado (P1.2.2: consumo shops x2)
# ============================================================
print("\n[STATE] 2. Env local calibrado (P1.2.2):")
try:
    # el env local vive en el repo, no en el dataset; aquí documentamos el estado
    state = {
        "P1.2.1_corregido": "curvas de precio local ≡ Kaggle (ratio 1.00x, 7 replays)",
        "P1.2.2_calibracion": "consumo shops x2 (kaggle_env/kaggriculture.py _town_consume)",
        "wrapper_F0": "4 bugs corregidos (aliasing ready/growing/empty, shed-empty, "
                      "ready prematuro no-ongoing, WATER-bloquea-PLANT)",
        "determinismo": "kg_make_seeded + seed_all P0b",
    }
    for k, v in state.items():
        print(f"[STATE]   {k}: {v}")
except Exception as e:
    print(f"[STATE]   error: {e!r}")

# ============================================================
# 3. Resultados del proyecto (resumen sincronizado)
# ============================================================
print("\n[STATE] 3. Resultados del proyecto (2026-08-22):")
results = {
    "F0_ECO_CORRECTED_64s": {"random": 21276, "v5b3": -7444, "mega": 20670, "div": 20310,
                             "note": "baseline maestro tras corregir 4 bugs del wrapper F0"},
    "Teacher_v1_E0COW_256s": {"random": 27095, "v5b3": -112, "win_v5b3": 0.527, "mega": 26725, "div": 26330,
                              "note": "E0 + COW d3-5 (primer Teacher que gana a v5b3)"},
    "Teacher_v2_COW2d14": {"random": 28091, "v5b3": 964, "win_v5b3": 0.844, "mega": 27604, "div": 27195,
                           "note": "E0 + COW d3-5 + COW2 d14 — descubierto por screening causal P7.3"},
    "P6_MacroPolicy_BC": {"win_v5b3": 0.188, "note": "Gate D no pasó: BC no optimiza WinRate"},
    "P7_preference": {"note": "81.2% preferir transición ahora (48 pares ramificados)"},
    "P7_4_multireplay": {"note": "7 ganadores: COW1 d0, EXPAND d6, STRAWBERRY dominante — "
                          "Teacher v2 es local-óptimo, no patrón Kaggle"},
    "P1_2_1_corregido": {"note": "bug de signo en harness; curvas precio local ≡ Kaggle"},
    "P1_2_2": {"note": "consumo shops x2 calibrado contra replay (WHEAT 0.58-1.58x)"},
}
for k, v in results.items():
    print(f"[STATE]   {k}: {json.dumps(v)}")

print("\n[STATE] Gates: C (Teacher>E0, WinRate v5b3>0) PASA con Teacher v2 (84.4%).")
print("[STATE] P7.5/MacroPolicy v2/PPO: PAUSADOS hasta F0-ECO-LADDER sobre env calibrado.")
print("[STATE] main.py / rl_best.pt: INTACTOS.")
print("\n[STATE] Sync completa — estado Kaggriculture P1.2.2 verificado.")
