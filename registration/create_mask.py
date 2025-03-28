import numpy as np
from scipy.ndimage import distance_transform_edt
import SimpleITK as sitk
from ..readcine.readcines import SliceDirection

##########################################################################
def distance_map(mask:np.array, spacing:np.array) -> np.array:
    """ Create distance map such a narrow band can be constructed. """
    
    dt_inside = distance_transform_edt(mask, sampling = spacing)
    dt_outside = distance_transform_edt(1 - mask, sampling = spacing)
    dt = dt_inside - dt_outside
    
    return dt


def mask_dilation(mask:sitk.Image, dilation_distance) -> sitk.Image:
    """
    Enlarge a mask using distance map. 

    :param mask: the mask as sitk Image
    :param dilation_distance: Distance in wolrd units (mm) to dilate the mask
    :return: the dilated mask
    """
    np_mask = sitk.GetArrayFromImage(mask)
    spacing = mask.GetSpacing()
    dt = distance_map(np_mask, spacing)
    dt = dt + dilation_distance 
    np_mask_dilated = (dt >= 0).astype(np.uint8)
    mask_dilated = sitk.GetImageFromArray(np_mask_dilated)
    mask_dilated.SetOrigin(mask.GetOrigin())
    mask_dilated.SetSpacing(mask.GetSpacing())
    mask_dilated.SetDirection(mask.GetDirection())

    return mask_dilated


def create_mask_2d(mask:np.array, pos_000:np.array, spacing:np.array, slice_direction:SliceDirection) -> sitk.Image:
    """
    Create a 2D SimpleITK image from a numpy array representation of the mask. 
    The 2D slice is through the center of the 3D volume in the specified slice direction. 

    :param mask: Numpy array of the mask
    :param pos_000: Position of the pixel with lowest x, y, z, position
    :param spacing: Pixel spacing
    :return: The dilated mask
    """
    
    dim = mask.shape

    # cut image depending on the slice direction
    if slice_direction == SliceDirection.TRANSVERSAL:
        
        slice = mask[:, :, int(dim[2]/2)]
        pos_00 =[pos_000[0], pos_000[1]]
        spacing_2d = [spacing[0], spacing[1]]

    elif slice_direction == SliceDirection.SAGITTAL:
        
        slice = mask[int(dim[0]/2), :, :]
        pos_00 =[pos_000[1], pos_000[2]]
        spacing_2d = [spacing[1], spacing[2]]

    elif slice_direction == SliceDirection.CORONAL:
        
        slice = mask[:, int(dim[1]/2), :]
        pos_00 =[pos_000[0], pos_000[2]]
        spacing_2d = [spacing[0], spacing[2]]

    else:
        raise ValueError(f'Unknown slice direction {slice_direction}')
    
    sitk_image = sitk.GetImageFromArray(slice)

    # assign the geometry
    sitk_image.SetOrigin(pos_00)
    sitk_image.SetSpacing(spacing_2d)

    return sitk_image


def remove_center_cross(mask:np.array, half_block_size:int) -> np.array:
    dim = mask.shape
    center = [int(dim[0]/2), int(dim[1]/2)]
    mask_remove = mask.copy()
    mask_remove[center[0]-half_block_size:center[0]+half_block_size, center[1]-half_block_size:center[1]+half_block_size] = 0
    return mask_remove
