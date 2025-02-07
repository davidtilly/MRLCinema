import numpy as np
from enum import Enum
import SimpleITK as sitk

class SliceDirection(Enum):
    TRANSVERSAL = 0
    CORONAL = 1
    SAGITTAL = 2

#########################################################################
def reorder_transversal(pixel_data:np.array, nrow, ncol) -> np.array:
    """ Redorder the pixel matrix to fit SimplITK creation
    Reverse order dims to fit SimpleITK (iy, ix) -> [ncol, nrow]  

    Transversal, i.e. direction cosines [1, 0, 0, 0, 1, 0]

    :param pixel_data: numpy array pixel matrix
    :param nrow, ncol: Image dimensions
    :return: np.array of reordered pixel matrix
    """
    
    image_reordered = np.zeros([nrow, ncol], dtype=int)
    for c in range(0, ncol):
        for r in range(0, nrow):
            image_reordered[r, c] = pixel_data[r, c]

    return image_reordered

#########################################################################
def reorder_sagittal(pixel_data:np.array, nrow, ncol) -> np.array:
    """ Sagittal, i.e. direction cosines
    
    Reorder from [0, 1, 0, 0, 0, -1] to [0, 1, 0, 0, 0, 1]
    
    :param pixel_data: numpy array pixel matrix
    :param nrow, ncol: Image dimensions
    :return: np.array of reordered pixel matrix
    """
    
    image_reordered = np.zeros([nrow, ncol], dtype=int)
    for r in range(0, nrow):
        for c in range(0, nrow):
            image_reordered[r, c] = pixel_data[nrow - r - 1, c]

    return image_reordered

#########################################################################
def reorder_coronal(pixel_data:np.array, nrow, ncol) -> np.array:
    """ 
    Coronal, i.e. direction cosines [0, 1, 0, 0, 0, -1], reorder to 
    [0, 1, 0, 0, 0, 1]
    
    :param pixel_data: numpy array with pixel data
    :param nrow, ncol: Image dimensions
    :return: np.array of reordered pixel matrix
    """
    
    image_reordered = np.zeros([nrow, ncol], dtype=int)
    
    for r in range(0, nrow):
        for c in range(0, ncol):
            image_reordered[r, c] = pixel_data[nrow - r -1, c]

    return image_reordered


def low_xyz_position(image_origin, slice_direction, spacing, nrow, ncol):
    """" Find the position of pixel with lowest x, y, z, position. """
    pos_000 = image_origin
    
    if slice_direction == SliceDirection.TRANSVERSAL:
        pos_00 = pos_000.take((0, 1))
        pos_nn = pos_00 + np.array([ncol, nrow]) * spacing.take((0, 1))
    elif slice_direction == SliceDirection.SAGITTAL:
        pos_00 = pos_000.take((1, 2))
        pos_nn = pos_00 + np.array([ncol, -nrow]) * spacing.take((1, 2))
    elif slice_direction == SliceDirection.CORONAL:
        pos_00 = pos_000.take((0, 2))
        pos_nn = pos_00 + np.array([ncol, -nrow]) * spacing.take((0, 2))

    return np.array([min(pos_00[0],pos_nn[0]), min(pos_00[1],pos_nn[1])])  

#########################################################################
def convert_np_to_sitk(pos_000:np.array, spacing:np.array, nrow:int, ncol:int, slice_direction:SliceDirection, pixel_data:np.array) -> sitk.Image:
    """
    Convert numpy image to SimpleITK image. Note that the loop order is
    different when using GetImageFromArray, so first need to convert
    before creating the image
    :param low_xyz: Porition of pixel with lowest x, y, z, position, will be the origin of the created image
    :param spacing: Pixel spacing
    :param nrow, ncol: 2D image dimensions
    :param direction_cosines: Direction cosines of the image data
    :param pixel_data: numpy array of pixel data
    :return:
    """
    image_reordered = None
    if slice_direction == SliceDirection.TRANSVERSAL:
        image_reordered = reorder_transversal(pixel_data, nrow, ncol)
        direction = (1, 0, 0, 1)

    elif slice_direction == SliceDirection.SAGITTAL:
        image_reordered = reorder_sagittal(pixel_data, nrow, ncol)
        direction = (1, 0, 0, 1) 

    elif slice_direction == SliceDirection.CORONAL:
        image_reordered = reorder_coronal(pixel_data, nrow, ncol)
        direction = (1, 0, 0, 1)
    else:
        raise ValueError(f'Unknown direction cosines {slice_direction}')

    # create the image
    sitk_image = sitk.GetImageFromArray(image_reordered.swapaxes(0, 1))

    # assign the geometry
    low_xyz = low_xyz_position(pos_000, slice_direction, spacing, nrow, ncol)
    sitk_image.SetOrigin(low_xyz) 
    sitk_image.SetSpacing(spacing)

    # since the pixel matrix reordered the direction cosines are now the same regardless of slice direction
    sitk_image.SetDirection(direction)

    return sitk_image