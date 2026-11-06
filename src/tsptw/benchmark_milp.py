"""Run the MILP baseline and audit a directory of small input instances."""
import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path
import sys
import scipy
from .core import read_instance,read_solution,evaluate,write_solution
from .exact_check import enumerate_feasible
from .milp import solve,VERSION


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',default='data/n10')
    parser.add_argument('--references',default='results/reference',help='reporting only; never used by solver')
    parser.add_argument('--results',default='results/milp')
    parser.add_argument('--time-limit',type=float,default=300)
    parser.add_argument('--audit',action='store_true',help='exhaustive count and optimum, limited to N<=10')
    args=parser.parse_args()
    inputs=sorted(Path(args.inputs).glob('*.inp'))
    if not inputs: parser.error('no input files')
    target=Path(args.results)
    summary=target/'summary.csv'
    artifacts=[summary,target/'environment.json']
    for inp in inputs:
        artifacts.extend([target/(inp.stem+'.out'),target/'metrics'/(inp.stem+'.json')])
    if any(p.exists() for p in artifacts): parser.error('results exist; choose a fresh --results directory')
    if args.audit and any(read_instance(p).n>10 for p in inputs): parser.error('audit restricted to N<=10')
    target.mkdir(parents=True,exist_ok=True)
    (target/'metrics').mkdir(exist_ok=True)
    environment=dict(python=sys.version,scipy=scipy.__version__,platform=platform.platform(),machine=platform.machine(),
        solver='HiGHS bundled with SciPy',threads='solver default (not explicitly controlled)',
        evaluation_rules='closed_start_v1',algorithm_version=VERSION,
        timing='runtime_seconds measures scipy.optimize.milp call; model_seconds excludes I/O; end_to_end_seconds covers model+solve+validation, excludes file I/O and exhaustive audit')
    (target/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    fields=['instance','input_sha256','algorithm','algorithm_version','status','feasible','objective','best_bound','gap_percent',
        'runtime_seconds','model_seconds','end_to_end_seconds','time_limit_seconds','output_path','validation_status',
        'reference_travel','feasible_permutations','exact_objective','exact_match','visited_prefixes']
    with summary.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader()
        for inp in inputs:
            instance=read_instance(inp)
            result=solve(instance,args.time_limit)
            audit=enumerate_feasible(instance) if args.audit else {}
            exact_match=(result['objective']==audit['exact_objective']) if args.audit else None
            if args.audit and (not exact_match or (audit['feasible_permutations'] and result['status']!='OPTIMAL')):
                raise RuntimeError(f'MILP/exhaustive mismatch: {inp}')
            out=target/(inp.stem+'.out')
            if result['route'] is not None:
                write_solution(result['route'],out)
                evaluate(instance,read_solution(out,instance.n))
            reference=Path(args.references)/(inp.stem+'.out')
            ref_cost=evaluate(instance,read_solution(reference,instance.n))['travel_time'] if reference.exists() else None
            # Reference is read only after solving, for reporting; it is never fed to MILP.
            (target/'metrics'/(inp.stem+'.json')).write_text(json.dumps(dict(**result,audit=audit),indent=2)+'\n')
            row=dict(instance=inp.stem,input_sha256=hashlib.sha256(inp.read_bytes()).hexdigest(),algorithm='MILP_MTZ',
                algorithm_version=VERSION,status=result['status'],feasible=result['route'] is not None,objective=result['objective'],
                best_bound=result['best_bound'],gap_percent=result['gap_percent'],runtime_seconds=result['runtime_seconds'],
                model_seconds=result['model_seconds'],end_to_end_seconds=result['end_to_end_seconds'],
                time_limit_seconds=args.time_limit,output_path=str(out) if result['route'] is not None else '',
                validation_status=result['validation_status'],reference_travel=ref_cost,
                feasible_permutations=audit.get('feasible_permutations'),exact_objective=audit.get('exact_objective'),
                exact_match=exact_match,visited_prefixes=audit.get('visited_prefixes'))
            writer.writerow(row);handle.flush()
            print(f"{inp.stem}: {result['status']}, objective={result['objective']}, feasible tours={audit.get('feasible_permutations','not counted')}",flush=True)
    print(f'Saved {len(inputs)} runs: {summary}')

if __name__=='__main__': main()
