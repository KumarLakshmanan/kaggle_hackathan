"""One-turn causal probe: force 4ee's step-170 queue to c68 order."""

import gzip
import hashlib
import json
from pathlib import Path
import sys

from kaggle_environments import make

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from paired_benchmark import _load_agent, _reward, _status
SEED = 383655650
ROUTE = HERE / "routes/Yizhou-submission-56608085-episode-114255901-seat1.json.gz"


class Intervention:
    def __init__(self, current, expected, old):
        self.current = current
        self.expected = expected
        self.old = old
        self.applied = False
        self.rival_at_252 = None

    def __call__(self, observation, configuration=None):
        step = int(observation["step"])
        if step == 252:
            rival = observation["farms"][1]
            self.rival_at_252 = {"cash": rival["money"], "land": list(rival["unlocked_quadrants"])}
        action = self.current(observation, configuration)
        if step == 170:
            assert action["market"] == self.expected
            action = dict(action, market=self.old)
            self.applied = True
        return action


if __name__ == "__main__":
    assert hashlib.sha256((HERE / "candidate_frozen.py").read_bytes()).hexdigest().startswith("4eeac9c3")
    trace_new = json.loads(gzip.decompress((HERE / "yizhou_current_seat0_trace.json.gz").read_bytes()))
    trace_old = json.loads(gzip.decompress((HERE / "yizhou_prior_seat0_trace.json.gz").read_bytes()))
    expected = trace_new["traces"][0][170]["action"]["market"]
    replacement = trace_old["traces"][0][170]["action"]["market"]
    current, current_timing = _load_agent(str(HERE / "candidate_frozen.py"), "yizhou_probe_current")
    rival, rival_timing = _load_agent("rawroute:" + str(ROUTE), "yizhou_probe_rival")
    candidate = Intervention(current, expected, replacement)
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": SEED}, debug=False)
    env.run([candidate, rival])
    final = env.steps[-1]
    out = {
        "seed": SEED, "candidate_seat": 0, "step": 170,
        "intervention": "Replace only the current candidate's step-170 market order with c68's order; all other turns use 4ee",
        "original_order": expected, "replacement_order": replacement,
        "applied": candidate.applied, "rival_pre_step_252": candidate.rival_at_252,
        "candidate_reward": _reward(final[0]), "opponent_reward": _reward(final[1]),
        "margin": _reward(final[0]) - _reward(final[1]),
        "candidate_status": _status(final[0]), "opponent_status": _status(final[1]),
        "frames": len(env.steps),
    }
    (HERE / "yizhou_turn170_probe.json").write_text(json.dumps(out, indent=2), encoding="utf8")
    print(json.dumps(out, indent=2))
