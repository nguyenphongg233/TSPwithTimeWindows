import unittest
import random
from tsptw.core import Instance, read_instance
from tsptw.generate import generate
from tsptw.milp import solve
from tsptw.exact_check import enumerate_feasible

class MilpTests(unittest.TestCase):
    def compare(self,instance):
        exact=enumerate_feasible(instance)
        result=solve(instance,10)
        self.assertEqual(result['objective'],exact['exact_objective'])
        self.assertEqual(result['status'],'OPTIMAL' if exact['feasible_permutations'] else 'INFEASIBLE_PROVEN')

    def test_sample(self):
        instance=read_instance('data/examples/topic12.inp')
        self.compare(instance)
        self.assertEqual(solve(instance,10)['objective'],380)

    def test_generated(self):
        for n in (1,5,8):
            for geo,tw in [('U','T'),('C','M'),('M','W')]:
                self.compare(generate(n,geo,tw,137)[0])

    def test_zero_time_subtours_and_asymmetry(self):
        self.compare(Instance([(0,10,0)]*3,[[0]*4 for _ in range(4)]))
        self.compare(Instance([(0,100,2),(0,100,0),(0,100,1)],
            [[0,8,1,7],[3,0,2,9],[9,4,0,2],[1,6,5,0]]))

    def test_random_asymmetric_against_exhaustive(self):
        rng=random.Random(20261106)
        for _ in range(12):
            n=6
            travel=[[0 if i==j else rng.randrange(15) for j in range(n+1)] for i in range(n+1)]
            windows=[]
            for _ in range(n):
                e=rng.randrange(20)
                windows.append((e,e+rng.randrange(10,65),rng.randrange(4)))
            self.compare(Instance(windows,travel))

    def test_infeasible_and_completion_after_deadline(self):
        self.compare(Instance([(0,0,0)],[[0,1],[1,0]]))
        self.compare(Instance([(10,10,20)],[[0,3],[99,0]]))

if __name__=='__main__': unittest.main()
