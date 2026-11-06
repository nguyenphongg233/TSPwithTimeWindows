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
        self.assertEqual((result['travel_time'],result['completion_time']),(380,465))

    def test_all_families_and_roundtrip(self):
        for geo,tw,n in itertools.product('UCM','WMT',(1,8)):
            instance,route = generate(n,geo,tw,42)
            self.assertEqual((instance,route),generate(n,geo,tw,42))
            with tempfile.TemporaryDirectory() as folder:
                inp,out = Path(folder)/'x.inp',Path(folder)/'x.out'
                write_instance(instance,inp)
                write_solution(route,out)
                self.assertEqual(evaluate(instance,route),evaluate(read_instance(inp),read_solution(out,n)))

    def test_window_levels_keep_geometry_and_nest(self):
        for geo in 'UCM':
            cases=[generate(10,geo,tw,42)[0] for tw in 'TMW']
            self.assertEqual(cases[0].travel,cases[2].travel)
            for narrow,wide in zip(cases,cases[1:]):
                for (en,ln,dn),(ew,lw,dw) in zip(narrow.windows,wide.windows):
                    self.assertLessEqual(ew,en)
                    self.assertLessEqual(ln,lw)
                    self.assertEqual(dn,dw)

    def test_legacy_geometry_and_service_preserved(self):
        old,old_route=generate(10,'C','T',42,version='1.1.0')
        new,new_route=generate(10,'C','T',42)
        self.assertEqual(old.travel,new.travel)
        self.assertEqual(old_route,new_route)
        self.assertEqual([w[2] for w in old.windows],[w[2] for w in new.windows])
        self.assertNotEqual(old.windows,new.windows)
        with self.assertRaises(ValueError):
            generate(10,'C','T',42,version='unknown')

    def test_deadline_waiting_and_return_to_depot(self):
        instance = Instance([(10,10,20)],[[0,3],[99,0]])
        result = evaluate(instance,[1])
        self.assertEqual((result['travel_time'],result['waiting_time'],result['completion_time']),(102,7,129))
        with self.assertRaises(ValueError):
            evaluate(Instance([(0,2,0)],instance.travel),[1])
        with self.assertRaises(ValueError):
            evaluate(instance,[0])

if __name__ == '__main__':
    unittest.main()
