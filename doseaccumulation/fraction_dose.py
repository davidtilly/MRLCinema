
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
    
def cumulative_mu(logfile:Logfile) -> float:
    """ Get the cumulative MU at a given time from the logfile.
    
    :param logfile: The logfile object
    :param time: The time at which to get the cumulative MU
    :return: The cumulative MU at the given time
    """
    delta_mu = logfile.delta_mu
    cum_mu = np.cumsum(delta_mu)
    return cum_mu

def find_nearest_index(array, value):
    idx = (np.abs(array - value)).argmin()
    return idx

def dose_accumulation_sitk(nominal_dose:sitk.Image, times:np.array, motion_trace:np.array, logfile:Logfile, delta_time=5) -> sitk.Image:
    """ Accumulate the dose over the motion trace with the assumption 
    that the whole (scaled) dose distribution is delivered at each time point.

    The dose is integrated over the motion trace, the position of the CTV
    is taken at the midpoint of the time step.

    :param motion_trace : The displacements in the motion trace 
    :param times        : The time points corresponding to the motion trace displacements
    :param nominal_dose : The dose distribution in a statis patient.
    :param logfile      : The logfile with the MU and time information
    :return             : The accumulated dose distribution when accounting for the motion.
    """
    accumulated_dose = sitk.Image(nominal_dose.GetSize(), sitk.sitkFloat64)
    accumulated_dose.CopyInformation(nominal_dose)

    cum_mu = cumulative_mu(logfile)
    tot_mu = logfile.total_mu_header
    
    total_treatment_time = np.max(logfile.times)
    dt = delta_time
    mu_start = 0
    time_start = 0
    
    while time_start <= (total_treatment_time-dt):
        
        time_mid = time_start + 0.5*dt
        dx = np.interp(time_mid, times, motion_trace[:,0])
        dy = np.interp(time_mid, times, motion_trace[:,1])
        dz = np.interp(time_mid, times, motion_trace[:,2])

        # Resample the dose with the translation
        translation = sitk.TranslationTransform(3,[dx, dy, dz])  
        dose_now = sitk.Resample(nominal_dose, accumulated_dose, translation, sitk.sitkLinear, 0.0, nominal_dose.GetPixelID())        
        
        # Calculate the number of MU from the logfile
        index = find_nearest_index(logfile.times, time_start + dt)
        mu_end = cum_mu[index]
        delta_mu = mu_end - mu_start 
        dose_scaling = delta_mu / tot_mu

        # update the dose over the time step
        scaled_dose = dose_now * dose_scaling
        accumulated_dose += scaled_dose

        # prepare for next step
        mu_start = mu_end
        time_start += dt

    return accumulated_dose


def dose_accumulation(nominal_dose:np.array, pos_000:np.array, spacing:np.array, 
                      times:np.array, motion_trace:np.array, logfile:Logfile, delta_time=5) -> np.array:
    """ Accumulate the dose over the motion trace with the assumption 
    Wrapper function around accumlation function using sitk images.
    """
    nominal_dose_sitk = sitk.GetImageFromArray(np.swapaxes(nominal_dose, 0, 2))
    nominal_dose_sitk.SetOrigin(pos_000.tolist())
    nominal_dose_sitk.SetSpacing(spacing.tolist())

    accumulated_dose_sitk = dose_accumulation_sitk(nominal_dose_sitk, times, motion_trace, logfile, delta_time)

    accumulated_dose = np.swapaxes(sitk.GetArrayFromImage(accumulated_dose_sitk), 0, 2)        
    
    return accumulated_dose



