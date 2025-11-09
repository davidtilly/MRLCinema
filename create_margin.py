import SimpleITK as sitk
import numpy as np

def create_margin(mask:sitk.Image, margin:np.array) -> sitk.Image:
    """ Create a new binary image using a margin 

    Note! Mask must be boolean with foreground = 1 and background = 0.
    If not then the function has undefined behaviour but will not throw.

    :param mask: mask to be expanded
    :param margin: margin to expand (mm)
    :return expanded volume
    """ 

    pixel_radius = margin / np.array(mask.GetSpacing())
    pixel_radius = (pixel_radius + 0.5).astype(int)

    image_margin = sitk.BinaryErode(mask, pixel_radius.tolist(), 	
                                    sitk.sitkBall,
                                    1, 0)
    return image_margin

