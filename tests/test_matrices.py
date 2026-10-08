"""Synthetic algorithm tests. No fixture represents kettle inventory data."""
import unittest
import numpy as np
from scipy.sparse import csc_matrix
from kettle_lca.matrices import construct, calculate, contributions


class MatrixTests(unittest.TestCase):
    def setUp(self):
        self.a, self.b, self.c = construct([
            {'id': 'synthetic-material', 'elementary': {'synthetic-emission': 2}},
            {'id': 'synthetic-product', 'inputs': {'synthetic-material': 3},
             'elementary': {'synthetic-emission': 1}}], ['synthetic-emission'], {'synthetic-emission': 4})

    def test_three_operations(self):
        r = calculate(self.a, self.b, self.c, [0, 1])
        np.testing.assert_allclose(r['s'], [3, 1])
        np.testing.assert_allclose(r['g'], [7])
        np.testing.assert_allclose(r['h'], [28])

    def test_cycle(self):
        a, b, c = construct([{'id': 'x', 'inputs': {'y': .2}, 'elementary': {'e': 1}},
                             {'id': 'y', 'inputs': {'x': .1}}], ['e'], {'e': 1})
        r = calculate(a, b, c, [1, 0])
        np.testing.assert_allclose(a @ r['s'], [1, 0])

    def test_contributions(self):
        r = contributions(self.a, self.b, self.c, {'a': [0, .3], 'b': [0, .7]}, [0, 1])
        np.testing.assert_allclose(sum(r.values()), [28])

    def test_bad_contributions(self):
        with self.assertRaises(ValueError):
            contributions(self.a, self.b, self.c, {'a': [0, .3]}, [0, 1])

    def test_unresolved_provider(self):
        with self.assertRaises(ValueError): construct([{'id': 'x', 'inputs': {'absent': 1}}], [], {})

    def test_missing_cf(self):
        with self.assertRaises(ValueError): construct([{'id': 'x'}], ['uncharacterized'], {})

    def test_singular(self):
        with self.assertRaises(ValueError): calculate(csc_matrix([[0.]]), csc_matrix([[1.]]), np.array([[1.]]), [1])

    def test_nonfinite(self):
        with self.assertRaises(ValueError): calculate(self.a, self.b, self.c, [0, float('nan')])

    def test_bad_dimension(self):
        with self.assertRaises(ValueError): calculate(self.a, self.b, self.c, [1])

    def test_negative_activity(self):
        with self.assertRaises(ValueError): calculate(csc_matrix([[-1.]]), csc_matrix([[1.]]), np.array([[1.]]), [1])


if __name__ == '__main__': unittest.main()
