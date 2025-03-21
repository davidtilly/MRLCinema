
import SimpleITK as sitk
import numpy as np

def find_crop_box(mask:sitk, m=10):
    """ Find min and max where mask is 1 """
    np_mask = sitk.GetArrayFromImage(mask)
    ys, xs = np.where(np_mask > 0.5)
    return [min(xs)-m, max(xs)+m, min(ys)-m, max(ys)+m]

def crop_image(mask:sitk.Image, box:list):
    """ Crop the mask to the region of interest. """
    xmin, xmax, ymin, ymax = box
    return mask[xmin:xmax, ymin:ymax]

def crop_sequence(cines:list, box:list):
    """ Crop the cine sequence using the box.
    """
    cines_cropped = []
    for cine in cines:
        cines_cropped.append(crop_image(cine.image, box))

    return cines_cropped
        
