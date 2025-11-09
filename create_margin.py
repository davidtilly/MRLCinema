import SimpleITK as sitk
import numpy as np

def create_margin(mask:sitk.Image, margin:np.array) -> sitk.Image:
    """ Create a new binary image using a margin 

    Note! The binary mask is expanded with an integer number of voxels.
    if specified margin is not an even number of voxels, then the number of 
    voxels is rounded to nearest integer. 

    Note! Mask must be boolean with foreground = 1 and background = 0.
    If not then the function has undefined behaviour but will not throw.

    :param mask: mask to be expanded
    :param margin: margin to expand [x, y, z] (mm)
    :return expanded volume
    """ 

    if len(margin) != 3:
        raise ValueError(f'Margin must be specified with a single number in x, y, z (vector of length 3) {margin}')
    
    pixel_radius = margin / np.array(mask.GetSpacing())
    pixel_radius = (pixel_radius + 0.5).astype(int)

    image_margin = sitk.BinaryErode(mask, pixel_radius.tolist(), 	
                                    sitk.sitkBall,
                                    1, 0)
    return image_margin

