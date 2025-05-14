

import numpy as np
import SimpleITK as sitk
from .readcine.readcines import CineImage, SliceDirection, resample_cine_to_identity 
from .registration.create_mask import create_registration_mask, create_grid
from .registration.preprocessing import crop_sequence, crop_image, find_crop_box
from .registration.preprocessing import histogram_matching_sequence
from .registration.group import group_registration_elastix
from U2Dose.patient.Roi import Roi
from U2Dose.dicomio.rtstruct import RtStruct

#################################################################################
def parameter_map_to_displacements(transform_parameter_map, reset_first=True):
    """ Extracts the displacements from a transform parameter map.
    Two parameters per displacement, one for each direction.
    """
    def mean_wo_extreme(v):
        imin = np.argmin(v)
        imax = np.argmax(v)
        v = np.delete(v,[imin, imax])
        return v

    transform_parameters = transform_parameter_map['TransformParameters']
    even = transform_parameters[::2]
    odd = transform_parameters[1::2]
    displacements = np.zeros([len(even), 2])
    displacements[:,0] = even
    displacements[:,1] = odd
    if reset_first:
        v = displacements[0:10,0]
        v = mean_wo_extreme(v)
        displacements[:,0] -= np.mean(v)

        v = displacements[0:10,1]
        v = mean_wo_extreme(v)
        displacements[:,1] -= np.mean(v)
    
    return displacements

#################################################################################
def sort_cines(cines:list[CineImage]) -> list[list[CineImage]]:
    """ Sorts the cines in slice directions. """
    
    time_sorted_transversal = list(filter(lambda cine: cine.direction == SliceDirection.TRANSVERSAL, cines))
    time_sorted_coronal = list(filter(lambda cine: cine.direction == SliceDirection.CORONAL, cines))
    time_sorted_sagittal = list(filter(lambda cine: cine.direction == SliceDirection.SAGITTAL, cines))
    
    return time_sorted_transversal, time_sorted_coronal, time_sorted_sagittal

#################################################################################
def extract_motion(cines:list[CineImage], rtss:RtStruct, max_n=1500) -> tuple[np.array, np.array, np.array]:
    """ Extract the motion of the from a cine directory.
    The cines are 
    1. Sorted in increasing time
    2. Sorted into slice directions
    3. Resampled to identity direction cosines.
    4. The cines are cropped to a mask created form the RTSS
    5. Registerered all together (per slice direction) using a group registation in Elastix
    6. The displacements are extracted from the transform parameter map.

    The motion is returned as a three tuples of (times, displacements), one for each slice direction.
    """
    #
    # Sort cines in time and then split into directions
    #
    cines = sorted(cines, key=lambda cine: cine.timestamp)
    transversals, coronals, sagittals = sort_cines(cines)
    
    #
    # Resample cines to identity direction cosines
    #
    transversals = [resample_cine_to_identity(cine) for cine in transversals]
    coronals = [resample_cine_to_identity(cine) for cine in coronals]
    sagittals = [resample_cine_to_identity(cine) for cine in sagittals]  

    #
    # Create the grid for the mask
    #
    grid = create_grid(transversals[0], coronals[0], sagittals[0])
    z_mm = Roi.from_rtstruct(rtss, name='Z_MM', grid=grid)

    mask_transversal = create_registration_mask(z_mm, transversals[0])
    mask_sagittal = create_registration_mask(z_mm, sagittals[0])
    mask_coronal = create_registration_mask(z_mm, coronals[0])

    # 
    # Crop mask and images in sequence
    #
    crop_box = find_crop_box(mask_transversal, m=30)
    transversals_cropped = crop_sequence(transversals, crop_box)
    transversals_cropped = histogram_matching_sequence(transversals_cropped[0], transversals_cropped)
    mask_transversal_cropped = crop_image(mask_transversal, crop_box)
    mask_transversal_cropped = sitk.Cast(mask_transversal_cropped, sitk.sitkUInt8)

    crop_box = find_crop_box(mask_sagittal, m=30)
    sagittals_cropped = crop_sequence(sagittals, crop_box)
    sagittals_cropped = histogram_matching_sequence(sagittals_cropped[0], sagittals_cropped)
    mask_sagittal_cropped = crop_image(mask_sagittal, crop_box)
    mask_sagittal_cropped = sitk.Cast(mask_sagittal_cropped, sitk.sitkUInt8)

    crop_box = find_crop_box(mask_coronal, m=30)
    coronals_cropped = crop_sequence(coronals, crop_box)
    coronals_cropped = histogram_matching_sequence(coronals_cropped[0], coronals_cropped)
    mask_coronal_cropped = crop_image(mask_coronal, crop_box)
    mask_coronal_cropped = sitk.Cast(mask_coronal_cropped, sitk.sitkUInt8)

    # 
    # perform the group registrations
    #
    resultImage, transformParameterMap_transversal = group_registration_elastix(transversals_cropped, mask_transversal_cropped, transversals[0].direction) 
    resultImage, transformParameterMap_sagittal = group_registration_elastix(sagittals_cropped, mask_sagittal_cropped, sagittals[0].direction)
    resultImage, transformParameterMap_coronal = group_registration_elastix(coronals_cropped, mask_coronal_cropped, coronals[0].direction)

    #
    # distill the motion into statistic
    #
    displacements_transversal = parameter_map_to_displacements(transformParameterMap_transversal[0], reset_first=True)
    displacements_sagittal = parameter_map_to_displacements(transformParameterMap_sagittal[0], reset_first=True)
    displacements_coronal = parameter_map_to_displacements(transformParameterMap_coronal[0], reset_first=True)

    t_transversal =[(cine.timestamp - transversals[0].timestamp).seconds for cine in transversals] 
    t_sagittal = [(cine.timestamp - sagittals[0].timestamp).seconds for cine in sagittals]
    t_coronal = [(cine.timestamp - coronals[0].timestamp).seconds for cine in coronals] 

    return t_transversal, displacements_transversal, t_sagittal, displacements_sagittal, t_coronal, displacements_coronal