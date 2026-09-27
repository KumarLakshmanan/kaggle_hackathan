"""Experiment: use longer sale lookahead only against a visible physical mirror."""

_CLONE_PARENT = agent
_CLONE_REPORT = dict(clone_gate_turns=0, clone_gate_equal_turns=0,
                     clone_gate_adv_turns=0, clone_gate_errors=0)


def _clone_physical_match(observation):
    farms = observation["farms"]
    if len(farms) != 2:
        return False
    return (farms[0]["tiles"] == farms[1]["tiles"]
            and farms[0]["farmer"] == farms[1]["farmer"]
            and farms[0]["hands"] == farms[1]["hands"])


def agent(observation, configuration=None):
    global _ADV_LOOK
    step = int(observation["step"])
    if step == 0:
        _CLONE_REPORT.update(clone_gate_turns=0, clone_gate_equal_turns=0,
                             clone_gate_adv_turns=0, clone_gate_errors=0)
    try:
        matched = _clone_physical_match(observation) if 144 <= step < 718 else False
    except Exception:
        _CLONE_REPORT["clone_gate_errors"] += 1
        matched = False
    _ADV_LOOK = 8 if matched else 4
    before = _ADV_REPORT.get("adv_turns", 0)
    action = _CLONE_PARENT(observation, configuration)
    if 144 <= step < 718:
        _CLONE_REPORT["clone_gate_turns"] += 1
        if matched:
            _CLONE_REPORT["clone_gate_equal_turns"] += 1
            if _ADV_REPORT.get("adv_turns", 0) > before:
                _CLONE_REPORT["clone_gate_adv_turns"] += 1
    _CLONE_REPORT.update(getattr(_CLONE_PARENT, "telemetry", {}))
    return action


agent.telemetry = _CLONE_REPORT
kaggle_submission_agent = agent
