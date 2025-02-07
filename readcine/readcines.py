
import glob
import os

import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import SimpleITK as sitk
from .parse_msnrbf import parse_msnrbf
from .distill_msrbf import distill_msnrbf
from .convert_to_sitk import convert_np_to_sitk, SliceDirection



def slice_direction(direction_cosines) -> list[int]:
    """ Converts the 2D direction cosines to 3D direction cosines

    :param direction_cosines: The two 3D direction cosines to 3D direction cosines
    """
    if np.allclose(direction_cosines, [1, 0, 0, 0, 1, 0]):
        return SliceDirection.TRANSVERSAL

    elif np.allclose(direction_cosines, [0, 1, 0, 0, 0, -1]):
        return SliceDirection.SAGITTAL

    elif np.allclose(direction_cosines, [1, 0, 0, 0, 0, -1]):
        return SliceDirection.CORONAL

    else:
        raise ValueError(f'Unknown direction cosines {direction_cosines}')


# def slice_direction(dim:np.array) -> SliceDirection:
#     """ Determines the slice direction based on the direction cosines

#     :param direction_cosines: 3D direction cosines
#     """
#     if dim[2] == 1:
#         return SliceDirection.TRANSVERSAL
    
#     if dim[0] == 1:
#         return SliceDirection.SAGITTAL
    
#     if dim[1] == 1:
#         return SliceDirection.CORONAL
    
#     raise ValueError(f'Unknown slice direction {dim}')
    

class CineImage(object):

    def __init__(self, image:sitk.Image, origin3d:np.array, spacing3d, direction:SliceDirection, timestamp:datetime):
        self.image = image
        self.origin3d = origin3d
        self.spacing3d = spacing3d
        self.timestamp = timestamp
        self.direction = direction

    def is_transverse(self):
        return self.direction == SliceDirection.TRANSVERSAL
    
    def is_coronal(self):
        return self.direction == SliceDirection.CORONAL
    
    def is_sagittal(self):
        return self.direction == SliceDirection.SAGITTAL
    
    #@property
    #def origin3d(self):
    #    return self.origin3d
    
    # @property
    # def low_xyz(self):
    #     pos_000 = self.image.TransformIndexToPhysicalPoint([0, 0, 0])
    #     pos_nnn = self.image.TransformIndexToPhysicalPoint([int(self.dim[0]-1), int(self.dim[1]-1), int(self.dim[2]-1)])
    #     return np.array([min(pos_000[0],pos_nnn[0]), min(pos_000[1],pos_nnn[1]), min(pos_000[2],pos_nnn[2])])


def readcines(directory) -> list[CineImage]:
    """ Reads a list of cine *.bin files and returns a list of sitk images wrapped into CineImage class

    :param directory: path to the cines to be read
    """
    images = [] 

    filenames = glob.glob(os.path.join(directory,'*.bin'))
    for i, filename in enumerate(filenames[:100]):
        
        # parse all records in the file and distill the relevant data
        records = parse_msnrbf(filename)
        distilled = distill_msnrbf(records)
        slice_data = distilled['TwoDSlicedata']

        if slice_data['PatientPosition']['value__'] != 3:
            #raise ValueError(f'Expected patient position 3, but got {slice_data['PatientPosition']['value__']}')
            raise ValueError('Expected patient position 3')
        
        #
        # Geomery of the image
        # 
        origin3d = np.array([slice_data['Origin']['X'], slice_data['Origin']['Y'], slice_data['Origin']['Z']])
        spacing = np.array([slice_data['VoxelSize']['XInmm'], slice_data['VoxelSize']['YInmm'], slice_data['VoxelSize']['ZInmm']])

        # Note! Spacing is not [x, y, z] as indicaded by the dictionary keys above, but follows the row/col direction
        # Here: for simplicity we take the minium of the spacing as spacing in all dirs
        # Not correct, but works since we have 2D images and intra-slice resolution is always the same in row and col-direction
        spacing3d = [slice_data['VoxelSize']['XInmm'], slice_data['VoxelSize']['YInmm'], slice_data['VoxelSize']['ZInmm']] 
        spacing3d = np.array(3 * [min(spacing)])

        nrow, ncol, nslices =[slice_data['Dimension']['Columns'], slice_data['Dimension']['Rows'], slice_data['Dimension']['Slices']] 

        if nslices > 1:
            raise ValueError(f'Expected only one slice, but got {nslices} slices')
        
        row_dir = slice_data['Orientation']['RowDirectionCosines']
        col_dir = slice_data['Orientation']['ColumnDirectionCosines'] 
        direction_cosines = np.array([row_dir['X'], row_dir['Y'], row_dir['Z'], col_dir['X'], col_dir['Y'], col_dir['Z']])
        direction = slice_direction(direction_cosines)

        pixel_data = np.array(distilled['TwoDSlicedata']['Data']).reshape([nrow, ncol, 2])
        pixel_data = pixel_data[:,:,1]

        image = convert_np_to_sitk(origin3d, spacing3d, nrow, ncol, direction, pixel_data)
        
        # time and date of the image
        timestamp_100ns = distilled['TwoDSlicedata']['Elapsed100NanosecondInterval']
        t0_utc = datetime(1900, 1, 1, 0, 0, 0, 0, tzinfo=ZoneInfo(key='UTC')) # in UTC
        t1_utc = t0_utc + timedelta(seconds=timestamp_100ns * 100 * 1e-9)
        t1_local = t1_utc.astimezone(ZoneInfo('Europe/Amsterdam'))

        images.append(CineImage(image, origin3d, spacing3d, direction, t1_local))
        
    return images

