import numpy as np
from scipy.ndimage import distance_transform_edt
import SimpleITK as sitk
from ..readcine.readcines import CineImage
from ..readcine.convert_to_sitk import sitk_resample_mask_to_slice
from U2Dose.geometry.Grid3D import Grid3D
from U2Dose.patient.Roi import Roi


##########################################################################
def distance_map(mask:np.array, spacing:np.array) -> np.array:
    """ Create distance map such a narrow band can be constructed. """
    
    dt_inside = distance_transform_edt(mask, sampling = spacing)
    dt_outside = distance_transform_edt(1 - mask, sampling = spacing)
    dt = dt_inside - dt_outside
    
    return dt

##########################################################################
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

##########################################################################
def remove_center_cross(image:sitk.Image, block_size:int) -> sitk.Image:
    dim = np.array(image.GetSize())
    center = np.array([dim[0]// 2, dim[1] // 2, dim[2] // 2])
    low = center - block_size
    high = center + block_size
    low = np.maximum(low, [0, 0, 0])
    high = np.minimum(high, dim - 1)

    np_image = sitk.GetArrayFromImage(image)    
    np_image[low[2]:high[2]] = 0
    np_image[:,low[1]:high[1]] = 0
    np_image[:,:,low[0]:high[0]] = 0
        
    image_copy = sitk.GetImageFromArray(np_image)
    image_copy.SetOrigin(image.GetOrigin())
    image_copy.SetSpacing(image.GetSpacing())
    image_copy.SetDirection(image.GetDirection())

    return image_copy

##########################################################################
def create_grid(transversal, coronal, sagittal) -> Grid3D:
    
    x_00 = transversal.image.GetOrigin()[0]
    if not np.isclose(x_00, coronal.image.GetOrigin()[0]):
        raise ValueError("The origins of the images do not match in the x direction.")
    
    y_00 = transversal.image.GetOrigin()[1]
    if not np.isclose(y_00, sagittal.image.GetOrigin()[1]):
        raise ValueError("The origins of the images do not match in the y direction.")
    
    z_00 = sagittal.image.GetOrigin()[2]
    if not np.isclose(z_00, coronal.image.GetOrigin()[2]):
        raise ValueError("The origins of the images do not match in the z direction.")
        
    s_x = transversal.image.GetSpacing()[0]
    if not np.isclose(s_x, coronal.image.GetSpacing()[0]):
        raise ValueError("The spacings of the images do not match in the x direction.")

    s_y = transversal.image.GetSpacing()[1]
    if not np.isclose(s_y, sagittal.image.GetSpacing()[1]):
        raise ValueError("The spacings of the images do not match in the y direction.")
    
    s_z = coronal.image.GetSpacing()[2]
    if not np.isclose(s_z, sagittal.image.GetSpacing()[2]):
        raise ValueError("The spacings of the images do not match in the z direction.")
   

    d_x = transversal.image.GetSize()[0]
    if d_x != coronal.image.GetSize()[0]:
        raise ValueError("The sizes of the images do not match in the x direction.")

    d_y = transversal.image.GetSize()[1]
    if d_y != sagittal.image.GetSize()[1]:
        raise ValueError("The sizes of the images do not match in the y direction.")
    
    d_z = coronal.image.GetSize()[2]
    if d_z != sagittal.image.GetSize()[2]:
        raise ValueError("The sizes of the images do not match in the z direction.")
    
    pos_000 = np.array([x_00, y_00, z_00])
    spacing = np.array([s_x, s_y, s_z])
    dim = np.array([d_x, d_y, d_z])
    
    return Grid3D(pos_000, spacing, dim)


##########################################################################
def create_registration_mask(mask:Roi, cine:CineImage) -> sitk.Image:
    """ Create a 2D SimpleITK image from a 3D Roi representation of the registration mask. 
    Makes a 2D slice defined by the cine image. 
    The mask is dilated and then a center cross is removed.

    :param mask: Roi respresentation of mask
    :param cine: The cine image, defines where the 2D mask cut should be made
    :return: The registation mask
    """

    mask_slice = sitk_resample_mask_to_slice(mask, cine.image)

    dilation_distance = 20 # mm
    mask_slice = mask_dilation(mask_slice, dilation_distance=dilation_distance)

    num_pixels_per_side = 3
    mask_slice = remove_center_cross(mask_slice, num_pixels_per_side)

    return mask_slice


