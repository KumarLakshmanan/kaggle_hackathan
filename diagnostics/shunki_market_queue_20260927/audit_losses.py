"""Diagnostic reuse of two already-evaluated native losses; not a holdout."""
from collections import Counter
import gzip
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from trace_paired_game_events import run


if __name__ == "__main__":
    rows=[]
    for seed in (2660012,2660013):
        out=HERE/f"diagnostic_loss_{seed}.json.gz"
        if out.exists():
            with gzip.open(out,"rt",encoding="utf8") as h:trace=json.load(h)
        else:
            trace=run(str(ROOT/"exp_shunki_market_queue_20260927.py"),str(ROOT/"main_uploaded_mirror_straw24_20260926_489fe8e4.py"),seed,0)
            with gzip.open(out,"wt",encoding="utf8") as h:json.dump(trace,h,separators=(",",":"))
        failures=Counter();examples=[]
        for e in trace["events"]:
            if e["player"] != 0:continue
            if e["phase"] in ("market_unit","market_atomic") and not e["success"]:
                key=e["operation"]+":"+e.get("item","")+":"+str(e.get("failure_reason",""))
                failures[key]+=1
                if e["operation"] != "SELL" and len(examples)<20:examples.append(e)
        row={"seed":seed,"margin":trace["margin"],"statuses":[trace["candidate_status"],trace["opponent_status"]],
             "failures":dict(failures),"examples":examples,"trace":str(out)}
        rows.append(row)
        (HERE/"loss_diagnosis.json").write_text(json.dumps(rows,indent=2),encoding="utf8")
        print(seed,trace["margin"],dict(failures),flush=True)
