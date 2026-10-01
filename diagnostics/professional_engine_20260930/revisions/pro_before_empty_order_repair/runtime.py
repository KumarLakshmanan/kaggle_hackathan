"""Online controller with explicit forecasts and bounded decision budgets."""
import copy
from .simulation import plain
from .beliefs import RivalBelief
from .scheduler import action
from .optimizer import optimize
from .planner import search
from .value import estimate


def itinerary(data, obs, cfg):
    step = int(obs['step'])
    if step < 72: return copy.deepcopy(data['opening'][step])
    shops = obs['town']['unlocked_shops']; route = None
    for count in range(1, min(len(shops), 8)+1):
        if step < 72*count: break
        selected = data['route_map'].get('|'.join(shops[:count]))
        if selected is not None: route = selected
    if route is None: route = next(iter(data['routes']))
    return copy.deepcopy(data['routes'][str(route)][min(step, 718)])


class Controller:
    def __init__(self, parent, data, model, physical=False):
        self.parent = parent; self.data = data; self.model = model; self.physical = physical
        self.reset()

    def reset(self):
        self.belief = RivalBelief(); self.previous_action = None; self.active_plan = None
        self.last_step = -1; self.last_forecast = None; self.last_value = None
        self.telemetry = {'pro_calls': 0, 'pro_market_changes': 0, 'pro_macro_activations': 0,
            'pro_physical_turns': 0, 'pro_nodes': 0, 'pro_forecast_transitions': 0, 'pro_cache_hits': 0, 'pro_errors': 0}

    def __call__(self, observation, configuration):
        obs, cfg = plain(observation), plain(configuration or {})
        step = int(obs['step'])
        if step <= self.last_step: self.reset()
        self.last_step = step
        baseline = self.parent(obs, cfg)
        belief = self.belief.update(obs, cfg, self.previous_action)
        self.last_value = estimate(obs, self.model)
        if self.physical and step in (144, 216) and self.active_plan is None:
            self.last_forecast = search(obs, cfg, belief, lambda o, c: itinerary(self.data, o, c), self.model, online=True)
            self.telemetry['pro_forecast_transitions'] += self.last_forecast['transitions']
            if self.last_forecast['selected']:
                self.active_plan = self.last_forecast['selected']['plan']; self.telemetry['pro_macro_activations'] += 1
        if self.active_plan is not None:
            baseline = action(obs, cfg, self.active_plan); self.telemetry['pro_physical_turns'] += 1
        chosen, report = optimize(obs, cfg, baseline, belief)
        self.telemetry['pro_calls'] += 1; self.telemetry['pro_nodes'] += report['nodes']
        self.telemetry['pro_market_changes'] += int(report['changed']); self.telemetry['pro_cache_hits'] += report['cache_hits']
        self.previous_action = copy.deepcopy(chosen)
        return chosen
