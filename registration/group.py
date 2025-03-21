
import SimpleITK as sitk
import numpy as np
from scipy.optimize import minimize
from ..readcine.readcines import CineImage

def calc_mean_image(images) -> sitk.Image:
    """ Create the mean image of a list of images. """

    mean_image = sitk.Image(images[0])
    for image in images[1:]:
        mean_image += image
    mean_image = mean_image / len(images)

    return mean_image

def parameters_to_translation_transforms(parameters, n=2) -> list[sitk.Transform]:
    """ Convert a list of parameters to a SimpleITK transform. """
    
    transforms = []
    for i in range(0, len(parameters), n):
        transform = sitk.TranslationTransform(2)
        transform.SetParameters(parameters[i:i+n])
        transforms.append(transform)

    return transforms

def objective_function_image(moving, fixed, mask) -> float:

    np_moving = sitk.GetArrayFromImage(moving)
    np_fixed = sitk.GetArrayFromImage(fixed)
    np_mask = sitk.GetArrayFromImage(mask)
    value  = np.square(np_moving[np_mask] - np_fixed[np_mask]).mean()    
    return value

def fun(x, *args):
    images, mask = args
    return objective_function(images, mask, x)

def objective_function(images, mask, transform_parameters) -> float:
    """Objective function for registration.

    Args:
        images: List of images to be registered.

    Returns:
        float: Value of the objective function.
    """
    
    transforms = parameters_to_translation_transforms(transform_parameters)
    moving_ts =[] 
    for trans, moving in zip(transforms, images):
        moving_ts.append(sitk.Resample(moving, moving, trans, sitk.sitkLinear, 0.0, moving.GetPixelID()))

    mean_image = calc_mean_image(moving_ts)

    obj_fun = 0
    for moving_t in moving_ts:
        obj_fun += objective_function_image(moving_t, mean_image, mask)

    obj_fun = obj_fun / len(images)

    return obj_fun
    
def group_registration(images, mask) -> list[sitk.Image]:
    """ Group registration of a sequence of images.
    Minimize the difference between the images and the mean of their transformed images.
    """

    num_images = len(images)
    parameters = [0] * 2 * num_images
    x0 = np.array(parameters)
    sitk_images = [image.image for image in images] 
    
    def callback(intermediate_result):
        print(f'fun: {intermediate_result.nit}, {intermediate_result.fun}')

    #res  = minimize(fun, x0, args=(sitk_images, mask), method='powell', callback=callback, options={'maxiter': 100})
    res  = minimize(fun, x0, args=(sitk_images, mask), method='CG', callback=callback, options={'maxiter': 100})

    transforms = parameters_to_translation_transforms(res.x)
    return transforms



def group_registration_elastix(images:list[CineImage], mask:sitk.Image, initial_transform_filename=None) -> tuple[sitk.Image, list[dict]]:
    """ Group registration of a sequence of images.
    Minimize the difference between the images and the mean of their transformed images.
    """

    #sitk.LogToConsoleOn()

    vector_of_images = sitk.VectorOfImage()
    vector_of_masks = sitk.VectorOfImage()
    
    for image in images:
        vector_of_images.push_back(image)
        vector_of_masks.push_back(mask)
    
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

    #parameter_map = sitk.GetDefaultParameterMap('groupwise')
    parameter_map['NumberOfResolutions'] = '2'
    parameter_map['Transform'] = ['TranslationStackTransform']
    parameter_map['Metric'] = ['VarianceOverLastDimensionMetric']
    #parameter_map['MaximumNumberOfIterations'] = ['999'] 

    if initial_transform_filename != None:
        elastixImageFilter.SetInitialTransformParameterFileName(initial_transform_filename)
        parameter_map['NumberOfSubTransforms'] = str(len(images))  
    
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
