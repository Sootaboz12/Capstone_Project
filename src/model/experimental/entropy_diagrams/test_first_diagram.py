"""Check exact threshold selection against independently calculated cases."""

import math
import unittest

import numpy as np

from first_diagram import entropy, split_curve


class SplitterTests(unittest.TestCase):
    def test_entropy_and_perfect_split(self) -> None:
        np.testing.assert_allclose(entropy(np.array([0.0, 0.5, 1.0])), [0, 1, 0])
        curve = split_curve(np.array([0., 0., 2., 2.]), np.array([0, 0, 1, 1]))
        self.assertEqual(curve["threshold"].tolist(), [1.0])
        self.assertEqual(curve.iloc[0]["information_gain"], 1.0)

    def test_no_gain_when_groups_have_same_label_ratio(self) -> None:
        curve = split_curve(np.array([0., 0., 2., 2.]), np.array([0, 1, 0, 1]))
        self.assertEqual(curve.iloc[0]["information_gain"], 0.0)

    def test_scan_against_direct_partitioning(self) -> None:
        x = np.array([4., 0., 2., 0., 4., 8., 2.])
        y = np.array([1, 0, 1, 1, 0, 1, 0])

        def direct_entropy(labels: list[int]) -> float:
            p = sum(labels) / len(labels)
            return -sum(q * math.log2(q) for q in (p, 1 - p) if q)

        curve = split_curve(x, y)
        self.assertEqual(curve["threshold"].tolist(), [1., 3., 6.])
        for row in curve.itertuples(index=False):
            left = y[x < row.threshold].tolist()
            right = y[x >= row.threshold].tolist()
            expected = direct_entropy(y.tolist()) - (
                len(left) * direct_entropy(left) + len(right) * direct_entropy(right)
            ) / len(y)
            self.assertAlmostEqual(row.information_gain, expected)
            self.assertEqual(row.n_f, len(left))
            self.assertEqual(row.n_t, len(right))
            self.assertAlmostEqual(row.p_f, sum(left) / len(left))
            self.assertAlmostEqual(row.p_t, sum(right) / len(right))


if __name__ == "__main__":
    unittest.main()
