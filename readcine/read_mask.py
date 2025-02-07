
import glob, os
import json

# read patient ID
def read_patient_ID(path):
    """ Read the patient ID from the current directory

    :return: The patient ID
    """
    mask_filename = glob.glob(os.path.join(path, 'BinaryMasks', 'Z_MM*.json'))
    mask_filename = mask_filename[0]
    with open(mask_filename) as f:
        mask_file = json.load(f)
        return mask_file['PatientMRN']
    

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

 