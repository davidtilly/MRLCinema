from U2Dose.dicomio.rtstruct import RtStruct
from U2Dose.dicomio.rtplan import RtPlan
import pydicom
import glob, os
import json

#############################################################################
def prescription_ds(ds:pydicom.Dataset) -> tuple[int, float]:
    """ Extract the prescription from the RT plan. """
    
    prescription_dose = float(ds.DoseReferenceSequence[0].TargetPrescriptionDose)
    number_of_fractions = int(ds.FractionGroupSequence[0].NumberOfFractionsPlanned)
    
    return number_of_fractions, prescription_dose

def prescription(rtplan:RtPlan) -> tuple[int, float]:
    """ Extract the prescription from the RT plan. """
    
    return prescription_ds(rtplan._ds)

#############################################################################
def rtss_frame_of_reference_ds(ds:pydicom.Dataset) -> str:
    return ds.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID

def rtss_frame_of_reference(rtss:RtStruct) -> str:
    return rtss_frame_of_reference_ds(rtss._ds)

#############################################################################
def read_cine_patient_ID(path) -> str:
    """ Read the patient ID from the current directory

    :return: The patient ID
    """
    mask_filenames = glob.glob(os.path.join(path, 'BinaryMasks', 'Z_MM*.json'))

    if len(mask_filenames) == 0:
        dir = os.path.join(path, 'BinaryMasks')
        raise FileNotFoundError(f'No mask files found in the dir {dir}')

    mask_filename = mask_filenames[0]
    with open(mask_filename) as f:
        mask_file = json.load(f)
        return mask_file['PatientMRN']

#############################################################################
def find_cine_frame_of_reference(path) -> str:
    """ Read the frame of reference from the session
    """
    mask_filenames = glob.glob(os.path.join(path, 'BinaryMasks', 'Z_MM*.json'))

    if len(mask_filenames) == 0:
        dir = os.path.join(path, 'BinaryMasks')
        raise FileNotFoundError(f'No mask files found in the dir {dir}')

    mask_filename = mask_filenames[0]
    with open(mask_filename) as f:
        mask_file = json.load(f)
        return mask_file['FrameOfReferenceUid']

############################################################################
def find_structure_set(patient_path:str, frame_of_reference:str) -> RtStruct|None:
    """ Find the RT structure set for a given patient ID and frame of reference."""

    rtss_filenames = glob.glob(os.path.join(patient_path, '*', 'RS*.dcm'))

    rtss = None 
    for filename in rtss_filenames:
        rtss_ds = pydicom.dcmread(filename)
        
        if rtss_ds.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID == frame_of_reference:
            rtss = RtStruct(filename)
            rtss.parse()
            return rtss
        
    return None

############################################################################
def find_plan_from_frame_of_reference(patient_data_path:str, frame_of_reference:str) -> RtPlan|None:
    """ Find the RT plan for a given patient based on the FoR."""

    rtplan_filenames = glob.glob(os.path.join(patient_data_path, '*', 'RP*.dcm'))
    
    rtplan = None
    for filename in rtplan_filenames:
        rtplan_ds = pydicom.dcmread(filename)
    
        if rtplan_ds.FrameOfReferenceUID == frame_of_reference:
            rtplan = RtPlan(filename)
            rtplan.parse()
            return rtplan
    
    return None
############################################################################