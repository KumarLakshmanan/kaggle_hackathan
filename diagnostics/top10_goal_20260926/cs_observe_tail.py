"""Telemetry-only view of the incumbent cow-to-goose decision."""

_CS_OBSERVE_PARENT = agent
_CS_OBSERVE_REPORT = {}


def agent(observation, configuration=None):
    action = _CS_OBSERVE_PARENT(observation, configuration)
    _CS_OBSERVE_REPORT.update(_CS_REPORT)
    return action


agent.telemetry = _CS_OBSERVE_REPORT
kaggle_submission_agent = agent
