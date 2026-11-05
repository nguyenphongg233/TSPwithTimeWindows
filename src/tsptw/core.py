"""Strict topic-format I/O and earliest-service schedule evaluation."""
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Instance:
    windows: list[tuple[int, int, int]]
    travel: list[list[int]]

    @property
    def n(self):
        return len(self.windows)


def read_instance(path):
    lines = Path(path).read_text().splitlines()
    try:
        rows = [list(map(int, line.split())) for line in lines]
        if not rows or len(rows[0]) != 1:
            raise ValueError('first line must contain N')
        n = rows[0][0]
        if not 1 <= n <= 1000 or len(rows) != 2*n + 2:
            raise ValueError('N or number of lines is invalid')
        windows = rows[1:n+1]
        travel = rows[n+1:]
        if any(len(w) != 3 for w in windows):
            raise ValueError('each customer requires e l d')
        if any(e < 0 or l < e or d < 0 for e,l,d in windows):
            raise ValueError('require 0 <= e <= l and d >= 0')
        if any(len(row) != n+1 or any(t < 0 for t in row) for row in travel):
            raise ValueError('invalid travel matrix')
        return Instance([tuple(w) for w in windows], travel)
    except (ValueError, IndexError) as exc:
        raise ValueError(f'{path}: {exc}') from exc


def write_instance(instance, path):
    rows = [[instance.n], *instance.windows, *instance.travel]
    Path(path).write_text(''.join(' '.join(map(str,row))+'\n' for row in rows))


def read_solution(path, n):
    rows = Path(path).read_text().splitlines()
    if len(rows) != 2 or rows[0].split() != [str(n)]:
        raise ValueError('output requires two lines: N and a permutation')
    route = list(map(int, rows[1].split()))
    if len(route) != n or set(route) != set(range(1,n+1)):
        raise ValueError('route must be a permutation of 1..N')
    return route


def write_solution(route, path):
    Path(path).write_text(str(len(route))+'\n'+' '.join(map(str,route))+'\n')


def evaluate(instance, route):
    if len(route) != instance.n or set(route) != set(range(1,instance.n+1)):
        raise ValueError('route must be a permutation of 1..N')
    time = cost = waiting = 0
    previous = 0
    schedule = []
    for customer in route:
        e,l,d = instance.windows[customer-1]
        leg = instance.travel[previous][customer]
        arrival = time + leg
        start = max(arrival,e)
        if start > l:
            raise ValueError(f'customer {customer}: start {start} exceeds deadline {l}')
        waiting += start-arrival
        cost += leg
        time = start+d
        schedule.append((customer,arrival,start,time))
        previous = customer
    return dict(travel_time=cost, waiting_time=waiting, completion_time=time, schedule=schedule)
