import unittest
import numpy as np
import SimpleITK as sitk
from MRLCinema.create_margin import create_margin_sitk, create_margin



class TestCreateMargin(unittest.TestCase):
    """ Test the creation of margins. 
    Remmber simpleitk reverse pixel ordering. 
    """

    def test_expand_single_voxel_sitk(self):
        """ expand a single voxel (2, 3, 4) voxels. """
        mask = np.zeros([21, 21, 21], dtype=int)
        mask[10, 10, 10] = 1
        
        sitk_mask = sitk.GetImageFromArray(mask)
        
        pixel_radius = np.array([2, 3, 4]) # in sitk order
        sitk_mask_margin = create_margin_sitk(sitk_mask, pixel_radius)
        mask_margin = sitk.GetArrayFromImage(sitk_mask_margin)
        
        # test expansion along X
        print(mask_margin[10,10,:])
        self.assertTrue( np.all(mask_margin[10,10,8:13]))
        self.assertFalse( np.any(mask_margin[10,10,0:8]))
        self.assertFalse( np.any(mask_margin[10,10,13:]))

        # test expansion along Y
        print(mask_margin[10,:,10])
        self.assertTrue( np.all(mask_margin[10,7:14,10]))
        self.assertFalse( np.any(mask_margin[10,0:7,10]))
        self.assertFalse( np.any(mask_margin[10,14:,10]))

        # test expansion along Z
        print(mask_margin[:,10,10])
        self.assertTrue( np.all(mask_margin[6:15,10,10]))
        self.assertFalse( np.any(mask_margin[0:6,10]))
        self.assertFalse( np.any(mask_margin[15:,10,10]))


    def test_expand_single_voxel(self):
        """ Expand a single voxel (4, 3, 2) mm in x, y, z. """
        mask = np.zeros([21, 21, 21], dtype=int)
        mask[10, 10, 10] = 1
        margin = np.array([4, 3, 2])
        spacing = np.array([0.5, 1, 2])

        mask_margin = create_margin(mask, spacing, margin)
        
        # test expansion along X
        print(mask_margin[:,10,10])
        self.assertTrue( np.all(mask_margin[2:19,10,10]))
        self.assertFalse( np.any(mask_margin[0:2,10,10,]))
        self.assertFalse( np.any(mask_margin[19:,10,10]))

        # test expansion along Y
        print(mask_margin[10,:,10])
        self.assertTrue( np.all(mask_margin[10,7:14,10]))
        self.assertFalse( np.any(mask_margin[10,0:7,10]))
        self.assertFalse( np.any(mask_margin[10,14:,10]))

        # test expansion along Z
        print(mask_margin[10,10,:])
        self.assertTrue( np.all(mask_margin[10,10,9:12]))
        self.assertFalse( np.any(mask_margin[10,19,0:9]))
        self.assertFalse( np.any(mask_margin[10,10,12:]))


