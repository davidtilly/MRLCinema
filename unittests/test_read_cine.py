import unittest
import numpy as np
import os, glob
import SimpleITK as sitk
from MRLCinema.readcine.readcines import read_single_cine


def find_filename(sdirection:str, stype) -> str:
    test_root = '/home/david/source/MRLCinema/testdata'
    path = os.path.join(test_root, sdirection, f'*.{stype}')
    filenames = glob.glob(path)
    if len(filenames) != 1:
        raise ValueError(f'Expected to find exactly one file as {path} but found {len(filenames)}')
    return filenames[0]


class TestReadCine(unittest.TestCase):

    def test_read_cine_transversal(self):
        filename_bin = find_filename('transversal', 'bin')
        cine = read_single_cine(filename_bin)
        filename_dcm = find_filename('transversal', 'dcm')
        sitk_image = sitk.ReadImage(filename_dcm)

        self.assertTrue(np.allclose(sitk.GetArrayFromImage(cine.image), sitk.GetArrayFromImage(sitk_image)))

if __name__ == '__main__':
    unittest.main()