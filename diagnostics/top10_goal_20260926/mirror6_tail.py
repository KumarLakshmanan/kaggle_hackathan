"""Pilot: six-turn sale advance only while both public farms physically match."""

_MIRROR6_REPORT = dict(clone_gate_turns=0, clone_gate_equal_turns=0,
                       clone_gate_adv_turns=0, clone_gate_errors=0)


def agent(observation, configuration=None):
    global _ADV_LOOK

    step = int(observation["step"])
    if step == 0:
        _MIRROR6_REPORT.update(clone_gate_turns=0, clone_gate_equal_turns=0,
                               clone_gate_adv_turns=0, clone_gate_errors=0)
    try:
        matched = _clone_physical_match(observation) if 144 <= step < 718 else False
    except Exception:
        _MIRROR6_REPORT["clone_gate_errors"] += 1
        matched = False
    _ADV_LOOK = 6 if matched else 4
    before = _ADV_REPORT.get("adv_turns", 0)
    action = _CLONE_PARENT(observation, configuration)
    if 144 <= step < 718:
        _MIRROR6_REPORT["clone_gate_turns"] += 1
        if matched:
            _MIRROR6_REPORT["clone_gate_equal_turns"] += 1
            if _ADV_REPORT.get("adv_turns", 0) > before:
                _MIRROR6_REPORT["clone_gate_adv_turns"] += 1
    _MIRROR6_REPORT.update(getattr(_CLONE_PARENT, "telemetry", {}))
    return action


agent.telemetry = _MIRROR6_REPORT
kaggle_submission_agent = agent
