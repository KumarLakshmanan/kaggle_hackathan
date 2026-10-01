"""Build frozen candidates or request an offline executable strategy suggestion."""
import argparse
import importlib.util
import json
from pathlib import Path
from .build import build
from .beliefs import RivalBelief
from .planner import search
from .runtime import itinerary


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='command', required=True)
    export = sub.add_parser('build'); export.add_argument('--baseline', type=Path, required=True)
    export.add_argument('--model', type=Path, required=True); export.add_argument('--output', type=Path, required=True)
    export.add_argument('--physical', action='store_true')
    plan = sub.add_parser('plan'); plan.add_argument('--baseline', type=Path, required=True)
    plan.add_argument('--model', type=Path, required=True); plan.add_argument('--input', type=Path, required=True)
    plan.add_argument('--output', type=Path, required=True); plan.add_argument('--transitions', type=int, default=12000)
    args = parser.parse_args()
    if args.command == 'build': result = build(args.output, args.baseline, args.model, args.physical)
    else:
        if args.output.exists(): raise FileExistsError(args.output)
        payload = json.loads(args.input.read_text(encoding='utf-8-sig')); obs = payload['observation']; cfg = payload['configuration']
        spec = importlib.util.spec_from_file_location('pro_offline_executor', args.baseline)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        belief = RivalBelief().update(obs, cfg)
        result = search(obs, cfg, belief, lambda o, c: itinerary(module._DATA, o, c),
                        json.loads(args.model.read_text()), max_transitions=args.transitions)
        args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
