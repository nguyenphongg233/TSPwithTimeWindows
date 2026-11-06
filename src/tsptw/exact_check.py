"""Exhaustive enumeration with safe time-window prefix pruning, for small N only."""
from .core import evaluate


def enumerate_feasible(instance, max_n=10):
    if instance.n > max_n:
        raise ValueError(f'exhaustive check restricted to N <= {max_n}')
    count=0;best=None;best_route=None;prefixes=0
    def visit(previous,time,cost,remaining,route):
        nonlocal count,best,best_route,prefixes
        prefixes+=1
        if not remaining:
            count+=1
            value=cost+instance.travel[previous][0]
            if best is None or value<best:
                best=value;best_route=route[:]
            return
        for i in remaining:
            e,l,d=instance.windows[i-1]
            start=max(time+instance.travel[previous][i],e)
            if start<=l:
                visit(i,start+d,cost+instance.travel[previous][i],remaining-{i},route+[i])
    visit(0,0,0,set(range(1,instance.n+1)),[])
    if best_route is not None:
        assert evaluate(instance,best_route)['travel_time']==best
    return dict(feasible_permutations=count,exact_objective=best,exact_route=best_route,visited_prefixes=prefixes)
