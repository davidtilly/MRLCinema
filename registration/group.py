
import SimpleITK as sitk
import numpy as np
from scipy.optimize import minimize
from ..readcine.readcines import CineImage, image_to_2d, SliceDirection



#################################################################################
def group_registration_elastix(cines:list[CineImage], mask:sitk.Image, slice_direction:SliceDirection, initial_transform_filename=None) -> tuple[sitk.Image, list[dict]]:
    """ Group registration of a sequence of images.
    Minimize the difference between the images and the mean of their transformed images.
    """

    #sitk.LogToConsoleOn()

    vector_of_images = sitk.VectorOfImage()
    vector_of_masks = sitk.VectorOfImage()

    mask_2d = image_to_2d(mask, slice_direction)

    for cine in cines:
        image_2d = image_to_2d(cine, slice_direction)
        vector_of_images.push_back(image_2d)       
        vector_of_masks.push_back(mask_2d)
    
    sequence_image = sitk.JoinSeries(vector_of_images)
    sequence_mask = sitk.JoinSeries(vector_of_masks)

    print('image info', sequence_image.GetOrigin(), sequence_image.GetSpacing(), sequence_image.GetSize(), sequence_image.GetPixelID(), sequence_image.GetDirection())
    print('mask info', sequence_mask.GetOrigin(), sequence_mask.GetSpacing(), sequence_mask.GetSize(), sequence_mask.GetPixelID(), sequence_mask.GetDirection())

    elastixImageFilter = sitk.ElastixImageFilter()
    elastixImageFilter.SetFixedImage(sequence_image)
    elastixImageFilter.SetMovingImage(sequence_image)
    elastixImageFilter.SetFixedMask(sequence_mask)
    elastixImageFilter.SetMovingMask(sequence_mask)

    elastixImageFilter.LogToConsoleOn()
    parameter_map = sitk.GetDefaultParameterMap('translation')

    parameter_map = sitk.GetDefaultParameterMap('groupwise')
    parameter_map['NumberOfResolutions'] = '1'
    parameter_map['Transform'] = ['TranslationStackTransform']
    parameter_map['Metric'] = ['VarianceOverLastDimensionMetric']
    #parameter_map['MaximumNumberOfIterations'] = ['999'] 

    if initial_transform_filename != None:
        elastixImageFilter.SetInitialTransformParameterFileName(initial_transform_filename)
        parameter_map['NumberOfSubTransforms'] = str(len(cines))  
    
    print()
    print('start parameter map')
    print(sitk.PrintParameterMap(parameter_map))
    print('end parameter map')
    print()

    elastixImageFilter.SetParameterMap(parameter_map)
    elastixImageFilter.Execute()

    resultImage = elastixImageFilter.GetResultImage()
    transformParameterMap = elastixImageFilter.GetTransformParameterMap()
    
    return resultImage, transformParameterMap


