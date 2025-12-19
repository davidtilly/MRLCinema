

import numpy as np
import SimpleITK as sitk

from readcine.convert_to_sitk import is_same_geometry
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
def sort_cines_direction(cines:list[CineImage]) -> list[list[CineImage]]:
    """ Sorts the cines in slice directions. """
    time_sorted_transversal = list(filter(lambda cine: cine.is_transversal(), cines))
    time_sorted_coronal = list(filter(lambda cine: cine.is_coronal(), cines))
    time_sorted_sagittal = list(filter(lambda cine: cine.is_sagittal(), cines))
    
    return time_sorted_transversal, time_sorted_coronal, time_sorted_sagittal

#################################################################################
def filter_geometry(cines:list[CineImage], reference_image:CineImage=None) -> list[CineImage]:
    """ Filter out any cine that does not match the geometry of either the template or the majority of the first cine. """
    
    filtered_cines = []

    if reference_image != None:

        filtered_cines = list(filter(lambda cine: is_same_geometry(cine.image, reference_image.image), cines))

    else:
        ref_image = cines[0].image
        filtered_cines_0 = list(filter(lambda cine: is_same_geometry(cine.image, ref_image), cines))

        ref_image = cines[-1].image
        filtered_cines_1 = list(filter(lambda cine: is_same_geometry(cine.image, ref_image), cines))

        if len(filtered_cines_0) > len(filtered_cines_1):
            filtered_cines = filtered_cines_0
        else:
            filtered_cines = filtered_cines_1

    return list(filtered_cines)

#################################################################################
def prepare_masks(transversal, coronal, sagittal, rtss:RtStruct):
    """ Prepare the masks and crop boxes for subsequent motion analysis. """

    # Create the grid for the mask
    grid = create_grid(transversal, coronal, sagittal)
    z_mm = Roi.from_rtstruct(rtss, name='Z_MM', grid=grid)

    # Create masks per slice direction
    mask_transversal = create_registration_mask(z_mm, transversal)
    mask_coronal = create_registration_mask(z_mm, coronal)
    mask_sagittal = create_registration_mask(z_mm, sagittal)

    # crop mask to box
    crop_box_transversal = find_crop_box(mask_transversal, m=30)
    mask_transversal_cropped = crop_image(mask_transversal, crop_box_transversal)
    mask_transversal_cropped = sitk.Cast(mask_transversal_cropped, sitk.sitkUInt8)
    
    crop_box_coronal = find_crop_box(mask_coronal, m=30)
    mask_coronal_cropped = crop_image(mask_coronal, crop_box_coronal)
    mask_coronal_cropped = sitk.Cast(mask_coronal_cropped, sitk.sitkUInt8)

    crop_box_sagittal = find_crop_box(mask_sagittal, m=30)
    mask_sagittal_cropped = crop_image(mask_sagittal, crop_box_sagittal)
    mask_sagittal_cropped = sitk.Cast(mask_sagittal_cropped, sitk.sitkUInt8)

    # convert to 2D images
    mask_transversal_cropped = image_to_2d(mask_transversal_cropped, SliceDirection.TRANSVERSAL)
    mask_coronal_cropped = image_to_2d(mask_coronal_cropped, SliceDirection.CORONAL)
    mask_sagittal_cropped = image_to_2d(mask_sagittal_cropped, SliceDirection.SAGITTAL)
    
    return [mask_transversal_cropped, mask_coronal_cropped, mask_sagittal_cropped],[crop_box_transversal, crop_box_coronal, crop_box_sagittal] 


#################################################################################
def resample_to_identity(transversals:list[CineImage], coronals:list[CineImage], sagittals:list[CineImage]
                         ) -> tuple[list[CineImage], list[CineImage], list[CineImage]]:
    """ Resample cines to identity direction cosines."""
    
    transversals = [resample_cine_to_identity(cine) for cine in transversals]
    coronals = [resample_cine_to_identity(cine) for cine in coronals]  
    sagittals = [resample_cine_to_identity(cine) for cine in sagittals]

    return transversals, coronals, sagittals

#################################################################################
def prepare_images(transversals:list[sitk.Image], coronals:list[sitk.Image], sagittals:list[sitk.Image], 
                   crop_boxes) -> tuple[list[sitk.Image], list[sitk.Image], list[sitk.Image]]:
    """ Prepare images for motion analysis, 
    1. Crop to crop box
    2. Histogram matching 
    3. Convert to 2D images. """
    
    # Crop images to box
    transversals_cropped = crop_sequence(transversals, crop_boxes[0])
    coronals_cropped = crop_sequence(coronals, crop_boxes[1])
    sagittals_cropped = crop_sequence(sagittals, crop_boxes[2])
    
    # Histogram matching
    transversals_cropped = histogram_matching_sequence(transversals_cropped[10], transversals_cropped)
    coronals_cropped = histogram_matching_sequence(coronals_cropped[10], coronals_cropped)
    sagittals_cropped = histogram_matching_sequence(sagittals_cropped[10], sagittals_cropped)

    # convert to 2D images
    transversals_cropped = sequence_to_2d(transversals_cropped, SliceDirection.TRANSVERSAL)
    coronals_cropped = sequence_to_2d(coronals_cropped, SliceDirection.CORONAL)
    sagittals_cropped = sequence_to_2d(sagittals_cropped, SliceDirection.SAGITTAL)
    
    return transversals_cropped, coronals_cropped, sagittals_cropped

#################################################################################
def extract_times(cines:list[CineImage], t_start) -> np.array:
    """ Extract the timing info from a list of CineImage objects. """
    def delta_t(t1, t0):
        delta = t1 - t0
        return delta.seconds + delta.microseconds * 1e-6
    ts =[delta_t(cine.timestamp, t_start) for cine in cines] 
    return ts

#################################################################################
def prepare_motion_analysis_(cines:list[CineImage], rtss:RtStruct):
    """ Prepare the cines for subsequent motion analysis. """""

    #
    # Sort cines in time and then split into directions
    #
    cines = sorted(cines, key=lambda cine: cine.timestamp)
    transversals, sagittals, coronals = sort_cines(cines)
    
    #
    # Remove any image that does not match the expected geometry
    #
    transversals = filter_geometry(transversals)
    sagittals = filter_geometry(sagittals)
    coronals = filter_geometry(coronals)

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
    def delta_t(t1, t0):
        delta = t1 - t0
        return delta.seconds + delta.microseconds * 1e-6
    t_transversal =[delta_t(cine.timestamp, transversals[0].timestamp) for cine in transversals] 
    t_sagittal = [delta_t(cine.timestamp, sagittals[0].timestamp) for cine in sagittals]
    t_coronal = [delta_t(cine.timestamp, coronals[0].timestamp) for cine in coronals] 

    prepared_cines = [transversals_cropped, sagittals_cropped, coronals_cropped]
    times = [t_transversal, t_sagittal, t_coronal] 
    masks = [mask_transversal_cropped, mask_sagittal_cropped, mask_coronal_cropped]

    return prepared_cines, times, masks


#################################################################################
def motion_analysis_single_plane(image_sequence:list[sitk.Image], mask:sitk.Image) -> np.array:
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
def extract_motion2(images:list[sitk.Image], mask:sitk.Image, crop_box: np.array) -> np.array:
    """ Extract the motion of the from a cine directory.
    The cines are 
    1. Sorted in increasing time
    2. Sorted into slice directions
    3. Resampled to identity direction cosines.
    4. The cines are cropped to a mask created form the RTSS
    5. Registerered all together (per slice direction) using a group registation in Elastix
    6. The displacements are extracted from the transform parameter map.

    The motion is returned as a tuple of (times, displacements).
    """

    images_cropped = crop_sequence(images, crop_box)
    
    #
    # Histogram matching
    #
    images_cropped = histogram_matching_sequence(images_cropped[10], images_cropped)

    #
    # convert to 2D images
    #
    images_cropped = sequence_to_2d(images_cropped, SliceDirection.TRANSVERSAL)

    #
    # perform the motion analysis
    #
    displacements = perform_motion_analysis(images, mask) 

    return displacements



#################################################################################
def motion_analysis(transversals:list[CineImage], coronals:list[CineImage], sagittals:list[CineImage], 
                    mask_transversal:sitk.Image, mask_coronal:sitk.Image, mask_sagittal:sitk.Image, 
                    crop_boxes: np.array
                    ) -> tuple[np.array, np.array, np.array]:
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

    transversals_sitk, coronals_sitk, sagittals_sitk = prepare_images(transversals, coronals, sagittals, crop_boxes)

    displacements_transversal = motion_analysis_single_plane(transversals_sitk, mask_transversal) 
    displacements_coronal = motion_analysis_single_plane(coronals_sitk, mask_coronal) 
    displacements_sagittal = motion_analysis_single_plane(sagittals_sitk, mask_sagittal)

    displacements = [displacements_transversal, displacements_coronal, displacements_sagittal]

    return displacements

