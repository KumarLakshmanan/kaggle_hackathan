"""Offline plan suggestions and standalone agent generation."""
import argparse
import importlib.util
import json
from pathlib import Path

from .build_agent import build, ROOT
from .planner import search_plan


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    export=commands.add_parser('build');export.add_argument('--output',type=Path,required=True)
    export.add_argument('--baseline',type=Path,default=ROOT/'main.py')
    export.add_argument('--nodes',type=int,default=48);export.add_argument('--depth',type=int,default=3)
    plan=commands.add_parser('plan');plan.add_argument('--input',type=Path,required=True)
    plan.add_argument('--output',type=Path,required=True)
    plan.add_argument('--baseline',type=Path,default=ROOT/'main.py')
    plan.add_argument('--horizon',type=int,default=12);plan.add_argument('--width',type=int,default=4)
    plan.add_argument('--nodes',type=int,default=400);plan.add_argument('--seconds',type=float,default=10.)
    args=parser.parse_args()
    if args.command=='build':
        if not 1<=args.nodes<=256 or not 1<=args.depth<=8: parser.error('Invalid search budget')
        result=build(args.output.resolve(),args.baseline.resolve(),args.nodes,args.depth)
    else:
        if args.output.exists(): raise FileExistsError(args.output)
        payload=json.loads(args.input.read_text(encoding='utf-8-sig'))
        specification=importlib.util.spec_from_file_location('engine_plan_executor',args.baseline)
        executor=importlib.util.module_from_spec(specification);specification.loader.exec_module(executor)
        # The immutable production itinerary is the default continuation. It
        # reads only current shops and step and cannot contaminate branch memory.
        def continuation(obs,cfg):
            import copy
            data=executor._DATA;step=int(obs['step'])
            if step<72:return copy.deepcopy(data['opening'][step])
            shops=obs['town']['unlocked_shops'];route=None
            for count in range(1,min(len(shops),8)+1):
                if step<72*count:break
                candidate=data['route_map'].get('|'.join(shops[:count]))
                if candidate is not None:route=candidate
            if route is None:route=next(iter(data['routes']))
            return copy.deepcopy(data['routes'][str(route)][min(step,718)])
        result=search_plan(payload['observation'],payload['configuration'],continuation,
                           args.horizon,args.width,args.nodes,args.seconds)
        result['baseline_continuation']='Immutable physical itinerary; distinct from full baseline agent.'
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
