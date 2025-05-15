
import json
import numpy as np


def create_report(patient_ID:str, cine_path:str, plan_label:str, times:tuple, displacements:tuple) -> dict:
    """ Create a report for the given patient ID and cine path.
    
    :param patient_ID   : The patient ID
    :param cine_path    : The path to the cine images
    :param plan_label   : The label of the RT Plan
    :param times        : The times of the cine images
    :param displacements: The displacements of the images
    """

    [displacements_transversal, displacements_sagittal, displacements_coronal] = displacements
    [times_transversal, times_sagittal, times_coronal] = times
    
    report = {}
    
    report['PatientID'] = patient_ID
    report['CinePath'] = cine_path
    report['PlanLabel'] = plan_label

    report['Times Transversal'] = list(times_transversal)
    report['Displacement Transversal X'] = displacements_transversal[:,0].tolist()
    report['Displacement Transversal Y'] = displacements_transversal[:,1].tolist()  

    report['Times Sagittal'] = list(times_sagittal)
    report['Displacement Sagittal Y'] = displacements_sagittal[:,0].tolist()
    report['Displacement Sagittal Z'] = displacements_sagittal[:,1].tolist()
    
    report['Times Coronal'] = list(times_coronal)
    report['Displacement Coronal X'] = displacements_coronal[:,0].tolist()
    report['Displacement Coronal Z'] = displacements_coronal[:,1].tolist()

    return report