import os
import socket
import json
import glob
from pathlib import Path

from datetime import datetime, timedelta
from MRLCinema.readcine.readcines import readcines
from MRLCinema.extract_motion import prepare_motion_analysis
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
plan_path = '/home/david/RTQADATA/PATIENT_DATA'
cine_path = '/mnt/Q'
mm_data_path = '/home/david/RTQADATA/MotionManagement'


#
# Help functions to read and search for patients and plans
#
def find_patient_plan_labels(motion_traces:dict, patient_ID:str) -> list[str]:
    plan_labels = []
    for k, _ in motion_traces.items():
        if k[0] == patient_ID:
            plan_labels.append(k[1])
    return plan_labels

def read_rtss(patient_ID, plan_label): 
    """ Read the RT Structure Set for a given patient ID and plan label. """
    rtss_filenames = glob.glob(os.path.join(plan_path, patient_ID, plan_label, 'RS*.dcm'))
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

    
    def read_motion_traces(self):
        """ Read available motion traces. Save patient IDs. """
        trace_filenames = glob.glob(os.path.join(mm_data_path, '*.json'))
        patient_IDs = set()
        for filename in trace_filenames:
            trace = json.load(open(filename, 'r'))
            self._motion_traces[(trace['PatientID'], trace['PlanLabel'])] = trace
            patient_IDs.add(trace['PatientID'])

        self._patient_IDs = sorted(list(patient_IDs))

    def read_cines(self):
        """ Read the cines for the current patient and plan. """
        path = ''

        if os.path.basename(self._current_motion_trace["CinePath"]) == 'TwoDImages':
            tmp = Path(self._current_motion_trace["CinePath"])
            path = os.path.join(cine_path, tmp.parent, 'TwoDImages')
        else:
            path = os.path.join(cine_path, os.path.basename(self._current_motion_trace["CinePath"]), 'TwoDImages')
        
        if not os.path.exists(path):
            return
        
        cines = readcines(path, max_n=1000)
        rtss = read_rtss(self._current_patient_ID, self._current_plan_label)
        self._current_cines, self._current_cine_times, self._current_cine_masks = prepare_motion_analysis(cines, rtss)

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
    