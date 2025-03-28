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

        # test all geometry
        self.assertTrue(cine.is_transverse())
        self.assertTrue(np.allclose(sitk_image.GetSize(), cine.image.GetSize()))
        self.assertTrue(np.allclose(sitk_image.GetSpacing(), cine.spacing3d))
        self.assertTrue(np.allclose(sitk_image.GetOrigin(), cine.origin3d))
        self.assertTrue(np.allclose(sitk_image.GetDirection(), cine.image.GetDirection()))

        # test the image data
        print(sitk.GetArrayFromImage(sitk_image).shape)
        print(sitk.GetArrayFromImage(cine.image).shape)
        self.assertTrue(np.allclose(sitk.GetArrayFromImage(cine.image), sitk.GetArrayFromImage(sitk_image)))

    def test_read_cine_sagittal(self):
        filename_bin = find_filename('sagittal', 'bin')
        cine = read_single_cine(filename_bin)
        filename_dcm = find_filename('sagittal', 'dcm')
        sitk_image = sitk.ReadImage(filename_dcm)

        # test all geometry
        self.assertTrue(cine.is_sagittal())
        self.assertTrue(np.allclose(sitk_image.GetSize(), cine.image.GetSize()))
        self.assertTrue(np.allclose(sitk_image.GetSpacing(), cine.spacing3d))
        self.assertTrue(np.allclose(sitk_image.GetOrigin() , cine.origin3d))
        self.assertTrue(np.allclose(sitk_image.GetDirection(), cine.image.GetDirection()))

        # test the pixel data
        print(sitk.GetArrayFromImage(sitk_image).shape)
        print(sitk.GetArrayFromImage(cine.image).shape)
        self.assertTrue(np.allclose(sitk.GetArrayFromImage(cine.image), sitk.GetArrayFromImage(sitk_image)))

    def test_read_cine_coronal(self):
        filename_bin = find_filename('coronal', 'bin')
        cine = read_single_cine(filename_bin)
        filename_dcm = find_filename('coronal', 'dcm')
        sitk_image = sitk.ReadImage(filename_dcm)

        # test all geometry
        self.assertTrue(cine.is_coronal())
        self.assertTrue(np.allclose(sitk_image.GetSize(), cine.image.GetSize()))
        self.assertTrue(np.allclose(sitk_image.GetSpacing(), cine.spacing3d))
        self.assertTrue(np.allclose(sitk_image.GetOrigin() , cine.origin3d))

        # test the pixel data
        self.assertTrue(np.allclose(sitk.GetArrayFromImage(cine.image), sitk.GetArrayFromImage(sitk_image)))


if __name__ == '__main__':
    unittest.main()