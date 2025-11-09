import SimpleITK as sitk
import numpy as np

def create_margin_sitk(mask:sitk.Image, pixel_radius:np.array) -> sitk.Image:
    """ Create a new binary image using a margin from a Simple ITK binay image

    :param mask: mask to be expanded
    :param pixel_radius: margin (in pixels) to expand 
    :return expanded volume
    """ 

    if len(pixel_radius) != 3:
        raise ValueError(f'Pixel radius must be specified with a single number in x, y, z (vector of length 3) {pixel_radius}')

    mask_margin = sitk.BinaryErode(mask, pixel_radius.tolist(), 	
                                   sitk.sitkBall,
                                   1, 0)
    return mask_margin

def create_margin(mask:np.array, spacing:np.array, margin:np.array) -> np.array:
    """ Create a new binary image using a margin 

    Note! The binary mask is expanded with an integer number of voxels.
    if specified margin is not an even number of voxels, then the number of 
    voxels is rounded to nearest integer. 

    Note! Mask must be boolean with foreground = 1 and background = 0.
    If not then the function has undefined behaviour but will not throw.

    :param mask   : mask to be expanded
    :param spacing: spacing btwn voxels  
    :param margin : margin to expand [x, y, z] (mm)
    :return expanded volume
    """ 

    if len(margin) != 3:
        raise ValueError(f'Margin must be specified with a single number in x, y, z (vector of length 3) {margin}')

    # convert to simple itk
    sitk_mask = sitk.GetImageFromArray(mask)
    sitk_mask = sitk.Cast(sitk_mask, sitk.sitkUInt8)
    sitk_mask.SetSpacing(spacing.tolist())

    # determine numberof pixels and convert to sitk order
    pixel_radius = margin / spacing
    pixel_radius = (pixel_radius + 0.5).astype(int)
    pixel_radius = pixel_radius[::-1]

    # apply the pixel margin
    sitk_mask_margin = create_margin_sitk(sitk_mask, pixel_radius)

    # convert back 
    mask_margin = sitk.GetArrayFromImage(sitk_mask_margin)
    
    return mask_margin