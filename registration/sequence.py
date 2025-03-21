
import numpy as np
import SimpleITK as sitk
from .single import rigid_registration, deformable_registration
from .fit_rigid_transform import fit_rigid_transform


def extract_rigid_displacement(transform:sitk.Transform, positions:list) -> np.array:
    """ Extract the displacement from a SimpleITK transform. """

    positions_t = np.array([np.array(transform.TransformPoint(pos)) for pos in positions])
    return fit_rigid_transform(positions, positions_t)


def cine_sequence_deformable_registration(cines:list, mask:sitk.Image, positions=list) -> list[tuple[sitk.Image, np.array]]:
    """ Register the cine sequence to extract the motion. 
    
    Use the first cine as the fixed image and register all other cines to this image.
    Extract the displacement by applying the transform to the list of positions.

    :param cines: List of cine images
    :param mask: Mask of the region of interest
    :param centre_position: Position used to determine the displacement.
    :return: List of registered images and the displacement of the centre position.
    """

    fixed = cines[0].image
    initial_transform = None
    results = []
    
    for moving in cines[1::]:
        
        registered_image, transform = deformable_registration(fixed.image, moving.image, mask, 
                                                              initial_transform=initial_transform)
        initial_transform = transform
        rigid_transform = extract_rigid_displacement(transform, positions)

        results.append([registered_image, rigid_transform])

    return results


def cine_sequence_rigid_registration(cines:list, mask:sitk.Image) -> list[tuple[sitk.Image, sitk.Transform]]:
    """ Rigidly register the cine sequence to extract the motion. 
    
    Use the first cine as the fixed image and register all other cines to this image.
    Extract the displacement of the centre position of the mask.

    :param cines: List of cine images
    :param mask: Mask of the region of interest
    :return: List of registered images and the displacement of the centre position.
    """

    fixed = cines[0]
    initial_transform = None
    results = []
    
    for moving in cines[1::]:
        
        registered_image, transform = rigid_registration(fixed.image, moving.image, mask, 
                                                         initial_transform=initial_transform)
        initial_transform = transform
        results.append([registered_image, transform])

    return results

