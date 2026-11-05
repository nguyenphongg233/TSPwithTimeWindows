"""python -m tsptw.validate instance.inp solution.out"""
import argparse
import json
from .core import read_instance, read_solution, evaluate

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('instance')
    parser.add_argument('solution')
    args = parser.parse_args()
    try:
        instance = read_instance(args.instance)
        result = evaluate(instance, read_solution(args.solution, instance.n))
    except (ValueError, OSError) as exc:
        parser.exit(1, f'INVALID: {exc}\n')
    print(json.dumps(dict(valid=True, **result), indent=2))

if __name__ == '__main__':
    main()
