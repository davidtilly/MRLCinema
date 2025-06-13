
import SimpleITK as sitk
import numpy as np
from QAckis.Logfiles.Logfile import Logfile


def displacement_at_time(motion_report:dict, time:float) -> tuple:
    """ Get the displacement at a given time from the motion report.
    Ata given time, the 2D displacement in each cine direcftion is accessed.
    The average displacement is calculated.
    
    :param motion_report: The motion report dictionary
    :param time: The time at which to get the displacement
    :return: A tuple with the displacements in x, y, z direction
    """
    times = motion_report['TimesTransversal']
    idx = np.searchsorted(times, time)
    idx = max(0, idx - 1)  # Ensure idx is not negative
    idx = min(idx, len(times) - 1)  # Ensure idx is within bounds
    t_dx = motion_report['DisplacementTransversalX'][idx]
    t_dy = motion_report['DisplacementTransversalY'][idx]

    times = motion_report['TimesSagittal']
    idx = np.searchsorted(times, time)
    idx = max(0, idx - 1)  # Ensure idx is not negative
    idx = min(idx, len(times) - 1)  # Ensure idx is within bounds
    s_dy = motion_report['DisplacementSagittalY'][idx]
    s_dz = motion_report['DisplacementSagittalZ'][idx]

    times = motion_report['TimesCoronal']
    idx = np.searchsorted(times, time)
    idx = max(0, idx - 1)  # Ensure idx is not negative 
    idx = min(idx, len(times) - 1)  # Ensure idx is within bounds
    c_dx = motion_report['DisplacementCoronalX'][idx]
    c_dz = motion_report['DisplacementCoronalZ'][idx]

    # Combine the displacements
    dx = 0.5 * (t_dx + c_dx)
    dy = 0.5 * (t_dy + s_dy)
    dz = 0.5 * (s_dz + c_dz)
    
    return (dx, dy, dz)
    

def dose_accumulation(motion_report:dict, nominal_dose:sitk.Image, logfile:Logfile):
    """ Accumulate the dose over the motion trace with the assumption 
    that the whole (scaled) dose distribution is delivered at each time point.

    The dose is integrated over the motion trace, the position of the CTV
    is taken at the midpoint of the time step.
    """
    accumulated_dose = sitk.Image.CopyInformation(nominal_dose)
    tot_mu = logfile.total_mu()
    
    total_treatment_time = np.max(logfile.times)
    dt = 5
    mu_start = 0

    while time < (total_treatment_time-0.5*dt):
        
        dx, dy, dz = displacement_at_time(motion_report, time + 0.5*dt)

        # Resample the dose with the translation
        translation = sitk.TranslationTransform(dimension=3)
        translation.SetParameters([dx, dy, dz])
        dose_time = sitk.Resample(nominal_dose, accumulated_dose, translation, sitk.sitkLinear, 0.0, nominal_dose.GetPixelID())        
        
        # Calculate the number of MU from the logfile
        mu_end = logfile.mu(time)
        delta_mu = mu_end - mu_start 
        dose_scaling = delta_mu / tot_mu

        # update the dose over the time step
        accumulated_dose += dose_scaling * dose_time

        # prepare for next step
        mu_start = mu_end
        time += dt

    return accumulated_dose


