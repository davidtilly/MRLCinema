
import SimpleITK as sitk
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from MRLCinema.motion_trace import MotionTrace

def plot_motion_traces_empty(fig=None):
    """ Create an empty matplotlib figure for motion analysis statistics. """
    if fig is None:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(40/2.54, 12/2.54))
    
    (ax1, ax2, ax3) = fig.get_axes()

    for ax in (ax1, ax2, ax3):
        ax.clear()
        ax.set_ylim(-10, 10)
        
        ax.set_ylabel('Displacement (mm)')

    ax1.set_title('Motion Analysis')
    ax3.set_xlabel('Time (s)')
    fig.tight_layout()
    
    return fig


def plot_cines_empty(fig=None):
    """ Create an empty matplotlib figure for cines. """
    if fig is None:
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(40/2.54, 12/2.54))
    
    (ax1, ax2, ax3) = fig.get_axes()

    for ax in (ax1, ax2, ax3):
        ax.clear()
        ax.set_axis_off()
        custom_lines = [Line2D([0], [0], color='red', lw=2, ls='dotted')]
        ax.legend(custom_lines, ['Z_MM'])

    ax1.set_title('Transversal')
    ax2.set_title('Sagittal')
    ax3.set_title('Coronal')

    fig.tight_layout()
    
    return fig


def plot_stats_empty(fig=None):
    """ Empty plot the motion analysis statistics. """
    if fig is None:
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(40/2.54, 12/2.54))
    
    (ax1, ax2, ax3) = fig.get_axes()

    for ax in (ax1, ax2, ax3):
        ax.clear()
        ax.set_xlabel('Displacement (mm)')

    ax1.set_title('X')
    ax2.set_title('Y')
    ax3.set_title('Z')
    
    fig.tight_layout()
    
    return fig


def plot_motion_traces(motion_trace:MotionTrace, time_start, time_end, time_now, fig):
    """ Plot the motion traces with a vertical line at the given time. """

    ax1, ax2, ax3 = fig.get_axes()
    for ax in (ax1, ax2, ax3):
        ax.clear()
    
    ax1.set_ylabel('X (mm)')
    ax2.set_ylabel('Y (mm)')
    ax3.set_ylabel('Z (mm)')
        
    ax1.set_title('Motion Traces')
    ax3.set_xlabel('Time (s)')
    
    ax1.plot(motion_trace.times_transversal, motion_trace.displacements_transversal_x, label='Transversal', color='C0')
    ax1.plot(motion_trace.times_coronal, motion_trace.displacements_coronal_x, label='Coronal', color='C1')
    ax2.plot(motion_trace.times_transversal, motion_trace.displacements_transversal_y, label='Transversal', color='C0')
    ax2.plot(motion_trace.times_sagittal, motion_trace.displacements_sagittal_y, label='Sagittal', color='C2')
    ax3.plot(motion_trace.times_sagittal, motion_trace.displacements_sagittal_z, label='Sagittal', color='C2')
    ax3.plot(motion_trace.times_coronal, motion_trace.displacements_coronal_z, label='Coronal', color='C1')
    for ax in (ax1, ax2, ax3):
        ax.legend(loc='upper left')
        ax.grid(True)
        ax.plot([time_now, time_now],[-5, 5], label=f'Time {time_now}', color='white')
        ax.set_xlim(time_start, time_end)

    return fig


def plot_cines(cines, cine_times, cine_masks, time, fig, v_min=0, v_max=2048):
    """ Plot the cines for the given time (or closest to). 
    Window level can be adjusted with v_min and v_max.
    """
    
    if cines is None: return None
    if cine_masks is None: return None
    if cine_times is None: return None
    if fig is None: return None  

    ax1, ax2, ax3 = fig.get_axes()
    
    for ax in (ax1, ax2, ax3):
        ax.clear()
        ax.set_axis_off()
    
    [transversals, sagittal, coronal] = cines
    [t_transversal, t_sagittal, t_coronal] = cine_times
    [mask_transversal, mask_sagittal, mask_coronal] = cine_masks
    

    # Plot the cines closest in time in each direction
    time_index = min(range(len(t_transversal)), key=lambda i: abs(t_transversal[i] - time))
    ax1.imshow(sitk.GetArrayFromImage(transversals[time_index]), cmap='gray', origin='lower', vmin=v_min, vmax=v_max)
    ax1.contour(sitk.GetArrayFromImage(mask_transversal), [0.5], colors='red', linestyles='dotted')
    ax1.set_title(f'Transversal {t_transversal[time_index]:.2f} s')

    time_index = min(range(len(t_sagittal)), key=lambda i: abs(t_sagittal[i] - time))
    ax2.imshow(sitk.GetArrayFromImage(sagittal[time_index]), cmap='gray', origin='lower', vmin=v_min, vmax=v_max)
    ax2.contour(sitk.GetArrayFromImage(mask_sagittal), [0.5], colors='red', linestyles='dotted')
    ax2.set_title(f'Sagittal {t_sagittal[time_index]:.2f} s')

    time_index = min(range(len(t_coronal)), key=lambda i: abs(t_coronal[i] - time))
    ax3.imshow(sitk.GetArrayFromImage(coronal[time_index]), cmap='gray', origin='lower', vmin=v_min, vmax=v_max)
    ax3.contour(sitk.GetArrayFromImage(mask_coronal), [0.5], colors='red', linestyles='dotted')
    ax3.set_title(f'Coronal {t_coronal[time_index]:.2f} s')

    for ax in (ax1, ax2, ax3):
        custom_lines = [Line2D([0], [0], color='red', lw=2, ls='dotted')]
        ax.legend(custom_lines, ['Z_MM'])
    
    return fig


def displacement_statistics_1d(translations:np.array, q:float=0.975) -> list:
    """ Return the q and (1-q) percentiles of a 1D array of translations. """
    qq = 100*q
    return[np.percentile(translations, qq), np.percentile(translations, 100-qq)]


def trace_amplitude(trace:MotionTrace):
    """ Return the min and max of a motion trace dictionary. """
    amp_x = max(np.abs(trace.displacements_transversal_x).max(), np.abs(trace.displacements_coronal_x).max())
    amp_y = max(np.abs(trace.displacements_transversal_y).max(), np.abs(trace.displacements_sagittal_y).max())
    amp_z = max(np.abs(trace.displacements_sagittal_z).max(), np.abs(trace.displacements_coronal_z).max())
    return (amp_x, amp_y, amp_z)
    

def plot_stats(motion_trace:MotionTrace, fig):
    """ Empty plot the motion analysis statistics. """
    if fig is None:
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(40/2.54, 12/2.54))
    
    (ax1, ax2, ax3) = fig.get_axes()

    for ax in (ax1, ax2, ax3):
        ax.clear()

    (amp_x, amp_y, amp_z) = trace_amplitude(motion_trace)
    bin_edge_x = int(amp_x + 1.)
    bin_edge_y = int(amp_y + 1.)
    bin_edge_z = int(amp_z + 1.) 
    bins_x = np.arange(-bin_edge_x, bin_edge_x + 0.1, 0.5)
    bins_y = np.arange(-bin_edge_y, bin_edge_y + 0.1, 0.5)
    bins_z = np.arange(-bin_edge_z, bin_edge_z + 0.1, 0.5)

    interval_trans_x = displacement_statistics_1d(motion_trace.displacements_transversal_x, q=0.975)
    interval_cor_x = displacement_statistics_1d(motion_trace.displacements_coronal_x, q=0.975)
    interval_trans_y = displacement_statistics_1d(motion_trace.displacements_transversal_y, q=0.975)
    interval_sag_y = displacement_statistics_1d(motion_trace.displacements_sagittal_y, q=0.975)
    interval_sag_z = displacement_statistics_1d(motion_trace.displacements_sagittal_z, q=0.975)
    interval_cor_z = displacement_statistics_1d(motion_trace.displacements_coronal_z, q=0.975)

    ax1.hist(motion_trace.displacements_transversal_x, bins=bins_x, label=F'Transversal, 95% [{interval_trans_x[1]:.2f}, {interval_trans_x[0]:.2f}]', color='C0')
    ax1.hist(motion_trace.displacements_coronal_x, bins=bins_x, label=F'Coronal, 95% [{interval_cor_x[1]:.2f}, {interval_cor_x[0]:.2f}]', color='C1')
    ax2.hist(motion_trace.displacements_transversal_y, bins=bins_y, label=F'Transversal, 95% [{interval_trans_y[1]:.2f}, {interval_trans_y[0]:.2f}]', color='C0')
    ax2.hist(motion_trace.displacements_sagittal_y, bins=bins_y, label=F'Sagittal, 95% [{interval_sag_y[1]:.2f}, {interval_sag_y[0]:.2f}]', color='C2')
    ax3.hist(motion_trace.displacements_sagittal_z, bins=bins_z, label=F'Sagittal, 95% [{interval_sag_z[1]:.2f}, {interval_sag_z[0]:.2f}]', color='C2')
    ax3.hist(motion_trace.displacements_coronal_z, bins=bins_z, label=F'Coronal, 95% [{interval_cor_z[1]:.2f}, {interval_cor_z[0]:.2f}]', color='C1')
    ax1.set_title('X')
    ax2.set_title('Y')
    ax3.set_title('Z')

    for ax in (ax1, ax2, ax3):
        ax.legend()
        ax.set_xlabel('Displacement (mm)')

    fig.suptitle('Motion Analysis Statistics')
    fig.tight_layout()
    
    return fig


