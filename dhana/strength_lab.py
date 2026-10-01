"""Reproducible local evaluation using the unmodified official interpreter.

This development tool is not imported by the submitted agent. The fast runner
omits history rendering/schema overhead; verify compares it to Kaggle's runner.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import gzip
import hashlib
import importlib.util
import io
import json
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".bench_deps"))
sys.path.insert(0, str(ROOT))
if sys.implementation.name == "pypy":
    from standalone_engine import make, __version__, engine, Struct
else:
    with contextlib.redirect_stdout(io.StringIO()):
        from kaggle_environments import make, __version__
        from kaggle_environments.envs.kaggriculture import kaggriculture as engine
        from kaggle_environments.utils import Struct

_CODE = {}


def clone_tree(value):
    """Copy the acyclic JSON observation tree without deepcopy's memo overhead."""
    if isinstance(value, dict):
        return {k: clone_tree(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clone_tree(v) for v in value]
    if isinstance(value, tuple):
        return tuple(clone_tree(v) for v in value)
    return value


def load(path, overrides=None):
    path = Path(path).resolve()
    if str(path).startswith("rawroute:"):
        raise ValueError(path)
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            actions = json.load(handle)["actions"]
        return lambda obs, cfg=None: copy.deepcopy(actions[obs["step"]])
    key = (str(path), path.stat().st_mtime_ns)
    if key not in _CODE:
        _CODE[key] = compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")
    name = "lab_" + hashlib.sha256(str(path).encode()).hexdigest()[:12]
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None))
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(_CODE[key], module.__dict__)
    for key, value in (overrides or {}).items():
        if key not in module.__dict__:
            raise ValueError(f"Unknown override: {key}")
        module.__dict__[key] = value
    return module.agent


def play(candidate, opponent, seed, seat=0, overrides=None, full=False, trace=False):
    agents = [load(candidate, overrides), load(opponent)]
    if seat:
        agents.reverse()
    elapsed = [0., 0.]
    maxima = [0., 0.]
    calls = [0, 0]
    recorded = []
    exceptions = []
    public_checkpoint = {}

    def call(i, obs, cfg):
        before = time.perf_counter()
        try:
            action = agents[i](obs, cfg)
            if i == seat and obs.get("step") == 72:
                ns = getattr(agents[i], "__globals__", {})
                public_checkpoint.update(own_money=obs["farms"][i]["money"],
                    signature=ns.get("_v52_signature", lambda _: None)(obs),
                    main=ns.get("_V51_USE_MAIN", {}).get(i),
                    rank41=ns.get("_V52_USE_RANK41", {}).get(i))
            if not isinstance(action, dict) or not isinstance(action.get("market", []), list):
                raise ValueError("Invalid action schema")
            return action
        except Exception as exc:
            exceptions.append({"seat": i, "step": obs.get("step"), "error": repr(exc)})
            raise
        finally:
            duration = time.perf_counter() - before
            elapsed[i] += duration
            maxima[i] = max(maxima[i], duration)
            calls[i] += 1

    start = time.perf_counter()
    if full:
        env = make("kaggriculture", configuration={"seed": seed}, debug=True)
        env.run([lambda obs, cfg: call(0, obs, cfg), lambda obs, cfg: call(1, obs, cfg)])
        states = env.state
    else:
        defaults = {k: v.get("default") if isinstance(v, dict) else v
                    for k, v in engine.specification["configuration"].items()}
        defaults["seed"] = seed
        env = SimpleNamespace(configuration=Struct(**defaults), info={}, done=False)
        states = [Struct(observation=Struct(step=0), action={}, reward=0, status="ACTIVE")
                  for _ in range(2)]
        engine.interpreter(states, env)
        for step in range(defaults["episodeSteps"] - 1):
            for i, state in enumerate(states):
                state.observation.step = step
                # Each player receives only its own private inventory. The seed
                # was scrubbed by the engine before the first agent call.
                observation = clone_tree(state.observation)
                observation["remainingOverageTime"] = 60
                state.action = call(i, observation, Struct(**clone_tree(env.configuration)))
            if trace:
                recorded.append({"step": step,
                                 "observation": copy.deepcopy(dict(states[seat].observation)),
                                 "actions": [copy.deepcopy(s.action) for s in states]})
            engine.interpreter(states, env)
    rewards = [float(s.reward) for s in states]
    row = {"candidate": str(candidate), "opponent": str(opponent), "seed": seed, "seat": seat,
           "rewards": rewards, "margin": rewards[seat] - rewards[1-seat],
           "statuses": [s.status for s in states], "wall_seconds": time.perf_counter()-start,
           "candidate_mean_ms": elapsed[seat]*1000/max(1, calls[seat]),
           "candidate_max_ms": maxima[seat]*1000, "exceptions": exceptions}
    row["telemetry"] = dict(getattr(agents[seat], "telemetry", {}))
    row["public_step72"] = public_checkpoint
    if trace:
        row["trace"] = recorded
    return row


def summary(rows):
    margins = [r["margin"] for r in rows]
    return {"games": len(rows), "wins": sum(m > 0 for m in margins),
            "draws": sum(m == 0 for m in margins), "losses": sum(m < 0 for m in margins),
            "mean_margin": statistics.fmean(margins) if margins else 0,
            "min_margin": min(margins, default=0),
            "all_done": all(r["statuses"] == ["DONE", "DONE"] for r in rows),
            "mean_call_ms": statistics.fmean(r["candidate_mean_ms"] for r in rows) if rows else 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", default="dhana/main.py")
    parser.add_argument("--opponent", default="main.py")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 314159])
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--overrides", default="{}")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--manifest")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--resume", action="store_true", help="Resume an identical candidate/configuration checkpoint")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    overrides = json.loads(args.overrides)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    source = Path(args.candidate).read_bytes()
    candidate_hash = hashlib.sha256(source).hexdigest()
    snapshots = ROOT / "analysis_artifacts" / "dhana_strength" / "sources"
    snapshots.mkdir(parents=True, exist_ok=True)
    frozen = snapshots / (candidate_hash + ".py")
    if not frozen.exists():
        frozen.write_bytes(source)
    original_candidate = args.candidate
    args.candidate = str(frozen)
    if args.verify:
        checks = []
        for seat in (0, 1):
            fast = play(args.candidate, args.opponent, args.seeds[0], seat, overrides)
            official = play(args.candidate, args.opponent, args.seeds[0], seat, overrides, full=True)
            assert fast["rewards"] == official["rewards"], (fast, official)
            assert fast["statuses"] == official["statuses"] == ["DONE", "DONE"]
            checks.append({"fast": fast, "official": official})
            print("VERIFIED", json.dumps(fast), flush=True)
        output.write_text(json.dumps({"engine": __version__, "complete": True,
            "candidate": original_candidate, "candidate_sha256": candidate_hash,
            "opponent_sha256": hashlib.sha256(Path(args.opponent).read_bytes()).hexdigest(),
            "overrides": overrides, "parity_checks": checks}, indent=2), encoding="utf-8")
        return
    if args.manifest:
        entries = json.loads(Path(args.manifest).read_text(encoding="utf-8"))["routes"]
        if args.limit:
            entries = entries[::max(1, len(entries)//args.limit)][:args.limit]
        jobs = [(args.candidate, e["path"], int(e["seed"]), seat, overrides, False, args.trace)
                for e in entries for seat in (0, 1)]
    else:
        jobs = [(args.candidate, args.opponent, seed, seat, overrides, False, args.trace)
                for seed in args.seeds for seat in (0, 1)]
    metadata = {"engine": __version__, "candidate": original_candidate,
                "candidate_sha256": candidate_hash, "overrides": overrides,
                "manifest": args.manifest}
    if not args.manifest:
        metadata["opponent_sha256"] = hashlib.sha256(Path(args.opponent).read_bytes()).hexdigest()
    rows = []
    if args.resume and output.exists():
        previous = json.loads(output.read_text(encoding="utf-8"))
        for key in ("engine", "candidate_sha256", "overrides", "opponent_sha256"):
            if previous.get(key) != metadata.get(key):
                raise ValueError(f"Cannot resume: {key} differs")
        requested = {(j[1], j[2], j[3]) for j in jobs}
        rows = [r for r in previous["rows"] if (r["opponent"], r["seed"], r["seat"]) in requested]
        done = {(r["opponent"], r["seed"], r["seat"]) for r in rows}
        jobs = [j for j in jobs if (j[1], j[2], j[3]) not in done]
        print("RESUMED", len(rows), "remaining", len(jobs), flush=True)
    total = len(rows) + len(jobs)
    output.write_text(json.dumps({**metadata, "complete": False, "expected_games": total,
                                 "summary": summary(rows), "rows": rows}), encoding="utf-8")
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(play, *job) for job in jobs]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            if len(rows) <= 10 or len(rows) % 25 == 0 or len(rows) == total:
                print(f"{len(rows)}/{total} seed={row['seed']} seat={row['seat']} margin={row['margin']}", json.dumps(summary(rows)), flush=True)
            if len(rows) % 25 == 0:
                output.write_text(json.dumps({**metadata, "complete": False, "expected_games": total,
                                              "summary": summary(rows), "rows": rows}), encoding="utf-8")
    payload = {**metadata, "complete": True, "expected_games": total,
               "summary": summary(rows), "rows": rows}
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("WROTE", output, flush=True)


if __name__ == "__main__":
    main()
