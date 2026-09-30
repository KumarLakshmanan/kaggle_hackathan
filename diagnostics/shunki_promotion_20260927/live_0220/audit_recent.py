"""Read-only runtime check of eight latest public games for each active upload."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
KAGGLE = r"C:/Users/Veeramani Selvaraj/AppData/Roaming/Python/Python314/Scripts/kaggle.exe"


def collect(job):
    sid, episode = job
    incoming = HERE/"incoming"
    incoming.mkdir(exist_ok=True)
    eid = int(episode["id"])
    p = incoming/f"episode-{eid}-replay.json"
    if not p.exists():
        subprocess.run([KAGGLE,"competitions","replay",str(eid),"-p",str(incoming),"-q"],capture_output=True,check=True)
    raw = p.read_bytes()
    data = json.loads(raw)
    seat = data["info"]["TeamNames"].index("Lakshmanan R")
    rewards = data["rewards"]
    return {"submission":sid,"episode":eid,"create_time":episode["createTime"],"seat":seat,
            "statuses":data["statuses"],"own":rewards[seat],"rival":rewards[1-seat],
            "margin":rewards[seat]-rewards[1-seat],"replay_sha256":hashlib.sha256(raw).hexdigest(),
            "nonpass_farmer_commands":sum((frame[seat].get("action") or {}).get("farmer",["PASS"])[0] != "PASS" for frame in data["steps"][1:])}


if __name__ == "__main__":
    jobs=[]
    for sid in (56591314,56590642):
        episodes=json.loads((HERE/f"episodes_{sid}.json").read_text())
        completed=[e for e in episodes if e["state"].endswith("COMPLETED") and "PUBLIC" in e["type"]]
        jobs.extend((sid,e) for e in sorted(completed,key=lambda e:e["createTime"],reverse=True)[:8])
    rows=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(collect,j) for j in jobs]):
            r=f.result();rows.append(r)
            print(r["submission"],r["episode"],r["margin"],r["statuses"],flush=True)
    result={"selection":"Eight latest completed public episodes per active submission, without outcome filtering; different opponents, descriptive only","rows":rows}
    (HERE/"recent_runtime_audit.json").write_text(json.dumps(result,indent=2),encoding="utf8")
