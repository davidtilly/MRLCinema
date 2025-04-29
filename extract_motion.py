

import numpy as np
import SimpleITK as sitk
from .readcine.readcines import readcines, SliceDirection, resample_cine_to_identity 
from .registration.create_mask import create_registration_mask, create_grid
from .registration.crop import crop_sequence, crop_image, find_crop_box
from .registration.group import group_registration_elastix
from .motion_statistics import motion_statistics, parameter_map_to_displacements
from U2Dose.patient.Roi import Roi
from U2Dose.dicomio.rtstruct import RtStruct


def extract_motion(cine_directory:str, rtss:RtStruct, max_n=1500):

    #
    # Read all cines in directory, sort in time and then split into directions
    #
    cines = readcines(cine_directory, max_n=max_n)

    time_sorted_cines = sorted(cines, key=lambda cine: cine.timestamp)

    time_sorted_transversal = list(filter(lambda cine: cine.direction == SliceDirection.TRANSVERSAL, time_sorted_cines))
    time_sorted_coronal = list(filter(lambda cine: cine.direction == SliceDirection.CORONAL, time_sorted_cines))
    time_sorted_sagittal = list(filter(lambda cine: cine.direction == SliceDirection.SAGITTAL, time_sorted_cines))
    time_sorted_transversal =[ resample_cine_to_identity(cine) for cine in time_sorted_transversal]
    time_sorted_coronal =[ resample_cine_to_identity(cine) for cine in time_sorted_coronal]
    time_sorted_sagittal =[ resample_cine_to_identity(cine) for cine in time_sorted_sagittal] 

    #
    # Create the grid for the mask
    #
    grid = create_grid(time_sorted_transversal[0], time_sorted_coronal[0], time_sorted_sagittal[0])
    z_mm = Roi.from_rtstruct(rtss, name='Z_MM', grid=grid)

    mask_transversal = create_registration_mask(z_mm, time_sorted_transversal[0])
    mask_sagittal = create_registration_mask(z_mm, time_sorted_sagittal[0])
    mask_coronal = create_registration_mask(z_mm, time_sorted_coronal[0])

    # 
    # Crop mask and images in sequence
    #
    crop_box = find_crop_box(mask_transversal, m=30)
    cines_transversal_cropped = crop_sequence(time_sorted_transversal, crop_box)
    mask_transversal_cropped = crop_image(mask_transversal, crop_box)
    mask_transversal_cropped = sitk.Cast(mask_transversal_cropped, sitk.sitkUInt8)

    crop_box = find_crop_box(mask_sagittal, m=30)
    cines_sagittal_cropped = crop_sequence(time_sorted_sagittal, crop_box)
    mask_sagittal_cropped = crop_image(mask_sagittal, crop_box)
    mask_sagittal_cropped = sitk.Cast(mask_sagittal_cropped, sitk.sitkUInt8)

    crop_box = find_crop_box(mask_coronal, m=30)
    cines_coronal_cropped = crop_sequence(time_sorted_coronal, crop_box)
    mask_coronal_cropped = crop_image(mask_coronal, crop_box)
    mask_coronal_cropped = sitk.Cast(mask_coronal_cropped, sitk.sitkUInt8)

    # 
    # perform the registrations
    #
    resultImage, transformParameterMap_transversal = group_registration_elastix(cines_transversal_cropped, mask_transversal_cropped, time_sorted_transversal[0].direction) 
    resultImage, transformParameterMap_sagittal = group_registration_elastix(cines_sagittal_cropped, mask_sagittal_cropped, time_sorted_sagittal[0].direction)
    resultImage, transformParameterMap_coronal = group_registration_elastix(cines_coronal_cropped, mask_coronal_cropped, time_sorted_coronal[0].direction)


    #
    # distill the motion into statistic
    #
    displacements_transversal = parameter_map_to_displacements(transformParameterMap_transversal[0], reset_first=True)
    displacements_sagittal = parameter_map_to_displacements(transformParameterMap_sagittal[0], reset_first=True)
    displacements_coronal = parameter_map_to_displacements(transformParameterMap_coronal[0], reset_first=True)

    x_p, y_p, z_p = motion_statistics(displacements_transversal, displacements_sagittal, displacements_coronal, percentile=0.98)

    return x_p, y_p, z_p