
import glob
import os
from enum import Enum
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import SimpleITK as sitk
from .parse_msnrbf import parse_msnrbf
from .distill_msrbf import distill_msnrbf
from .convert_to_sitk import convert_np_to_sitk, sitk_resample


class SliceDirection(Enum):
    TRANSVERSAL = 0
    CORONAL = 1
    SAGITTAL = 2


def direction_2d_to_3d(direction_cosines_2d) -> list[float]:
    """ Converts the 2D direction cosines to 3D direction cosines """

    if np.allclose(direction_cosines_2d, [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]):
        return (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    
    if np.allclose(direction_cosines_2d, [0.0, 1.0, 0.0, 0.0, 0.0, -1.0]):
        return [0.0, 0.0, -1.0, 1.0, 0.0, 0.0, 0.0, -1.0, 0.0]
    
    if np.allclose(direction_cosines_2d, [1.0, 0.0, 0.0, 0.0, 0.0, -1.0]):
        return [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0] 
    
    raise ValueError(f'Unknown direction cosines {direction_cosines_2d}')


def slice_direction(direction_cosines) -> list[int]:
    """ Converts the 2D direction cosines to 3D direction cosines

    :param direction_cosines: The two 3D direction cosines to 3D direction cosines
    """
    if np.allclose(direction_cosines, [1, 0, 0, 0, 1, 0]):
        return SliceDirection.TRANSVERSAL

    elif np.allclose(direction_cosines, [0, 1, 0, 0, 0, -1, ]):
        return SliceDirection.SAGITTAL

    elif np.allclose(direction_cosines, [1, 0, 0, 0, 0, -1]):
        return SliceDirection.CORONAL

    else:
        raise ValueError(f'Unknown direction cosines {direction_cosines}')



class CineImage(object):
    """ A class to store the cine image and mask with the corresponding geometry and timestamp."""

    def __init__(self, image:sitk.Image, mask:sitk.Image, direction:SliceDirection, timestamp:datetime):
        self.image = image
        self.mask = mask
        self.timestamp = timestamp
        self.direction = direction

    @property
    def origin3d(self):
        """ The origin of the image in 3D space. """
        return self.image.GetOrigin() 

    @property
    def spacing3d(self):
        """ The spacing of the image in 3D space. """
        return self.image.GetSpacing()    

    def is_transverse(self):
        return self.direction == SliceDirection.TRANSVERSAL
    
    def is_coronal(self):
        return self.direction == SliceDirection.CORONAL
    
    def is_sagittal(self):
        return self.direction == SliceDirection.SAGITTAL
    
    def low_xyz_position(self) -> np.array:
        """" Find the position of pixel with lowest x, y, z, position. """
        pos_000 = self.origin3d
        nrow, ncol, ndepth = self.image.GetSize()
        pos_nnn = self.image.TransformIndexToPhysicalPoint((nrow-1, ncol-1, ndepth-1))
        return np.array([min(pos_000[0],pos_nnn[0]), min(pos_000[1],pos_nnn[1]), min(pos_000[2],pos_nnn[2])])  


##########################################################################
def image_to_2d(image, slice_direction) -> sitk.Image:
    """ Convert a 3D image to a 2D image. """

    if slice_direction == SliceDirection.TRANSVERSAL:
        return image[:,:,0] 

    elif slice_direction == SliceDirection.SAGITTAL:
        return image[0,:,:]

    elif slice_direction == SliceDirection.CORONAL:
        return image[:,0,:]
    
    else:
        raise ValueError(f'Unknown slice direction {slice_direction}')


##########################################################################
def identity_direction_geometry(cine:CineImage) -> tuple:
    """ Determine the image ordersuing an identity direction cosines."""
    new_pos_000 = cine.low_xyz_position()
    identity_direction = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    new_size = [] 
    new_spacing = []

    if cine.direction == SliceDirection.TRANSVERSAL:
        new_size = cine.image.GetSize()
        new_spacing = cine.spacing3d
    
    elif cine.direction == SliceDirection.SAGITTAL:
        new_size = (cine.image.GetSize()[2], cine.image.GetSize()[0], cine.image.GetSize()[1])
        new_spacing = (cine.spacing3d[2], cine.spacing3d[0], cine.spacing3d[1])
    
    elif cine.direction == SliceDirection.CORONAL:
        new_size = (cine.image.GetSize()[0], cine.image.GetSize()[2], cine.image.GetSize()[1])
        new_spacing = (cine.spacing3d[0], cine.spacing3d[2], cine.spacing3d[1])
    
    return new_pos_000, new_spacing, new_size, identity_direction


def resample_cine_to_identity(cine:CineImage) -> CineImage:
    new_pos_000, new_spacing, new_size, identity_direction = identity_direction_geometry(cine)
    resampled_image = sitk_resample(cine.image, new_pos_000, new_spacing, new_size, identity_direction)
    resampled_mask = sitk_resample(cine.mask, new_pos_000, new_spacing, new_size, identity_direction)
    return CineImage(resampled_image, resampled_mask, cine.direction, cine.timestamp)


def read_single_cine(filename:str) -> CineImage:
    """ Parse all records in the file and distill the relevant data. """

    records = parse_msnrbf(filename)
    distilled = distill_msnrbf(records)
    slice_data = distilled['TwoDSlicedata']

    #
    # Geomery of the image
    # 
    origin3d = np.array([slice_data['Origin']['X'], slice_data['Origin']['Y'], slice_data['Origin']['Z']])

    # Note! Spacing is not [x, y, z] as indicaded by the dictionary keys above, but follows the row/col direction
    # Here: for simplicity we take the minium of the spacing as spacing in all dirs
    # Not correct, but works since we have 2D images and intra-slice resolution is always the same in row and col-direction
    spacing3d = [slice_data['VoxelSize']['XInmm'], slice_data['VoxelSize']['YInmm'], slice_data['VoxelSize']['ZInmm']] 
    
    nrow, ncol, nslices = [slice_data['Dimension']['Columns'], slice_data['Dimension']['Rows'], slice_data['Dimension']['Slices']] 

    if nslices > 1:
        raise ValueError(f'Expected only one slice, but got {nslices} slices')
    
    row_dir = slice_data['Orientation']['RowDirectionCosines']
    col_dir = slice_data['Orientation']['ColumnDirectionCosines'] 
    direction_cosines_2d = [row_dir['X'], row_dir['Y'], row_dir['Z'], col_dir['X'], col_dir['Y'], col_dir['Z']]
    direction_cosines_3d = direction_2d_to_3d(direction_cosines_2d)
    direction = slice_direction(direction_cosines_2d)

    # 
    # Image data, convert data from byte stream to 2D numpy array of int16 type
    #
    image_data_flat = np.frombuffer(bytes(distilled['TwoDSlicedata']['Data']), dtype=np.int16)
    image_data = image_data_flat.reshape([nslices, nrow, ncol])
    image = convert_np_to_sitk(origin3d, spacing3d, direction_cosines_3d, image_data)

    #
    # Mask, convert data from byte stream to 2D numpy array of int16 type
    #
    mask_data_flat = np.frombuffer(bytes(distilled['MMEMonitoringResult']['ResultStructures']['items'][0]['m_Item2']['Data']), np.int16)
    mask_data = mask_data_flat.reshape([nslices, nrow, ncol])
    mask = convert_np_to_sitk(origin3d, spacing3d, direction_cosines_3d, mask_data)
    
    # time and date of the image
    timestamp_100ns = distilled['TwoDSlicedata']['Elapsed100NanosecondInterval']
    t0_utc = datetime(1900, 1, 1, 0, 0, 0, 0, tzinfo=ZoneInfo(key='UTC')) # in UTC
    t1_utc = t0_utc + timedelta(seconds=timestamp_100ns * 100 * 1e-9)
    t1_local = t1_utc.astimezone(ZoneInfo('Europe/Amsterdam'))

    return CineImage(image, mask, direction, t1_local)


def readcines(directory, max_n=None) -> list[CineImage]:
    """ Reads a list of cine *.bin files and returns a list of sitk images wrapped into CineImage class

    :param directory: path to the cines to be read
    """
    cines = []
     
    filenames = glob.glob(os.path.join(directory,'*.bin'))
    N = len(filenames)
    if max_n != None:
        N = min(N, max_n)

    for filename in filenames[:N]:

        cine = read_single_cine(filename)
        cines.append(cine)
        
    return cines



