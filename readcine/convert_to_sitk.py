import numpy as np
import SimpleITK as sitk

#########################################################################
def reorder_transversal(pixel_data:np.array, nrow, ncol) -> np.array:
    """ Redorder the flattened pixel matrix to fit SimplITK creation
    Transversal, i.e. direction cosines [1, 0, 0, 0, 1, 0, 0, 0, 1]
    :param pixel_data_1d: numpy array flattened
    :param nrow, ncol: Image dimensions
    :return: np.array of reordered pixel matrix
    """
    
    dim = [ncol, nrow, 1]

    #pixel_data = pixel_data_1d.reshape([nrow, ncol])
    image_reordered = np.zeros([dim[2], dim[1], dim[0]], dtype=int)
    for iz in range(0, dim[2]):
        for iy in range(0, dim[1]):
            for ix in range(0, dim[0]):
                image_reordered[iz, iy, ix] = pixel_data[ix, iy]

    return image_reordered

#########################################################################
def reorder_sagittal(pixel_data:np.array, nrow, ncol) -> np.array:
    """ Redorder the flattened pixel matrix to fit SimplITK creation
    Sagittal, i.e. direction cosines [1, 0, 0, 0, 0, -1, 0, 1, 0]
    :param pixel_data_1d: numpy array flattened
    :param nrow, ncol: Image dimensions
    :return: np.array of reordered pixel matrix
    """
    dim = [ncol, 1, nrow]

    #pixel_data = pixel_data_1d.reshape([nrow, ncol])
    image_reordered = np.zeros([dim[2], dim[1], dim[0]], dtype=int)
    for iz in range(0, dim[2]):
        for iy in range(0, dim[1]):
            for ix in range(0, dim[0]):
                image_reordered[iz, iy, ix] = pixel_data[ix, dim[2]-1-iz]

    return image_reordered

#########################################################################
def reorder_coronal(pixel_data:np.array, nrow, ncol) -> np.array:
    """ Redorder the flattened pixel matrix to fit SimplITK creation
    Coronal, i.e. direction cosines [0, 1, 0, 0, 0, -1, 1, 0, 0]
    :param pixel_data_1d: numpy array
    :param nrow, ncol: Image dimensions
    :return:
    """
    dim = [1, ncol, nrow]
    #pixel_data = pixel_data_1d.reshape([nrow, ncol])
    image_reordered = np.zeros([dim[2], dim[1], dim[0]], dtype=int)
    for iz in range(0, dim[2]):
        for iy in range(0, dim[1]):
            for ix in range(0, dim[0]):
                image_reordered[iz, iy, ix] = pixel_data[iy, dim[2]-1-iz]

    return image_reordered

def low_xyz_position(image_origin, direction_cosines, spacing, nrow, ncol, nslices):
    """" Find the position of pixel with lowest x, y, z, position. """
    pos_000 = image_origin
    dim = np.array([ncol, nrow, nslices])
    pos_nnn = pos_000 + np.dot(dim -1, np.reshape(direction_cosines, [3, 3])) * spacing
    return np.array([min(pos_000[0],pos_nnn[0]), min(pos_nnn[1],pos_nnn[1]), min(pos_nnn[2],pos_nnn[2])])

#########################################################################
def convert_np_to_sitk(pos_000:np.array, spacing:np.array, nrow, ncol, direction_cosines:np.array, pixel_data:np.array) -> sitk.Image:
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

    if np.allclose(direction_cosines, (1, 0, 0, 0, 1, 0, 0, 0, 1)):
        image_reordered = reorder_transversal(pixel_data, nrow, ncol)

    if np.allclose(direction_cosines, (1, 0, 0, 0, 0, -1, 0, 1, 0)):
        image_reordered = reorder_sagittal(pixel_data, nrow, ncol)

    if np.allclose(direction_cosines, (0, 1, 0, 0, 0, -1, 1, 0, 0)):
        image_reordered = reorder_coronal(pixel_data, nrow, ncol)

    # create the image
    sitk_image = sitk.GetImageFromArray(image_reordered)

    # assign the geometry
    low_xyz = low_xyz_position(pos_000, direction_cosines, spacing, nrow, ncol, 1)
    sitk_image.SetOrigin(low_xyz) 
    sitk_image.SetSpacing(spacing)

    # since the pxel matrix reordered the direction cosines are now the same regardless of slice direction
    sitk_image.SetDirection((1, 0, 0, 0, 1, 0, 0, 0, 1))

    return sitk_image