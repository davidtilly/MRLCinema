
import SimpleITK as sitk
import numpy as np
from ..readcine.readcines import SliceDirection

###########################################################################################
def histogram_matching_sequence(image_reference:sitk.Image, image_sequence:list[sitk.Image]) -> list[sitk.Image]:

    images_matched = []
    for image in image_sequence:
        image_matched = sitk.HistogramMatching(image, image_reference, numberOfHistogramLevels = 2048, 
                                               numberOfMatchPoints = 10, thresholdAtMeanIntensity = False) 
        images_matched.append(image_matched)

    return images_matched

###########################################################################################
def find_crop_box(mask:sitk, m=10):
    """ Find min and max where mask is 1 """
    np_mask = sitk.GetArrayFromImage(mask)
    zs, ys, xs = np.where(np_mask > 0.5)
    min_z = min(zs)
    max_z = max(zs)
    min_y = min(ys)
    max_y = max(ys)
    min_x = min(xs)
    max_x = max(xs)

    min_z = max(0, min_z - m)
    max_z = min(mask.GetSize()[2], max_z + m)

    min_y = max(0, min_y - m)
    max_y = min(mask.GetSize()[1], max_y + m)

    min_x = max(0, min_x - m)
    max_x = min(mask.GetSize()[0], max_x + m)

    return [min_x, max_x, min_y, max_y, min_z, max_z]

###########################################################################################
def crop_image(mask:sitk.Image, box:list):
    """ Crop the mask to the region of interest. """
    xmin, xmax, ymin, ymax, zmin, zmax = box
    return mask[xmin:xmax, ymin:ymax, zmin:zmax]

###########################################################################################
def crop_sequence(cines:list, box:list):
    """ Crop the cine sequence using the box.
    """
    cines_cropped = []
    for cine in cines:
        cines_cropped.append(crop_image(cine.image, box))

    return cines_cropped

##########################################################################
def sequence_to_2d(images:list[sitk.Image], slice_direction) -> list[sitk.Image]:
    """ Convert a sequence to 2D images. """

    images_2d = []
    for image in images:
        image_2d = image_to_2d(image, slice_direction)
        images_2d.append(image_2d)

    return images_2d


##########################################################################
def image_to_2d(image, slice_direction) -> sitk.Image:
    """ Convert a 3D image to a 2D image. """

    if slice_direction == SliceDirection.TRANSVERSAL:
        return image[:,:,0] 

    elif slice_direction == SliceDirection.SAGITTAL:
        return image[0,:,:]

    elif slice_direction == SliceDirection.CORONAL:
        return image[:,0,:]
    
    else:
        raise ValueError(f'Unknown slice direction {slice_direction}')