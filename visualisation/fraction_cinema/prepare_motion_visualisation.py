
import numpy as np
import SimpleITK as sitk

from ...readcine.readcines import CineImage, SliceDirection, resample_cine_to_identity 
from ...registration.create_mask import create_grid
from ...registration.preprocessing import crop_sequence, crop_image, find_crop_box, sequence_to_2d, image_to_2d
from ...extract_motion import sort_cines_direction, filter_geometry
from ...readcine.convert_to_sitk import sitk_resample_mask_to_slice
from U2Dose.patient.Roi import Roi
from U2Dose.dicomio.rtstruct import RtStruct



#################################################################################
def prepare_motion_visualisation(cines:list[CineImage], rtss:RtStruct):
    """ Prepare the cines for subsequent motion analysis. """""

    #
    # Sort cines in time and then split into directions
    #
    cines = sorted(cines, key=lambda cine: cine.timestamp)
    transversals, coronals, sagittals = sort_cines_direction(cines)
    
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

    mask_transversal = sitk_resample_mask_to_slice(z_mm, transversals[0].image)
    mask_sagittal = sitk_resample_mask_to_slice(z_mm, sagittals[0].image)
    mask_coronal = sitk_resample_mask_to_slice(z_mm, coronals[0].image)


    # 
    # Prepocessoing by cropping (image and mask) 
    #
    crop_box = find_crop_box(mask_transversal, m=50)
    transversals_cropped = crop_sequence(transversals, crop_box)
    mask_transversal_cropped = crop_image(mask_transversal, crop_box)
    mask_transversal_cropped = sitk.Cast(mask_transversal_cropped, sitk.sitkUInt8)

    crop_box = find_crop_box(mask_sagittal, m=50)
    sagittals_cropped = crop_sequence(sagittals, crop_box)
    mask_sagittal_cropped = crop_image(mask_sagittal, crop_box)
    mask_sagittal_cropped = sitk.Cast(mask_sagittal_cropped, sitk.sitkUInt8)
    
    crop_box = find_crop_box(mask_coronal, m=50)
    coronals_cropped = crop_sequence(coronals, crop_box)
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
    t_transversal = [cine.relative_time for cine in transversals] 
    t_sagittal = [cine.relative_time for cine in sagittals]
    t_coronal = [cine.relative_time for cine in coronals] 

    prepared_cines = [transversals_cropped, sagittals_cropped, coronals_cropped]
    times = [t_transversal, t_sagittal, t_coronal] 
    masks = [mask_transversal_cropped, mask_sagittal_cropped, mask_coronal_cropped]

    return prepared_cines, times, masks