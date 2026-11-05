import itertools
from pathlib import Path
import tempfile
import unittest
from tsptw.core import Instance, evaluate, read_instance, read_solution, write_instance, write_solution
from tsptw.generate import generate

class PipelineTests(unittest.TestCase):
    def test_topic_example(self):
        instance = read_instance('data/examples/topic12.inp')
        result = evaluate(instance, read_solution('data/examples/topic12.out',instance.n))
        self.assertEqual((result['travel_time'],result['completion_time']),(310,395))

    def test_all_families_and_roundtrip(self):
        for geo,tw,n in itertools.product('UCM','WMT',(1,8)):
            instance,route = generate(n,geo,tw,42)
            self.assertEqual((instance,route),generate(n,geo,tw,42))
            with tempfile.TemporaryDirectory() as folder:
                inp,out = Path(folder)/'x.inp',Path(folder)/'x.out'
                write_instance(instance,inp)
                write_solution(route,out)
                self.assertEqual(evaluate(instance,route),evaluate(read_instance(inp),read_solution(out,n)))

    def test_deadline_waiting_and_open_route(self):
        instance = Instance([(10,10,20)],[[0,3],[99,0]])
        result = evaluate(instance,[1])
        self.assertEqual((result['travel_time'],result['waiting_time'],result['completion_time']),(3,7,30))
        with self.assertRaises(ValueError):
            evaluate(Instance([(0,2,0)],instance.travel),[1])
        with self.assertRaises(ValueError):
            evaluate(instance,[0])

if __name__ == '__main__':
    unittest.main()
