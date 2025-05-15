
import SimpleITK as sitk
import numpy as np

#################################################################################
def group_registration_elastix(cines:list[sitk.Image], mask:sitk.Image, initial_transform_filename=None) -> tuple[sitk.Image, list[dict]]:
    """ Group registration of a sequence of images.
    Minimize the variation over sequence per pixel position.
    """

    #sitk.LogToConsoleOn()

    vector_of_images = sitk.VectorOfImage()
    vector_of_masks = sitk.VectorOfImage()

    for cine in cines:
        vector_of_images.push_back(cine)       
        vector_of_masks.push_back(mask)
    
    sequence_image = sitk.JoinSeries(vector_of_images)
    sequence_mask = sitk.JoinSeries(vector_of_masks)

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


