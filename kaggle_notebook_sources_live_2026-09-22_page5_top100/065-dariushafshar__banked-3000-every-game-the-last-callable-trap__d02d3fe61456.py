import os, json, time, inspect, textwrap
from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

LIVE = {"actTimeout": 1, "episodeSteps": 720, "runTimeout": 1200}   # the live runner's configuration, read off a replay

# A file that binds `agent` EARLY (a stub), defines a helper LATER, then re-defines `agent` at the end.
BAD = textwrap.dedent("""
    from kaggle_environments.envs.kaggriculture.kaggriculture import agents as _builtin
    _starter = _builtin["starter"]

    def agent(obs, configuration=None):          # v1 stub, bound FIRST
        return {"farmer": ["PASS"], "hands": [], "market": []}

    def _first_shop(obs):                        # a helper, bound AFTER `agent`
        return ((obs or {}).get("town", {}) or {}).get("unlocked_shops", [])

    def agent(obs, configuration=None):          # the real agent -- RE-bound, position unchanged
        return _starter(obs)              # the built-in starter takes (obs) only
""")
open("bad_agent.py", "w").write(BAD)

fn = get_last_callable(open("bad_agent.py").read(), path="bad_agent.py")
print("Kaggle will call:", fn.__name__, inspect.signature(fn))

def play(paths, seed=1):
    env = make("kaggriculture", configuration={**LIVE, "seed": seed})
    env.run(paths)
    fin = env.steps[-1]
    banks = [float(s.reward or 0) for s in fin]
    passes = [sum(1 for st in env.steps[1:] if (st[i].action or {}).get("farmer") == ["PASS"]
                  and not (st[i].action or {}).get("market") and not (st[i].action or {}).get("hands")) for i in range(2)]
    return banks, [s.status for s in fin], passes

banks, statuses, passes = play(["bad_agent.py", "random"])
print(f"bad_agent.py vs random -> bank {banks[0]:.0f} (opponent {banks[1]:.0f}), status {statuses[0]}, PASS steps {passes[0]}/720")


GOOD = BAD + textwrap.dedent("""

    def kaggle_entrypoint(obs, configuration=None):   # NEW name, bound LAST -> this is what Kaggle calls
        return agent(obs, configuration)
""")
open("good_agent.py", "w").write(GOOD)

fn = get_last_callable(open("good_agent.py").read(), path="good_agent.py")
print("Kaggle will call:", fn.__name__, inspect.signature(fn))
banks, statuses, passes = play(["good_agent.py", "random"])
print(f"good_agent.py vs random -> bank {banks[0]:.0f} (opponent {banks[1]:.0f}), status {statuses[0]}, PASS steps {passes[0]}/720")


MAIN_PATH = "/kaggle/input/your-dataset/main.py"     # <- point this at your submission file, or
MAIN_SOURCE = ""                                      # <- paste its full source here instead

def check(path):
    fn = get_last_callable(open(path).read(), path=path)
    name = getattr(fn, "__name__", repr(fn))
    try:
        sig = inspect.signature(fn); nparams = len(sig.parameters)
    except Exception:
        sig, nparams = "<?>", 0
    print(f"loader resolves: {name}{sig}")
    ok = nparams >= 1
    for seat in (0, 1):
        paths = [path, "random"] if seat == 0 else ["random", path]
        banks, statuses, passes = play(paths, seed=7 + seat)
        # The trap's signature is exact: the bank never moves off $3000 and (almost) every turn is PASS.
        never_acted = banks[seat] == 3000.0 and passes[seat] >= 700
        good = statuses[seat] == "DONE" and not never_acted
        ok &= good
        print(f"seat {seat}: bank {banks[seat]:.0f} vs {banks[1-seat]:.0f} | status {statuses[seat]} | PASS steps {passes[seat]}/720 -> {'acted' if good else 'NEVER ACTED'}")
    print("VERDICT:", "PASS -- Kaggle calls a real policy" if ok else "FAIL -- Kaggle will NOT call the function you think it does")
    return ok

if MAIN_SOURCE.strip():
    open("main_under_test.py", "w").write(MAIN_SOURCE); check("main_under_test.py")
elif os.path.exists(MAIN_PATH):
    check(MAIN_PATH)
else:
    print("No file attached -- demonstrating on the two toy agents above.\n")
    print("--- bad_agent.py ---");  check("bad_agent.py")
    print("\n--- good_agent.py ---"); check("good_agent.py")
