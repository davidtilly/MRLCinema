
import numpy as np


def range_percentile(displacements, percentile=0.95):
    """ Calculate the range of the displacements for the given images and masks.
    First take the abs value of the displacements, then cakculate the percentile in each direction
    """
    sorted_displacements = np.sort(displacements)
    return np.percentile(sorted_displacements, 2.5), np.percentile(sorted_displacements, 97.5)


def motion_statistics(displacements_transversal, displacements_sagittal, displacements_coronal, percentile=0.95):
    """ Calculate the motion statistics for the given images and masks.
    First take the abs value of the displacements, then cakculate the percentile in each direction
    
    Transversal and sagittal provides x displacement
    Sagittal provides y and z displacement
    Coronal provides x and z displacement

    The functions maximum of the percentiles per direction
    """
    x_transversal = np.abs(displacements_transversal[:,0])
    y_transversal = np.abs(displacements_transversal[:,1])
    x_transversal_p = np.percentile(x_transversal, percentile*100)
    y_transversal_p = np.percentile(y_transversal, percentile*100)

    y_sagittal = np.abs(displacements_sagittal[:,0])
    z_sagittal = np.abs(displacements_sagittal[:,1])
    y_sagittal_p = np.percentile(y_sagittal, percentile*100)
    z_sagittal_p = np.percentile(z_sagittal, percentile*100)

    x_coronal = np.abs(displacements_coronal[:,0])
    z_coronal = np.abs(displacements_coronal[:,1])
    x_coronal_p = np.percentile(x_coronal, percentile*100)
    z_coronal_p = np.percentile(z_coronal, percentile*100)

    return max(x_transversal_p, x_coronal_p), max(y_transversal_p, y_sagittal_p), max(z_sagittal_p, z_coronal_p)
