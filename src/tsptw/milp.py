"""Closed-tour MILP baseline: binary arcs, service times and MTZ orders."""
import argparse
import json
from pathlib import Path
from time import perf_counter
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix
from .core import evaluate, read_instance, write_solution

VERSION = '1.0.0'


def solve(instance, time_limit=300):
    if time_limit <= 0:
        raise ValueError('time_limit must be positive')
    started = perf_counter()
    n = instance.n
    sink = n+1
    # A necessary local feasibility check only; no metric assumption is needed.
    arcs = [(0,j) for j in range(1,n+1) if instance.travel[0][j] <= instance.windows[j-1][1]]
    arcs += [(i,j) for i in range(1,n+1) for j in range(1,n+1) if i != j
             and instance.windows[i-1][0]+instance.windows[i-1][2]+instance.travel[i][j] <= instance.windows[j-1][1]]
    arcs += [(i,sink) for i in range(1,n+1)]
    m = len(arcs)
    b = {i:m+i-1 for i in range(1,n+1)}
    u = {i:m+n+i-1 for i in range(1,n+1)}
    size = m+2*n
    costs = np.zeros(size)
    lower = np.zeros(size)
    upper = np.ones(size)
    integrality = np.zeros(size, dtype=int)
    integrality[:m] = 1
    for k,(i,j) in enumerate(arcs):
        costs[k] = instance.travel[i][0 if j==sink else j]
    for i,(e,l,d) in enumerate(instance.windows,1):
        lower[b[i]],upper[b[i]] = e,l
        lower[u[i]],upper[u[i]] = 1,n
    ri,ci,values,lbs,ubs = [],[],[],[],[]
    def add(coefficients, lo=-np.inf, hi=np.inf):
        row = len(lbs)
        for col,value in coefficients.items():
            if value:
                ri.append(row);ci.append(col);values.append(value)
        lbs.append(lo);ubs.append(hi)
    incoming = {i:{} for i in range(1,n+2)}
    outgoing = {i:{} for i in range(n+1)}
    for k,(i,j) in enumerate(arcs):
        incoming[j][k]=1;outgoing[i][k]=1
    for coeff in outgoing.values(): add(coeff,1,1)
    for coeff in incoming.values(): add(coeff,1,1)
    for k,(i,j) in enumerate(arcs):
        if j==sink: continue
        e_j = instance.windows[j-1][0]
        duration = instance.travel[i][j]+(instance.windows[i-1][2] if i else 0)
        latest_i = instance.windows[i-1][1] if i else 0
        big_m = max(0,latest_i+duration-e_j)
        coeff = {b[j]:1,k:-big_m}
        if i: coeff[b[i]]=-1
        add(coeff,lo=duration-big_m)
        if i:
            add({u[j]:1,u[i]:-1,k:-n},lo=1-n)
    matrix = coo_matrix((values,(ri,ci)),shape=(len(lbs),size)).tocsc()
    model_seconds = perf_counter()-started
    solve_started = perf_counter()
    result = milp(costs, integrality=integrality, bounds=Bounds(lower,upper),
        constraints=LinearConstraint(matrix,lbs,ubs),
        options={'time_limit':float(time_limit),'mip_rel_gap':0.0,'presolve':True})
    solve_seconds = perf_counter()-solve_started
    route = None
    objective = None
    if result.x is not None:
        if np.max(np.abs(result.x[:m]-np.round(result.x[:m]))) > 1e-5:
            raise ValueError('solver incumbent has fractional arcs')
        successors = {i:j for k,(i,j) in enumerate(arcs) if result.x[k]>.5}
        route=[]; current=0
        for _ in range(n+1):
            current=successors.get(current)
            if current==sink: break
            if current is None or current in route:
                raise ValueError('invalid incumbent path')
            route.append(current)
        if current != sink:
            raise ValueError('incumbent does not terminate at depot copy')
        objective=evaluate(instance,route)['travel_time']
        if result.fun is None or abs(objective-result.fun)>1e-4:
            raise ValueError('MILP objective disagrees with independent evaluator')
    if result.status==0 and route is not None: status='OPTIMAL'
    elif result.status==1: status='FEASIBLE' if route is not None else 'NO_SOLUTION_FOUND'
    elif result.status==2: status='INFEASIBLE_PROVEN'
    else: status='ERROR'
    def finite(value):
        return float(value) if value is not None and np.isfinite(value) else None
    bound=finite(getattr(result,'mip_dual_bound',None))
    gap=100*(objective-bound)/max(1,abs(objective)) if objective is not None and bound is not None else None
    return dict(status=status,route=route,objective=objective,best_bound=bound,gap_percent=gap,
        solver_gap=finite(getattr(result,'mip_gap',None)),solver_status=int(result.status),message=result.message,
        model_seconds=model_seconds,runtime_seconds=solve_seconds,end_to_end_seconds=perf_counter()-started,
        time_limit_seconds=time_limit,variables=size,binary_variables=m,constraints=len(lbs),
        validation_status='VALID' if route is not None else 'NOT_APPLICABLE',evaluation_rules='closed_start_v1')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('instance')
    parser.add_argument('--output',required=True)
    parser.add_argument('--metrics',required=True)
    parser.add_argument('--time-limit',type=float,default=300)
    args=parser.parse_args()
    if Path(args.output).exists() or Path(args.metrics).exists():
        parser.error('output or metrics already exists')
    result=solve(read_instance(args.instance),args.time_limit)
    if result['route'] is not None:
        Path(args.output).parent.mkdir(parents=True,exist_ok=True)
        write_solution(result['route'],args.output)
    Path(args.metrics).parent.mkdir(parents=True,exist_ok=True)
    Path(args.metrics).write_text(json.dumps(result,indent=2)+'\n')
    print(f"{result['status']}: objective={result['objective']}")
    if result['status']=='ERROR': parser.exit(1)

if __name__=='__main__': main()
