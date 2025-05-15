

import numpy as np
import SimpleITK as sitk
from .readcine.readcines import CineImage, SliceDirection, resample_cine_to_identity 
from .registration.create_mask import create_registration_mask, create_grid
from .registration.preprocessing import crop_sequence, crop_image, find_crop_box
from .registration.preprocessing import histogram_matching_sequence, image_to_2d, sequence_to_2d
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
def prepare_motion_analysis(cines:list[CineImage], rtss:RtStruct):
    """ Prepare the cines for subsequent motion analysis. """""

    #
    # Sort cines in time and then split into directions
    #
    cines = sorted(cines, key=lambda cine: cine.timestamp)
    transversals, coronals, sagittals = sort_cines(cines)
    
    #
    # Resample cines to identity direction cosines
    #
    transversals = [resample_cine_to_identity(cine) for cine in transversals]
    sagittals = [resample_cine_to_identity(cine) for cine in sagittals]  
    coronals = [resample_cine_to_identity(cine) for cine in coronals]

    #
    # Create the grid for the mask
    #
    grid = create_grid(transversals[0], coronals[0], sagittals[0])
    z_mm = Roi.from_rtstruct(rtss, name='Z_MM', grid=grid)

    mask_transversal = create_registration_mask(z_mm, transversals[0])
    mask_sagittal = create_registration_mask(z_mm, sagittals[0])
    mask_coronal = create_registration_mask(z_mm, coronals[0])


    # 
    # Prepocessoing by cropping (image and mask) and histogram matching
    #
    crop_box = find_crop_box(mask_transversal, m=30)
    transversals_cropped = crop_sequence(transversals, crop_box)
    transversals_cropped = histogram_matching_sequence(transversals_cropped[10], transversals_cropped)
    mask_transversal_cropped = crop_image(mask_transversal, crop_box)
    mask_transversal_cropped = sitk.Cast(mask_transversal_cropped, sitk.sitkUInt8)

    crop_box = find_crop_box(mask_sagittal, m=30)
    sagittals_cropped = crop_sequence(sagittals, crop_box)
    sagittals_cropped = histogram_matching_sequence(sagittals_cropped[10], sagittals_cropped)
    mask_sagittal_cropped = crop_image(mask_sagittal, crop_box)
    mask_sagittal_cropped = sitk.Cast(mask_sagittal_cropped, sitk.sitkUInt8)

    crop_box = find_crop_box(mask_coronal, m=30)
    coronals_cropped = crop_sequence(coronals, crop_box)
    coronals_cropped = histogram_matching_sequence(coronals_cropped[10], coronals_cropped)
    mask_coronal_cropped = crop_image(mask_coronal, crop_box)
    mask_coronal_cropped = sitk.Cast(mask_coronal_cropped, sitk.sitkUInt8)

    #
    # convert to 2D images
    #
    transversals_cropped = sequence_to_2d(transversals_cropped, SliceDirection.TRANSVERSAL)
    sagittals_cropped = sequence_to_2d(sagittals_cropped, SliceDirection.SAGITTAL)
    coronals_cropped = sequence_to_2d(coronals_cropped, SliceDirection.CORONAL)
    mask_transversal_cropped = image_to_2d(mask_transversal_cropped, SliceDirection.TRANSVERSAL)
    mask_sagittal_cropped = image_to_2d(mask_sagittal_cropped, SliceDirection.SAGITTAL)
    mask_coronal_cropped = image_to_2d(mask_coronal_cropped, SliceDirection.CORONAL)

    #
    # extract timing info
    #
    t_transversal =[(cine.timestamp - transversals[0].timestamp).seconds for cine in transversals] 
    t_sagittal = [(cine.timestamp - sagittals[0].timestamp).seconds for cine in sagittals]
    t_coronal = [(cine.timestamp - coronals[0].timestamp).seconds for cine in coronals] 

    prepared_cines = [transversals_cropped, sagittals_cropped, coronals_cropped]
    times = [t_transversal, t_sagittal, t_coronal] 
    masks = [mask_transversal_cropped, mask_sagittal_cropped, mask_coronal_cropped]

    return prepared_cines, times, masks


#################################################################################
def perform_motion_analysis(image_sequence:list[sitk.Image], mask:sitk.Image) -> np.array:
    """ Perform the group registration of a sequence of images. The mask determines which pixels are used for evaluation."""

    # 
    # perform the group registration
    #
    _resultImage, transformParameterMap = group_registration_elastix(image_sequence, mask) 
    
    #
    # extract the displacements for the sequence
    #
    displacements = parameter_map_to_displacements(transformParameterMap[0], reset_first=True)


    return displacements


#################################################################################
def extract_motion(cines:list[CineImage], rtss:RtStruct) -> tuple[np.array, np.array, np.array]:
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

    # preparation step 1-4
    prepared_cines, times, masks = prepare_motion_analysis(cines, rtss)
    transversals, sagittals, coronals = prepared_cines
    mask_transversal, mask_sagittal, mask_coronal = masks

    # motion extraction step 5-6
    displacements_transversal = perform_motion_analysis(transversals, mask_transversal) 
    displacements_sagittal = perform_motion_analysis(sagittals, mask_sagittal)
    displacements_coronal = perform_motion_analysis(coronals, mask_coronal) 

    displacements = [displacements_transversal, displacements_sagittal, displacements_coronal]

    return displacements, times

