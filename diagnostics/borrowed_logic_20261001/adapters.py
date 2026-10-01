"""Individual donor transplants. No upload, replay identity or real hidden seed."""
import copy as _borrow_copy
import math as _borrow_math


class _BorrowBelief:
    def __init__(self):
        self.tracker = _BORROW_PACKAGE.beliefs.SupplyBelief()

    def update(self, obs, cfg, previous_action=None):
        summary = self.tracker.observe(obs, cfg, previous_action=previous_action)
        high = _BORROW_PACKAGE.beliefs.estimate_private(obs['farms'][1-int(obs['player'])],
                    dict(cfg, currentStep=int(obs['step'])), scale=1.8, summary=summary)
        interval = summary['sale_rate_interval']
        return {'stock_bounds':{p:{'low':0,'high':int(high['shed'].get(p,0))}
                                for p in _BORROW_PACKAGE.native_core.PRODUCTS},
                'visible_supply':summary['visible_daily_throughput'],
                'net_flow_ema':{p:v[0]/max(1,int(cfg.get('turnsPerDay',24))) for p,v in interval.items()},
                'residual_uncertainty':{p:max(0,v[1]-v[0]) for p,v in interval.items()},
                'history_samples':summary['observed_transitions'], 'donor_summary':summary,
                'scope':'Capacity-feasible rival stock hypotheses from public service/harvest/trade intervals; not actual private inventory.'}


def _borrow_worker_state(obs, cfg, action):
    core = _BORROW_PACKAGE.native_core
    projected = _borrow_copy.deepcopy(obs)
    seat = int(obs['player']); farm = projected['farms'][seat]; private=projected['private']
    commands=[action.get('farmer',['PASS']),*action.get('hands',[])]
    demand={}
    for cmd in commands:
        if isinstance(cmd,list) and len(cmd)>1 and cmd[0]=='PLANT':
            demand[cmd[1]]=demand.get(cmd[1],0)+1
    blocked={p for p,n in demand.items() if n>private['seeds'].get(p,0)}
    for index,cmd in enumerate(commands):
        if isinstance(cmd,list) and len(cmd)>1 and cmd[0]=='PLANT' and cmd[1] in blocked:cmd=['PASS']
        core._apply_unit_action(farm,private,index,cmd,len(farm['tiles']),
            int(obs['step'])//int(cfg.get('turnsPerDay',24)),int(cfg.get('turnsPerDay',24)),int(cfg.get('shedCapacity',100)))
    return projected


def _borrow_one_order(obs,cfg,order):
    core=_BORROW_PACKAGE.native_core;Box=_BORROW_PACKAGE.engine.Box
    result=_borrow_copy.deepcopy(obs);seat=int(obs['player'])
    states=[]
    for p in (0,1):
        private=result['private'] if p==seat else core._new_private()
        private['inventories']=private.get('inventories',[{}]) if p==seat else [{} for _ in range(1+len(result['farms'][p]['hands']))]
        states.append(Box(action={'market':[order] if p==seat else []},
            observation=Box(farms=result['farms'],market=result['market'],private=private)))
    core._process_market(states,Box(configuration=Box(**cfg)))
    return result


def _borrow_accounting(obs,cfg,action):
    projected=_borrow_worker_state(obs,cfg,action)
    orders=[];deferred=0;checks=0
    for order in action.get('market',[]):
        if not isinstance(order,list) or not order:
            orders.append(_borrow_copy.deepcopy(order));continue
        after=_borrow_one_order(projected,cfg,order)
        if order[0] in ('HIRE','BUY_LAND','BUY_SEED','BUY_ANIMAL'):
            checks+=1
            book=_BORROW_PACKAGE.commitments.build_book(after,cfg,include_candidates=False)
            needed=float(book['baseline']['required_cash'])
            if float(after['farms'][int(obs['player'])]['money'])+1e-9<needed:
                deferred+=1;continue
        projected=after;orders.append(_borrow_copy.deepcopy(order))
    return dict(action,market=orders),{'borrow_accounting_checks':checks,'borrow_deferred_orders':deferred}


class _BorrowController:
    def __init__(self,modes):
        self.modes=tuple(modes)
        runtime=_PRO_CONTROLLER.__call__.__func__.__globals__
        self.original_belief=runtime['RivalBelief']
        if 'belief' in self.modes:
            runtime['RivalBelief']=_BorrowBelief
            _PRO_CONTROLLER.reset()
        self.optimizer=runtime['optimize']
        self.reset()

    def reset(self):
        self.previous=None;self.last=-1
        self.market_belief=(_BorrowBelief if 'belief' in self.modes else self.original_belief)()
        self.stats={'borrow_calls':0,'borrow_changed_turns':0,'borrow_errors':0,
            'borrow_feed_changes':0,'borrow_feed_forced_workers':0,'borrow_deferred_orders':0,
            'borrow_accounting_checks':0,'borrow_dynamic_turns':0,'borrow_endgame_turns':0,
            'borrow_market_nodes':0,'borrow_combined_transitions':0}

    def __call__(self,observation,configuration=None):
        obs=_borrow_copy.deepcopy(observation);cfg=dict(configuration or {})
        step=int(obs['step']);tpd=max(1,int(cfg.get('turnsPerDay',24)))
        obs['day'],obs['hour']=divmod(step,tpd)
        if step<=self.last:self.reset()
        self.last=step;baseline=None
        try:
            if 'combined' in self.modes:
                engine=_BORROW_PACKAGE.engine
                summary=engine._BELIEF.observe(engine.visible_observation(obs),engine.clean_config(cfg,obs))
                chosen,report=engine.decide(obs,cfg,settings=engine.SearchConfig(seconds=0.,max_transitions=48),belief_summary=summary)
                engine._BELIEF.remember_action(chosen)
                self.stats['borrow_combined_transitions']+=report['transitions']
                self.stats['borrow_changed_turns']+=1
            else:
                if 'dynamic' in self.modes:
                    chosen=_BORROW_PACKAGE.reference_scheduler.schedule(obs,cfg,'balanced')
                    chosen=_BORROW_PACKAGE.engine.legalize(obs,chosen,_BORROW_PACKAGE.engine.clean_config(cfg,obs))
                    self.stats['borrow_dynamic_turns']+=1
                    baseline=None
                else:
                    baseline=_BORROW_PARENT(obs,cfg);chosen=baseline
                if 'endgame' in self.modes and step>=int(cfg.get('episodeSteps',720))-1-2*tpd:
                    chosen=_BORROW_PACKAGE.scheduler.schedule(obs,cfg,'liquidate',{'focus':'liquidate'})
                    chosen=_BORROW_PACKAGE.engine.legalize(obs,chosen,_BORROW_PACKAGE.engine.clean_config(cfg,obs))
                    self.stats['borrow_endgame_turns']+=1
                if 'feed' in self.modes:
                    repaired,report=_BORROW_PACKAGE.scheduler.repair_feed_service(obs,cfg,chosen,return_report=True)
                    self.stats['borrow_feed_changes']+=int(repaired!=chosen)
                    self.stats['borrow_feed_forced_workers']+=len(report['forced_workers'])
                    chosen=repaired
                    if report['forced_workers']:
                        chosen=_BORROW_PACKAGE.engine.legalize(obs,chosen,_BORROW_PACKAGE.engine.clean_config(cfg,obs))
                if 'accounting' in self.modes:
                    chosen,report=_borrow_accounting(obs,cfg,chosen)
                    for key,n in report.items():self.stats[key]+=n
                if baseline is None or chosen!=baseline:
                    # Recompute order search for changed worker/finance actions;
                    # never reuse an old shed forecast after changing workers.
                    chosen,search_report=_SEARCH_ENGINE['optimize_market'](obs,chosen,cfg,_SEARCH_SETTINGS)
                    self.stats['borrow_market_nodes']+=search_report['nodes']
                    belief=self.market_belief.update(obs,cfg,self.previous)
                    chosen,market_report=self.optimizer(obs,cfg,chosen,belief)
                    self.stats['borrow_market_nodes']+=market_report['nodes']
                self.stats['borrow_changed_turns']+=int(baseline is None or chosen!=baseline)
        except Exception as error:
            self.stats['borrow_errors']+=1
            self.last_error=type(error).__name__+': '+str(error)
            chosen=baseline if baseline is not None else _BORROW_PARENT(obs,cfg)
        self.previous=_borrow_copy.deepcopy(chosen)
        _PRO_CONTROLLER.previous_action=_borrow_copy.deepcopy(chosen)
        self.stats['borrow_calls']+=1
        return chosen


_BORROW_CONTROLLER=_BorrowController(BORROW_MODES)


def agent(observation,configuration=None):
    chosen=_BORROW_CONTROLLER(observation,configuration)
    agent.telemetry.update(_BORROW_CONTROLLER.stats)
    return chosen


agent.telemetry={}


def kaggle_borrowed_logic_entrypoint(observation,configuration=None):
    return agent(observation,configuration)
