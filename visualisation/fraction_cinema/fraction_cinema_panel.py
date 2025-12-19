import panel as pn
import matplotlib.pyplot as plt
import SimpleITK as sitk

from MRLCinema.visualisation.fraction_cinema.business_logic import BusinessLogic
from MRLCinema.visualisation.fraction_cinema.plots import plot_motion_traces_empty, plot_motion_traces
from MRLCinema.visualisation.fraction_cinema.plots import plot_cines_empty, plot_cines 
from MRLCinema.visualisation.fraction_cinema.plots import plot_stats_empty, plot_stats

pn.extension('tabulator')
plt.style.use('dark_background')


#
# Header text - instructions
# 
header_text = """

Visualisation of motion traces and cines for a patient and plan.

Developed by Medical Physics, Uppsala University Hospital.
"""


#
# The business logic and data layer
#
the_model = BusinessLogic()


#
# Define GUI elements
#
# Patient and plan selection
button_read_patient_data = pn.widgets.Button(name="Read patients and motion traces", height=50, width=200, sizing_mode="fixed", button_type="primary")
patient_header = pn.pane.Markdown('## Patient')
select_patient = pn.widgets.Select(name='Select Patient', options=[])
select_plan = pn.widgets.Select(name='Select Plan', options=[])

row_patient = pn.Column(pn.layout.Divider(), 
                        patient_header, 
                        pn.Row(select_patient, select_plan), 
                        pn.layout.Divider())

# motion trace visualisation
slider_time_interval = pn.widgets.IntRangeSlider(name='Time Interval (index)', start=0, end=4000, step=1, value=(0,4000))
mpl_motion_traces = pn.pane.Matplotlib(plot_motion_traces_empty(), styles={"overflow":"auto"}, width=1200, tight=True)

# Cines controls and visualisation
slider_window_level = pn.widgets.IntRangeSlider(name='Window/Level', start=0, end=4000, step=25, value=(400,2600))
button_read_cines = pn.widgets.Button(name="Read cines", height=50, width=200, sizing_mode="fixed", button_type="primary")
config_time_fps = 4 # number of 'ticks' in the player per second.
cine_player = pn.widgets.Player(name='Player', start=0, end=100, value=0, step=1, interval=500, loop_policy='loop',
                                show_value=True, value_align='start', 
                                visible_buttons=["play", "pause"], show_loop_controls=False)
mpl_cines = pn.pane.Matplotlib(plot_cines_empty(), format='svg', styles={"overflow":"auto"}, width=1200, tight=True)

# Stats visualisation
mpl_stats = pn.pane.Matplotlib(plot_stats_empty(), styles={"overflow":"auto"}, width=1200, tight=True)


#
# Define GUI layout
#
template = pn.template.BootstrapTemplate(
    title="MRL Cinema",
    theme='dark'
)
template.main.append(pn.pane.Markdown(header_text))
template.main.append(button_read_patient_data)
template.main.append(row_patient)
template.main.append(pn.Column(slider_time_interval, mpl_motion_traces, pn.layout.Divider(), 
                               pn.Tabs(('Cines', pn.Column(pn.Row(cine_player, slider_window_level, button_read_cines), mpl_cines)), 
                                       ('Stats', mpl_stats)), 
                               pn.layout.Divider()))

#
# Define callback functions
#    
def clear_plots():
    plt.close(mpl_motion_traces.object)
    plot_motion_traces_empty(mpl_motion_traces.object)
    plt.close(mpl_cines.object)
    mpl_cines.object = plot_cines_empty(mpl_cines.object)
    plt.close(mpl_stats.object)
    mpl_stats.object = plot_stats_empty(mpl_stats.object)

def on_read_motion_traces(event):
    print('on_read_motion traces') 
    the_model.read_motion_traces()

    select_patient.options = the_model.patient_IDs
    if select_patient.options != []:
        select_patient.value = the_model.patient_IDs[0]
    
def on_patient_selected(event):
    clear_plots()
    print('on_patient_selected', event.new)
    the_model.current_patient_ID = event.new
    select_plan.options = the_model.current_patient_plan_names

def on_plan_selected(event):
    clear_plots()
    print('on_plan_selected', event.new)
    the_model.current_plan_label = event.new
    t_start = the_model.current_motion_trace.start_times()
    t_stop = the_model.current_motion_trace.end_times()
    slider_time_interval.start = int(t_start * config_time_fps)
    slider_time_interval.end = int(t_stop * config_time_fps)
    slider_time_interval.value = (slider_time_interval.start, slider_time_interval.end)
    mpl_motion_traces.object = plot_motion_traces(the_model.current_motion_trace, t_start, t_stop, t_start, mpl_motion_traces.object)
    mpl_stats.object = plot_stats(the_model.current_motion_trace, mpl_stats.object)

    mpl_cines.object = plot_cines_empty(mpl_cines.object)
    
def on_trace_time_interval_change(event):
    print('on_time_interval_change', event.new)
    t_start = event.new[0] / config_time_fps
    t_stop = event.new[1] / config_time_fps
    mpl_motion_traces.object = plot_motion_traces(the_model.current_motion_trace, t_start, t_stop, t_start, mpl_motion_traces.object)
    
    # remove cines if they were previously loaded
    mpl_cines.object = plot_cines_empty(mpl_cines.object)
    the_model.reset_cines()

def on_read_cines(event):
    t_start = slider_time_interval.value[0] / config_time_fps
    t_stop = slider_time_interval.value[1] / config_time_fps
    print('on_read_cines', t_start, t_stop)

    the_model.read_cines(t_start, t_stop)
    cine_player.start = slider_time_interval.value[0]
    cine_player.end = slider_time_interval.value[1]
    cine_player.value = slider_time_interval.value[0]
    time = slider_time_interval.value[0] / config_time_fps
    if the_model.current_cines != None:
        mpl_cines.object = plot_cines(the_model.current_cines, the_model.current_cine_times, the_model.current_cine_masks, 
                                      time, mpl_cines.object, v_min=slider_window_level.value[0], v_max=slider_window_level.value[1])  

def on_cine_window_level_change(event):
    print('on_window_level_change', event.new)
    time = cine_player.value / config_time_fps
    mpl_cines.object = plot_cines(the_model.current_cines, the_model.current_cine_times, the_model.current_cine_masks, 
                                  time, mpl_cines.object, v_min=slider_window_level.value[0], v_max=slider_window_level.value[1])  

def on_cine_time_change(event):
    print('on_time_selected', event.new)
    time = cine_player.value / config_time_fps
    t_start = slider_time_interval.value[0] / config_time_fps
    t_stop = slider_time_interval.value[1] / config_time_fps
    mpl_motion_traces.object = plot_motion_traces(the_model.current_motion_trace, t_start, t_stop, time, mpl_motion_traces.object)
    mpl_cines.object = plot_cines(the_model.current_cines, the_model.current_cine_times, the_model.current_cine_masks, 
                                  time, mpl_cines.object, v_min=slider_window_level.value[0], v_max=slider_window_level.value[1])  

#
# Add callbacks to GUI elements
#
button_read_patient_data.on_click(on_read_motion_traces)
select_patient.param.watch(on_patient_selected, 'value')
select_plan.param.watch(on_plan_selected, 'value')
slider_time_interval.param.watch(on_trace_time_interval_change, 'value')
button_read_cines.on_click(on_read_cines)
cine_player.param.watch(on_cine_time_change, 'value')
slider_window_level.param.watch(on_cine_window_level_change, 'value')


#
# Display GUI
#
template.servable(title='MRLCinema')
 




