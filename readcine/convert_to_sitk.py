import numpy as np
import SimpleITK as sitk
from U2Dose.patient.Roi import Roi


#########################################################################
def is_same_geometry(image_test:sitk.Image, image_ref:sitk.Image) -> bool:
    """ Check if two cine images have the same geometry. """
    if not np.allclose(image_test.GetSpacing(), image_ref.GetSpacing(), atol=1e-6):
        return False
        
    if not np.allclose(image_test.GetOrigin(), image_ref.GetOrigin(), atol=1e-6):
        return False
    if not np.allclose(image_test.GetDirection(), image_ref.GetDirection(), atol=1e-6):
        return False

    return True


#########################################################################
def convert_np_to_sitk(pos_000:np.array, spacing:np.array, direction_cosines, pixel_data:np.array) -> sitk.Image:
    """
    Convert numpy image to SimpleITK image. Note that the loop order is
    different when using GetImageFromArray, so the numpy must be in the correct orde. 
    The order should be [depth, col, row].

    :param pos_000: Position of first pixel, i.e. 1st row an column, will be the origin of the created image
    :param spacing: Pixel spacing
    :param direction_cosines: Direction cosines of the image data (sitk format)
    :param pixel_data: numpy array of pixel data [depth, col, row] 
    :return:
    """
    
    # create the image
    sitk_image = sitk.GetImageFromArray(pixel_data) 

    # assign the geometry
    sitk_image.SetOrigin(pos_000) 
    sitk_image.SetSpacing(spacing)

    # since the pixel matrix reordered the direction cosines are now the same regardless of slice direction
    sitk_image.SetDirection(direction_cosines)

    return sitk_image


#########################################################################
def sitk_resample(image, output_origin, output_spacing, output_size, output_direction):
    
    resample = sitk.ResampleImageFilter()
    resample.SetOutputOrigin(output_origin)
    resample.SetOutputSpacing(output_spacing)
    resample.SetSize(output_size)
    resample.SetOutputDirection(output_direction)
    resample.SetTransform(sitk.Transform())
    resample.SetDefaultPixelValue(0)
    resample.SetInterpolator(sitk.sitkLinear)
    image_resampled = resample.Execute(image)
    return image_resampled

#########################################################################
def sitk_resample_mask_to_slice(mask_3d:Roi, slice_image:sitk.Image) -> sitk.Image:
    sitk_mask_3d = sitk.GetImageFromArray(np.swapaxes(mask_3d.mask, 0, 2))
    sitk_mask_3d.SetOrigin(mask_3d.pos_000)
    sitk_mask_3d.SetSpacing(mask_3d.spacing)

    output_origin = slice_image.GetOrigin()
    output_spacing = slice_image.GetSpacing()
    output_size = slice_image.GetSize()
    output_direction = slice_image.GetDirection()

    return sitk_resample(sitk_mask_3d, output_origin, output_spacing, output_size, output_direction)
