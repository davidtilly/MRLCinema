
import SimpleITK as sitk
import numpy as np

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

def crop_image(mask:sitk.Image, box:list):
    """ Crop the mask to the region of interest. """
    xmin, xmax, ymin, ymax, zmin, zmax = box
    return mask[xmin:xmax, ymin:ymax, zmin:zmax]

def crop_sequence(cines:list, box:list):
    """ Crop the cine sequence using the box.
    """
    cines_cropped = []
    for cine in cines:
        cines_cropped.append(crop_image(cine.image, box))

    return cines_cropped
        
