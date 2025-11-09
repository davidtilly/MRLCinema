import unittest
import numpy as np
import SimpleITK as sitk
from MRLCinema.create_margin import create_margin



class TestCreateMargin(unittest.TestCase):
    """ Test the creation of margins. 
    Remmber simpleitk reverse pixel ordering. 
    """

    def test_expand_single_voxel(self):
        """ expand a single voxel (4, 2, 1) voxels in x, y, z. """
        mask = np.zeros([21, 21, 21], dtype=int)
        mask[10, 10, 10] = 1
        margin = np.array([2, 2, 2])

        sitk_mask = sitk.GetImageFromArray(mask)
        sitk_mask.SetSpacing([0.5, 1, 2])

        sitk_mask_margin = create_margin(sitk_mask, margin)
        mask_margin = sitk.GetArrayFromImage(sitk_mask_margin)
        
        # test expansion along X
        print(mask_margin[10,10, 6:14])
        self.assertTrue( np.all(mask_margin[10,10, 6:15]))
        self.assertFalse( np.any(mask_margin[10,10, 0:6]))
        self.assertFalse( np.any(mask_margin[10,10, 15:]))

        # test expansion along Y
        print(mask_margin[10,:,10])
        self.assertTrue( np.all(mask_margin[10,8:13,10]))
        self.assertFalse( np.any(mask_margin[10,0:8,10]))
        self.assertFalse( np.any(mask_margin[10,13:,10]))

        # test expansion along Z
        print(mask_margin[:,10])
        self.assertTrue( np.all(mask_margin[9:12, 10,10]))
        self.assertFalse( np.any(mask_margin[0:9,10]))
        self.assertFalse( np.any(mask_margin[12:,10,10]))



