import panel as pn
import matplotlib.pyplot as plt
import SimpleITK as sitk

from MRLCinema.visualisation.fraction_cinema.business_logic import BusinessLogic

pn.extension('tabulator')
plt.style.use('dark_background')


#
# Header text - instructions
# 
header_text = """# Fraction cinema

Visualisation of motion traces and cines for a patient and plan.

Developed by Medical Physics, Uppsala University Hospital.
"""

def plot_motion_traces_empty(fig=None):
    """ Create an empty matplotlib figure for motion analysis statistics. """
    if fig is None:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 5))
    
    (ax1, ax2, ax3) = fig.get_axes()

    for ax in (ax1, ax2, ax3):
        ax.clear()
        ax.set_ylim(-10, 10)
        ax.set_title('Motion Analysis Statistics')
        ax.set_ylabel('Displacement (mm)')

    ax3.set_xlabel('Time (s)')
    fig.tight_layout()
    
    return fig

def plot_cines_empty(fig=None):
    """ Create an empty matplotlib figure for cines. """
    if fig is None:
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 4))
    
    (ax1, ax2, ax3) = fig.get_axes()

    for ax in (ax1, ax2, ax3):
        ax.clear()

    fig.tight_layout()
    
    return fig

def plot_motion_traces(motion_trace, time, fig):
     
    ax1, ax2, ax3 = fig.get_axes()
    for ax in (ax1, ax2, ax3):
        ax.clear()
    
    ax1.set_ylabel('X (mm)')
    ax2.set_ylabel('Y (mm)')
    ax3.set_ylabel('Z (mm)')
        
    ax1.set_title('Motion Traces')
    ax3.set_xlabel('Time (s)')
    
    ax1.plot(motion_trace['TimesTransversal'], motion_trace['DisplacementTransversalX'], label='Transversal', color='C0')
    ax1.plot(motion_trace['TimesCoronal'], motion_trace['DisplacementCoronalX'], label='Coronal', color='C1')
    ax2.plot(motion_trace['TimesTransversal'], motion_trace['DisplacementTransversalY'], label='Transversal', color='C0')
    ax2.plot(motion_trace['TimesSagittal'], motion_trace['DisplacementSagittalY'], label='Sagittal', color='C2')
    ax3.plot(motion_trace['TimesSagittal'], motion_trace['DisplacementSagittalZ'], label='Sagittal', color='C2')
    ax3.plot(motion_trace['TimesCoronal'], motion_trace['DisplacementCoronalZ'], label='Coronal', color='C1')
    for ax in (ax1, ax2, ax3):
        ax.legend(loc='upper left')
        ax.grid(True)
        ax.plot([time, time],[-5, 5], label=f'Time {time}', color='white')

    return fig

def plot_cines(cines, cine_times, cine_masks, time, fig):
    """ Plot the cines for the given time (or closest to). """
    ax1, ax2, ax3 = fig.get_axes()
    
    for ax in (ax1, ax2, ax3):
        ax.clear()
        ax.set_axis_off()
    
    [transversals, sagittal, coronal] = cines
    [t_transversal, t_sagittal, t_coronal] = cine_times
    [mask_transversal, mask_sagittal, mask_coronal] = cine_masks
    
    # Plot the cines closest in time in each direction
    time_index = min(range(len(t_transversal)), key=lambda i: abs(t_transversal[i] - time))
    ax1.imshow(sitk.GetArrayFromImage(transversals[time_index]), cmap='gray', origin='lower', vmin=0, vmax=2048)
    ax1.contour(sitk.GetArrayFromImage(mask_transversal), [0.5], colors='red')
    ax1.set_title(f'Transversal {t_transversal[time_index]:.2f} s')

    time_index = min(range(len(t_sagittal)), key=lambda i: abs(t_sagittal[i] - time))
    ax2.imshow(sitk.GetArrayFromImage(sagittal[time_index]), cmap='gray', origin='lower', vmin=0, vmax=2048)
    ax2.contour(sitk.GetArrayFromImage(mask_sagittal), [0.5], colors='red')
    ax2.set_title(f'Sagittal {t_sagittal[time_index]:.2f} s')

    time_index = min(range(len(t_coronal)), key=lambda i: abs(t_coronal[i] - time))
    ax3.imshow(sitk.GetArrayFromImage(coronal[time_index]), cmap='gray', origin='lower', vmin=0, vmax=2048)
    ax3.contour(sitk.GetArrayFromImage(mask_coronal), [0.5], colors='red')
    ax3.set_title(f'Coronal {t_coronal[time_index]:.2f} s')
    
    return fig


#
# The business logic and data layer
#
the_model = BusinessLogic()


#
# Define GUI elements
#
# Patient and plan selection
button_read_data = pn.widgets.Button(name="Read patients and motion traces", height=50, width=200, sizing_mode="fixed", button_type="primary")
patient_header = pn.pane.Markdown('## Patient')
select_patient = pn.widgets.Select(name='Select Patient', options=[])
select_plan = pn.widgets.Select(name='Select Plan', options=[])
button_read_cines = pn.widgets.Button(name="Read cines", height=50, width=200, sizing_mode="fixed", button_type="primary")
row_patient = pn.Column(pn.layout.Divider(), patient_header, pn.Row(select_patient, select_plan, button_read_cines), pn.layout.Divider())

# matplotlib plots
time_slider = pn.widgets.IntSlider(name='Time', start=0, end=100, step=1, value=0)
mpl_motion_traces = pn.pane.Matplotlib(plot_motion_traces_empty(), styles={"overflow":"auto"}, width=1200, tight=True)
mpl_cines = pn.pane.Matplotlib(plot_cines_empty(), format='svg', styles={"overflow":"auto"}, width=800, tight=True)


#
# Define GUI layout
#
template = pn.template.BootstrapTemplate(
    title="MRL Cinema",
    theme='dark'
)
template.main.append(pn.pane.Markdown(header_text))
template.main.append(button_read_data)
template.main.append(row_patient)
template.main.append(pn.Column(time_slider, mpl_cines, mpl_motion_traces, pn.layout.Divider()))

#
# Define callback functions
#    
def clear_plots():
    plt.close(mpl_motion_traces.object)
    plot_motion_traces_empty(mpl_motion_traces.object)
    plt.close(mpl_cines.object)
    mpl_cines.object = plot_cines_empty(mpl_cines.object)

def on_read_motion_traces(event):
    print('on_read_motion traces') 
    the_model.read_motion_traces()

    select_patient.options = the_model.patient_IDs
    if select_patient.options != []:
        select_patient.value = the_model.patient_IDs[0]
    
def on_patient_selected(event):
    print('on_patient_selected', event.new)
    the_model.current_patient_ID = event.new
    select_plan.options = the_model.current_patient_plan_names
    clear_plots()

def on_plan_selected(event):
    print('on_plan_selected', event.new)
    the_model.current_plan_label = event.new
    time_slider.start = the_model.current_motion_trace['TimesTransversal'][0]
    time_slider.value = time_slider.start
    time_slider.end = the_model.current_motion_trace['TimesTransversal'][-1] 
    mpl_motion_traces.object = plot_motion_traces(the_model.current_motion_trace, time_slider.value, mpl_motion_traces.object)
    mpl_cines.object = plot_cines_empty(mpl_cines.object)

def on_read_cines(event):
    the_model.read_cines()
    if the_model.current_cines != None:
        mpl_cines.object = plot_cines(the_model.current_cines, the_model.current_cine_times, the_model.current_cine_masks, time_slider.value, mpl_cines.object)

def on_time_change(event):
    print('on_time_selected', event.new)
    mpl_motion_traces.object = plot_motion_traces(the_model.current_motion_trace, time_slider.value, mpl_motion_traces.object)
    mpl_cines.object = plot_cines(the_model.current_cines, the_model.current_cine_times, the_model.current_cine_masks, time_slider.value, mpl_cines.object)


#
# Add callbacks to GUI elements
#
button_read_data.on_click(on_read_motion_traces)
select_patient.param.watch(on_patient_selected, 'value')
select_plan.param.watch(on_plan_selected, 'value')
button_read_cines.on_click(on_read_cines)
time_slider.param.watch(on_time_change, 'value')


#
# Display GUI
#
template.servable(title='MRLCinema')
 




