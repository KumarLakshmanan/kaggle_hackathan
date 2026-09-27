from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from paired_benchmark import run_game

NEW=ROOT/"exp_shunki_mirror_quantity_20260927.py"
OLD=ROOT/"exp_shunki_market_queue_20260927.py"
RIVALS={"a2":OLD,"1f":ROOT/"exp_shunki_visible_repair_20260927.py",
        "489":ROOT/"main_uploaded_mirror_straw24_20260926_489fe8e4.py",
        "C95":ROOT/"diagnostics/public_rayk_top_meta/public_c95_main.py"}
SEEDS=list(range(2690000,2690008))


def point(r):
    return 1. if r["margin"]>0 else .5 if r["margin"]==0 else 0.


def game(job):
    rival,role,seed,seat=job
    r=run_game(str(NEW if role=="new" else OLD),str(RIVALS[rival]),seed,seat,False,144,{})
    return {"rival":rival,"role":role,"seed":seed,"seat":seat,"game":r}


def summarize(rows):
    scores={rival:{role:sum(point(r["game"]) for r in rows if r["rival"]==rival and r["role"]==role)
                   for role in ("old","new")} for rival in RIVALS}
    deltas=[sum((1 if r["role"]=="new" else -1)*point(r["game"]) for r in rows if r["seed"]==seed)/8 for seed in SEEDS]
    rng=random.Random(2690999)
    draws=sorted(sum(rng.choice(deltas) for _ in SEEDS)/len(SEEDS) for _ in range(10000))
    interval=[draws[249],draws[9749]]
    done=all(r["game"]["candidate_status"]==r["game"]["opponent_status"]=="DONE" for r in rows)
    errors=sum((r["game"].get("candidate_telemetry") or {}).get(k,0) for r in rows if r["role"]=="new" for k in ("queue_errors","quantity_errors","mirror_quantity_errors"))
    external_ok=all(scores[k]["new"]>=scores[k]["old"] for k in ("1f","489","C95"))
    head_ok=scores["a2"]["new"]>=12
    active_pairs=sum(all((r["game"].get("candidate_telemetry") or {}).get("quantity_turns",0)>0 for r in rows if r["rival"]=="a2" and r["role"]=="new" and r["seed"]==seed) for seed in SEEDS)
    gain=sum(s["new"]-s["old"] for s in scores.values())
    return {"scores":scores,"games":len(rows),"all_done":done,"queue_errors":errors,
            "pooled_point_gain":gain,"win_score_delta":sum(deltas)/len(SEEDS),
            "paired_seed_bootstrap_95":interval,"seed_deltas":deltas,
            "external_nonregression":external_ok,"head_thresholds":head_ok,"active_pairs":active_pairs,
            "passed":len(rows)==128 and active_pairs>=6 and done and errors==0 and external_ok and head_ok and gain>0 and interval[0]>0}


if __name__ == "__main__":
    digest=hashlib.sha256(NEW.read_bytes()).hexdigest()
    assert digest=="2765aed9d95f88b8e1bf66f3468dd91bdaa6a1cbd19b2b3b7d09aadbe0ee4cac"
    prior=json.loads((HERE/"top50_exclusion_proof.json").read_text())
    assert prior["sweeps"]==43 and prior["reused_games"]==100
    assert json.loads((HERE/"development.json").read_text())["passed"]
    rows=[]
    report={"candidate_sha256":digest,"plan_sha256":hashlib.sha256((HERE/"NATIVE_PLAN.md").read_bytes()).hexdigest(),
            "seeds":SEEDS,"artifacts":{k:{"path":str(p),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in {"new":NEW,**RIVALS}.items()},
            "rows":rows,"passed":False,"complete":False}
    jobs=[(rival,role,seed,seat) for seed in SEEDS for rival in RIVALS for role in ("old","new") for seat in (0,1)]
    with ProcessPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(game,j) for j in jobs]):
            r=f.result();rows.append(r)
            (HERE/"results.json").write_text(json.dumps(report,indent=2),encoding="utf8")
            print(len(rows),"/128",r["rival"],r["role"],r["seed"],r["seat"],r["game"]["margin"],flush=True)
    report["decision"]=summarize(rows);report["passed"]=report["decision"]["passed"];report["complete"]=True
    (HERE/"results.json").write_text(json.dumps(report,indent=2),encoding="utf8")
    print("DECISION",json.dumps(report["decision"]),flush=True)
