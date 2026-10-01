"""Build frozen candidates or request an offline executable strategy suggestion."""
import argparse
import importlib.util
import json
from pathlib import Path
from .build import build
from .beliefs import RivalBelief
from .review import search
from .runtime import itinerary
from .scheduler import commitment, action as scheduled_action


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='command', required=True)
    export = sub.add_parser('build'); export.add_argument('--baseline', type=Path, required=True)
    export.add_argument('--model', type=Path, required=True); export.add_argument('--output', type=Path, required=True)
    export.add_argument('--physical', action='store_true')
    plan = sub.add_parser('plan'); plan.add_argument('--baseline', type=Path)
    plan.add_argument('--model', type=Path); plan.add_argument('--input', type=Path, required=True)
    plan.add_argument('--output', type=Path, required=True); plan.add_argument('--transitions', type=int, default=12000)
    plan.add_argument('--control', choices=('maintenance', 'itinerary'), default='maintenance')
    plan.add_argument('--season', action='store_true', help='Simulate through native final cash with maturity and production ledgers.')
    args = parser.parse_args()
    if args.command == 'build': result = build(args.output, args.baseline, args.model, args.physical)
    else:
        if args.output.exists(): raise FileExistsError(args.output)
        payload = json.loads(args.input.read_text(encoding='utf-8-sig')); obs = payload['observation']; cfg = payload['configuration']
        belief = RivalBelief().update(obs, cfg)
        current_plan = commitment(obs)
        if args.control == 'itinerary':
            if not args.baseline: parser.error('--control itinerary requires --baseline.')
            spec = importlib.util.spec_from_file_location('pro_offline_executor', args.baseline)
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
            continuation = lambda o, c: itinerary(module._DATA, o, c)
        else: continuation = lambda o, c: scheduled_action(o, c, current_plan)
        if args.season:
            if args.control != 'maintenance': parser.error('Full-season suggestions require the compatible maintenance control.')
            from .season import search as season_search
            result = season_search(obs, cfg, belief, max_transitions=args.transitions)
        else:
            if not args.model: parser.error('Twelve-day tail estimates require --model; use --season for exact terminal forecasts.')
            result = search(obs, cfg, belief, continuation,
                            json.loads(args.model.read_text()), max_transitions=args.transitions)
            result['scope'] = 'Native executable twelve-day forecasts; baseline control '+args.control+'; heuristic reacting rivals and fitted terminal tail.'
        result['baseline_control'] = args.control
        if result.get('selected'):
            result['recommendation'] = dict(result['selected'], deployment_ready=False)
        elif not result.get('partial') and not result.get('selection_blocked_reason'):
            result['recommendation'] = {'name':'keep_existing_commitments', 'plan':current_plan,
                'reason':'No tested expansion passed the scenario improvement and execution gates.', 'deployment_ready':False}
        else:
            result['recommendation'] = {'name':'retain_current_policy', 'reason':result.get('selection_blocked_reason', 'Insufficient complete paired forecasts.'), 'deployment_ready':False}
        args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
