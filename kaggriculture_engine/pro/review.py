"""Guard offline suggestions whose itinerary control is outside model support."""
from .planner import search as raw_search


def search(*args, **kwargs):
    report = raw_search(*args, **kwargs)
    controls = report.get('baseline', [])
    supported = bool(controls) and not any(c.get('out_of_distribution', False) for c in controls)
    report['baseline_model_supported'] = supported
    if not supported:
        report['rejected_suggestion'] = report.get('selected')
        report['selected'] = None
        report['selection_blocked_reason'] = ('The baseline forecast extrapolates outside the fitted model. '
            'Supply a compatible continuation before accepting a strategy suggestion.')
    return report
