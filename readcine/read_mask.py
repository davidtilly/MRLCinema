
import glob, os
import json

    

#############################################################################
def read_mask(filename):
    """ Read the mask file from the current directory

    :return: The mask file
    """
    with open(filename) as f:
        mask_json = json.load(f)

        mask_meta_data = mask_json['StructureMask']
        dim =[mask_meta_data['VoxelsAlongX'], mask_meta_data['VoxelsAlongY'], mask_meta_data['VoxelsAlongZ']]
        spacing = [float(x) for x in mask_meta_data['VoxelSize'].split(',')]
        origin = [float(x) for x in mask_meta_data['VolumePosition'].split(',')]
        row_dir = [float(x) for x in mask_meta_data['RowVector'].split(',')]
        col_dir = [float(x) for x in mask_meta_data['ColVector'].split(',')]

        mask_data_str = mask_meta_data['CompressedVoxels']
        
    return mask_data_str

 