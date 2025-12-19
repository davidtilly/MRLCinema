from pathlib import PureWindowsPath, PurePosixPath, Path
from datetime import datetime, timedelta
import csv
import numpy as np
import SimpleITK as sitk
from readcine.readcines import CineImage, SliceDirection

def slice_direction_3d(direction_cosines_3d) -> CineImage:
    """ Converts the 3D direction cosines to SliceDirection enum

    :param direction_cosines: The two 3D direction cosines to 3D direction cosines
    """
    if np.allclose(direction_cosines_3d, [1, 0, 0, 0, 1, 0, 0, 0, 1]):
        return SliceDirection.TRANSVERSAL

    elif np.allclose(direction_cosines_3d, [0, 0, -1, 1, 0, 0, 0, -1, 0]):
        return SliceDirection.SAGITTAL
                                            
    elif np.allclose(direction_cosines_3d, [1, 0, 0, 0, 0, 1, 0, -1, 0]):
        return SliceDirection.CORONAL
    
    else:
        raise ValueError(f'Unknown direction cosines {direction_cosines_3d}')

#########################################################################
def read_single_cine_mha(filename:str, time:datetime) -> CineImage:
    image = sitk.ReadImage(filename)
    direction = slice_direction_3d(image.GetDirection())
    mask = None
    cine = CineImage(image, mask, direction, time)
    cine._dir = direction

    return cine

#########################################################################
def readcines_mha(cine_filename_times:list[dict], max_n=None) -> list[CineImage]:
    """ Reads a list of cine *.mha files and returns a list of sitk images wrapped into CineImage class

    :param directory: dictionary with filenames and timestamps
    """
    cines = []
     
    N = len(cine_filename_times.keys())
    if max_n != None:
        N = min(N, max_n)

    for key in list(cine_filename_times.keys())[:N]:
        value = cine_filename_times[key]
        time_str = value['cine_timestamp'] # ": "2025-11-21 08:30:31.224119",
        time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S.%f')
        cine = read_single_cine_mha(key, time)
        cine.relative_time = value['relative_cine_time']
        cines.append(cine)
        
    return cines



#summary_filename = Path('/mnt/P/TERAPI/FYSIKER/David_Tilly/cine_conversion/1.3.46.670589.11.79101.5.0.14876.2025111712350029010/TwoDImages/BinFileDump.txt')
def read_cines_mha(directory:Path, max_n=None) -> list[CineImage]:

    summary_filename = Path(directory) / 'TwoDImages' / 'BinFileDump.txt'

    cines = []
    with open(summary_filename, newline='') as csvfile:

        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        headings = next(reader)

        for row in reader:

            #
            # read image
            #
            proton_bin_filename = PureWindowsPath(','.join(row[-2:]))
            win_parts = proton_bin_filename.parts
            linux_path = PurePosixPath('directo', *win_parts[4:])

            proton_mha_filename = str(linux_path).replace('.protobin', '.mha')
            #print(proton_bin_filename, proton_mha_filename)
            
            image = sitk.ReadImage(proton_mha_filename)
            direction = slice_direction_3d(image.GetDirection())

            #
            # Decipher timestamp
            #
            time_stamp_str = row[-3]
            time_stamp_str = time_stamp_str.lstrip()
            time_str = time_stamp_str[:19]

            time_obj = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S')
            
            parts_s = time_stamp_str[20:-2]
            delta_ms = timedelta(microseconds=int(parts_s))
            time_obj += delta_ms

            mask = None
            cine = CineImage(image, mask, direction, time_obj)
            cine._dir = direction
            cines.append(cine)

            if (max_n != None) and len(cines) >= max_n:
                break   
    
    return cines    

        