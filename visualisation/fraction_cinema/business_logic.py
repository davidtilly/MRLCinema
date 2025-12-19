import os
import json
import glob
from pathlib import Path

from MRLCinema.readcine.readcines import readcines
from MRLCinema.visualisation.fraction_cinema.prepare_motion_visualisation import prepare_motion_visualisation
from MRLCinema.motion_trace import MotionTrace
from U2Dose.dicomio.rtstruct import RtStruct

#
# Configuration
# # 
# if os.name == 'nt':
#     config_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts', 'data_config_win.ini')
#     os.system(r"net use P: \\10.194.4.157\asfdoc Asfcon018 /persistent:yes /user:uas-asf\Asfcon")
# elif os.name == 'posix' and socket.gethostname() == 'david-VM':
#     config_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts', 'data_config_linux_david.ini')
# else:
#     config_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts', 'data_config.ini')

# with open(config_filename, 'r') as config_file:
#     config = json.load(config_file)

# where to search for logfiles
# logfile_path = config['logfile_path']

# where to write data
cine_path = '/mnt/Q'
mm_data_path = '/mnt/Q/MotionManagementData'

patient_data_root= f'/mnt/P/TERAPI/MRLINAC/QA/RTQADATA/PATIENT_DATA'
patient_data_root_archive = f'/mnt/P/TERAPI/MRLINAC/QA/RTQADATA/Patient_Data_Archive'
cine_report_path = f'/mnt/P/TERAPI/MRLINAC/QA/RTQADATA/MotionManagement'


#
# Help functions to read and search for patients and plans
#
def find_patient_path(patient_ID:str, paths:str) -> str|None:
    """ Check if the patient exists in the archive directory.

    :param patient_ID: The patient ID to check
    :param paths: The root directories to search for the patient
    :return: Path to the patient directory if the patient exists in any of the paths, None otherwise
    """
    for path in paths:
        patient_dirs = glob.glob(os.path.join(path, patient_ID, '*'))
        if  len(patient_dirs) > 0:
            return os.path.join(path, patient_ID)

    return None

def find_patient_plan_labels(motion_traces:dict, patient_ID:str) -> list[str]:
    plan_labels = []
    for k, _ in motion_traces.items():
        if k[0] == patient_ID:
            plan_labels.append(k[1])
    return plan_labels

def read_rtss(patient_path, plan_label): 
    """ Read the RT Structure Set for a given patient ID and plan label. """
    rtss_filenames = glob.glob(os.path.join(patient_path, plan_label, 'RS*.dcm'))
    if len(rtss_filenames) == 0:
        return None
    rtss = RtStruct(rtss_filenames[0])
    rtss.parse()
    return rtss

######################################################################################################################
class BusinessLogic(object):
    """ Class to handle the business logic of the logfile analysis. """

    def __init__(self):
        
        self._current_patient_ID = None
        self._current_plan_label = None
        
        self._patient_IDs = [] 
        self._current_patient_plan_names = None

        self._motion_traces = {}
        self._current_motion_trace = None

        self._current_cines = None
        self._current_cine_times = None
        self._current_cine_masks = None

    def reset_cines(self):
        self._current_cines, self._current_cine_times, self._current_cine_masks = None, None, None
    
    def read_motion_traces(self):
        """ Read available motion traces. Save patient IDs. """
        trace_filenames = glob.glob(os.path.join(cine_report_path, '*cine_motion_analysis.json'))
        patient_IDs = set()
        for filename in trace_filenames:
            trace = MotionTrace.from_file(filename)
            self._motion_traces[(trace.patient_ID, trace.plan_label)] = trace
            patient_IDs.add(trace.patient_ID)

        self._patient_IDs = sorted(list(patient_IDs))
    
    def read_cines(self, t_start:float, t_stop:float):
        """ Read the cines for the current patient and plan that lie within the given time interval (sec)."""

        # first read all times and filenames to extract only files in the time interval
        cine_times_filenames_dict_filename = os.path.join(cine_report_path, f'{self._current_patient_ID}_{self._current_plan_label}_cine_times_filenames.json')
        if os.path.exists(cine_times_filenames_dict_filename):
            with open(cine_times_filenames_dict_filename, 'r') as f:
                
                cine_times_filenames_dict = json.load(f)
                
                # filter times within t_start and t_stop
                for filename, value in list(cine_times_filenames_dict.items()):
                    relative_time = value['relative_cine_time'] 
                    if (relative_time < t_start) or (relative_time > t_stop):
                        cine_times_filenames_dict.pop(filename)
                                        
                cines = readcines(cine_times_filenames_dict, 1500)

                patient_path = find_patient_path(self._current_patient_ID, [patient_data_root, patient_data_root_archive])
                if patient_path is None:
                    return
                rtss = read_rtss(patient_path, self._current_plan_label)        
                self._current_cines, self._current_cine_times, self._current_cine_masks = prepare_motion_visualisation(cines, rtss)
                
    @property
    def current_patient_ID(self): 
        return self._current_patient_ID

    @current_patient_ID.setter
    def current_patient_ID(self, patient_ID):
        self._current_patient_ID = patient_ID
        self._current_patient_plan_names = find_patient_plan_labels(self._motion_traces, patient_ID)
        self.current_plan_label = None
        self._current_cines = None
        self._current_cine_times = None
        self._current_cine_masks = None

    @property
    def patient_IDs(self):
        return self._patient_IDs
        
    @property
    def current_plan_label(self):
        return self._current_plan_label

    @current_plan_label.setter
    def current_plan_label(self, plan_name:str):
        self._current_plan_label = plan_name
        self._current_motion_trace = self._motion_traces.get((self._current_patient_ID, plan_name))
        self._current_cines = None
        self._current_cine_times = None
        self._current_cine_masks = None

    @property
    def current_patient_plan_names(self):
        return self._current_patient_plan_names
    
    @property
    def current_motion_trace(self) -> dict:
        return self._current_motion_trace
    
    @property
    def current_cines(self):
        return self._current_cines
    
    @property
    def current_cine_times(self):
        return self._current_cine_times
    
    @property
    def current_cine_masks(self):
        return self._current_cine_masks  
    