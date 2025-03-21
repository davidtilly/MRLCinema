import unittest
import numpy as np
from MRLCinema.registration.fit_rigid_transform import fit_rigid_transform

class TestStringMethods(unittest.TestCase):

    def test_translation(self):
        A = np.zeros([4, 3])
        A[0:] = np.array([1, 2, 3])
        A[1,:] = np.array([4, 5, 6])
        A[2,:] = np.array([7, 8, 9])
        A[2,:] = np.array([10, 11, 12])

        B = A + np.array([1, 2, 3])

        transform = fit_rigid_transform(A, B)

        self.assertTrue(np.allclose(transform[0:3, 3], np.array([1, 2, 3])))

    #def test_rotation(self):

if __name__ == '__main__':
    unittest.main()