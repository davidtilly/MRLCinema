
import json
import numpy as np


def create_report(patient_ID:str, cine_path:str, plan_label:str, prescription:tuple, times:tuple, displacements:tuple) -> dict:
    """ Create a report for the given patient ID and cine path corresponding to a given RT Plan.
    
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
    report['FractionDose'] = prescription

    report['TimesTransversal'] = list(times_transversal)
    report['DisplacementTransversalX'] = displacements_transversal[:,0].tolist()
    report['DisplacementTransversalY'] = displacements_transversal[:,1].tolist()  

    report['TimesSagittal'] = list(times_sagittal)
    report['DisplacementSagittalY'] = displacements_sagittal[:,0].tolist()
    report['DisplacementSagittalZ'] = displacements_sagittal[:,1].tolist()
    
    report['TimesCoronal'] = list(times_coronal)
    report['DisplacementCoronalX'] = displacements_coronal[:,0].tolist()
    report['DisplacementCoronalZ'] = displacements_coronal[:,1].tolist()

    report['version'] = '1.0' 

    return report