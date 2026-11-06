"""Deterministic planted-feasible instances; no external dependencies."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random
from .core import Instance, evaluate, write_instance, write_solution

VERSION = '2.0.0'
LEGACY_VERSION = '1.1.0'
FIELDS = ['instance','replicate','n','geometry','window','seed','generator_version','sha256','reference_travel','reference_waiting','reference_completion','mean_window_width','evaluation_rules']


def generate(n, geometry, window, seed, version=VERSION):
    if not 1 <= n <= 1000 or geometry not in ('U','C','M') or window not in ('W','M','T'):
        raise ValueError('invalid generation parameters')
    if version not in (VERSION, LEGACY_VERSION):
        raise ValueError('unsupported generator version')
    rng = random.Random(seed)
    centers = [(rng.uniform(100,900),rng.uniform(100,900)) for _ in range(4)]
    points = [(500,500)]
    for _ in range(n):
        if geometry == 'U' or (geometry == 'M' and rng.random() < .5):
            points.append((rng.uniform(0,1000),rng.uniform(0,1000)))
        else:
            x,y = rng.choice(centers)
            points.append((min(1000,max(0,rng.gauss(x,60))),min(1000,max(0,rng.gauss(y,60)))))
    travel = [[0 if i==j else max(1,math.ceil(math.hypot(x-u,y-v)))
               for j,(u,v) in enumerate(points)] for i,(x,y) in enumerate(points)]
    route = list(range(1,n+1))
    rng.shuffle(route)
    service = [rng.randint(1,30) for _ in range(n)]
    # Separate RNG: identical geometry, service, route and schedule across TW levels.
    wrng = random.Random(seed ^ 0x5EED)
    if version == LEGACY_VERSION:
        halfwidth = {'T':30,'M':150,'W':600}[window]
    else:
        # Scale overlap to the characteristic travel/service time of this instance.
        leg_mean = sum(travel[a][b] for a,b in zip([0]+route[:-1],route))/n
        scale = leg_mean + sum(service)/n
        halfwidth = max(30, math.ceil(scale * {'T':1,'M':2,'W':4}[window]))
    windows = [None]*n
    time = previous = 0
    for customer in route:
        target = time + travel[previous][customer] + rng.randint(0,30)
        if version == LEGACY_VERSION:
            left = int(wrng.random()*(halfwidth+1))
            right = int(wrng.random()*(halfwidth+1))
        else:
            left = math.floor(halfwidth*(0.5+0.5*wrng.random()))
            right = math.floor(halfwidth*(0.5+0.5*wrng.random()))
        windows[customer-1] = (max(0,target-left),target+right,service[customer-1])
        time = target + service[customer-1]
        previous = customer
    instance = Instance(windows,travel)
    evaluate(instance,route)
    return instance,route


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--config')
    source.add_argument('--replay-manifest', help='recreate the exact dataset from saved seeds')
    source.add_argument('--seed-manifest', help='reuse seeds with the current generator version; creates a new dataset')
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    root = Path(args.root)
    generation_version = VERSION
    if args.replay_manifest or args.seed_manifest:
        with Path(args.replay_manifest or args.seed_manifest).open() as handle:
            saved = list(csv.DictReader(handle))
        if any(row['generator_version'] not in (VERSION,LEGACY_VERSION) for row in saved):
            parser.error('generator version differs from manifest')
        jobs = [(int(r['n']),r['geometry'],r['window'],int(r['replicate']),int(r['seed'])) for r in saved]
        expected = {r['instance']:r['sha256'] for r in saved} if args.replay_manifest else {}
        versions = {r['instance']:r['generator_version'] for r in saved} if args.replay_manifest else {}
    else:
        config = json.loads(Path(args.config).read_text())
        used = set()
        jobs = []
        for n in config['sizes']:
            for geo in config['geometries']:
                for tw in config['windows']:
                    for replicate in range(1,config['replicates']+1):
                        seed = random.SystemRandom().getrandbits(64)
                        while seed in used:
                            seed = random.SystemRandom().getrandbits(64)
                        used.add(seed)
                        jobs.append((n,geo,tw,replicate,seed))
        expected = {}
        versions = {}
        generation_version = config.get('generator_version',VERSION)
        if generation_version not in (VERSION,LEGACY_VERSION):
            parser.error('unsupported generator version')
    manifest = root/'data'/'manifest.csv'
    planned = []
    for n,geo,tw,replicate,seed in jobs:
        if not 1 <= n <= 1000 or geo not in 'UCM' or tw not in 'WMT' or replicate < 1:
            parser.error('invalid generation parameters')
        stem = f'n{n}_{geo.lower()}_{tw.lower()}_{replicate:02d}'
        planned.extend([root/'data'/f'n{n}'/(stem+'.inp'),root/'results'/'reference'/(stem+'.out')])
    if manifest.exists() or len(set(planned)) != len(planned) or any(p.exists() for p in planned):
        parser.error('duplicate instance or existing file; use a fresh --root')
    rows = []
    for n,geo,tw,replicate,seed in jobs:
        stem = f'n{n}_{geo.lower()}_{tw.lower()}_{replicate:02d}'
        inp = root/'data'/f'n{n}'/(stem+'.inp')
        out = root/'results'/'reference'/(stem+'.out')
        version = versions.get(stem, generation_version)
        instance,route = generate(n,geo,tw,seed,version=version)
        inp.parent.mkdir(parents=True,exist_ok=True)
        out.parent.mkdir(parents=True,exist_ok=True)
        write_instance(instance,inp)
        write_solution(route,out)
        digest = hashlib.sha256(inp.read_bytes()).hexdigest()
        if stem in expected and digest != expected[stem]:
            parser.error(f'replay hash mismatch: {stem}')
        score = evaluate(instance,route)
        rows.append(dict(zip(FIELDS,[stem,replicate,n,geo,tw,seed,version,digest,
            score['travel_time'],score['waiting_time'],score['completion_time'],
            sum(l-e for e,l,d in instance.windows)/n,'closed_start_v1'])))
    manifest.parent.mkdir(parents=True,exist_ok=True)
    with manifest.open('w',newline='') as handle:
        writer = csv.DictWriter(handle,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Generated {len(rows)} instances; manifest: {manifest}')

if __name__ == '__main__':
    main()
