

import numpy as np
import json

class MotionTrace():

    def __init__(self):
        self.patient_ID = None
        self.plan_label = None
        self.times_transversal = np.array([])
        self.times_coronal = np.array([])
        self.times_sagittal = np.array([])
        self.displacements_transversal = np.array([])
        self.displacements_coronal = np.array([])
        self.displacements_sagittal = np.array([])
        self.n_skip = 10

    @staticmethod 
    def from_file(filename:str):
        """ Load a motion trace from file. """
        with open(filename, 'r') as f:
            trace = json.load(f)
            motion_trace = MotionTrace()
            motion_trace.patient_ID = trace['PatientID']
            motion_trace.plan_label = trace['PlanLabel']
            motion_trace.times_transversal = np.array(trace['TimesTransversal'])
            motion_trace.displacements_transversal = np.array(list(zip(trace['DisplacementTransversalX'], trace['DisplacementTransversalY'])))
            motion_trace.times_coronal = np.array(trace['TimesCoronal'])
            motion_trace.displacements_coronal = np.array(list(zip(trace['DisplacementCoronalX'], trace['DisplacementCoronalZ'])))
            motion_trace.times_sagittal = np.array(trace['TimesSagittal'])
            motion_trace.displacements_sagittal = np.array(list(zip(trace['DisplacementSagittalY'], trace['DisplacementSagittalZ'])))
            return motion_trace
    
    @property
    def displacements_transversal_x(self) -> np.array:
        return self.displacements_transversal[:,0]
    
    @property
    def displacements_transversal_y(self) -> np.array:
        return self.displacements_transversal[:,1]
    
    @property
    def displacements_coronal_x(self) -> np.array:
        return self.displacements_coronal[:,0]
    
    @property
    def displacements_coronal_z(self) -> np.array:
        return self.displacements_coronal[:,1]
    
    @property
    def displacements_sagittal_y(self) -> np.array:
        return self.displacements_sagittal[:,0]
    
    @property
    def displacements_sagittal_z(self) -> np.array:
        return self.displacements_sagittal[:,1]

    def _is_transversal_empty(self) -> bool:
        return len(self.times_transversal) == 0
    
    def _is_coronal_empty(self) -> bool:
        return len(self.times_coronal) == 0
    
    def _is_sagittal_empty(self) -> bool:
        return len(self.times_sagittal) == 0
    
    def _is_empty(self) -> bool:
        return self._is_transversal_empty() and self._is_coronal_empty() and self._is_sagittal_empty()
    
    def start_times(self) -> float:
        if self._is_empty():
            raise ValueError('Motion trace is empty')

        times = []
        if not self._is_transversal_empty():
            times.append(self.times_transversal[0])
        if not self._is_coronal_empty():
            times.append(self.times_coronal[0])
        if not self._is_sagittal_empty():
            times.append(self.times_sagittal[0])
        
        return min(times)
    
    def end_times(self) -> float:
        if self._is_empty():
            raise ValueError('Motion trace is empty')

        times = []
        if not self._is_transversal_empty():
            times.append(self.times_transversal[-1])
        if not self._is_coronal_empty():
            times.append(self.times_coronal[-1])
        if not self._is_sagittal_empty():
            times.append(self.times_sagittal[-1])
        
        return max(times)

    def add_transversal(self, times:np.array, displacements:np.array):
        if self._is_transversal_empty():
            self.times_transversal = times.copy()
            self.displacements_transversal = displacements.copy()
        else:
            d_tranversal = displacements[self.n_skip:]
            self.displacements_transversal = np.concatenate((self.displacements_transversal, d_tranversal))
            self.times_transversal = np.concatenate((self.times_transversal, times))

    def add_coronal(self, times:np.array, displacements:np.array):
        if self._is_coronal_empty():
            self.times_coronal = times.copy()
            self.displacements_coronal = displacements.copy()
        else:
            d_coronal = displacements[self.n_skip:]
            self.displacements_coronal = np.concatenate((self.displacements_coronal, d_coronal))
            self.times_coronal = np.concatenate((self.times_coronal, times))

    def add_sagittal(self, times:np.array, displacements:np.array):
        if self._is_sagittal_empty():
            self.times_sagittal = times.copy()
            self.displacements_sagittal = displacements.copy()
        else:
            d_sagittal = displacements[self.n_skip:]
            self.displacements_sagittal = np.concatenate((self.displacements_sagittal, d_sagittal))
            self.times_sagittal = np.concatenate((self.times_sagittal, times))

    def add(self, times:np.array, displacements:np.array):
        self.add_transversal(times[0], displacements[0])
        self.add_coronal(times[1], displacements[1])
        self.add_sagittal(times[2], displacements[2])

