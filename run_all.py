import os
import glob
import time
import json

from MRLCinema.readcine.readcines import readcines
from MRLCinema.extract_motion import extract_motion
from MRLCinema.report import create_report
from MRLCinema.patient_data import read_cine_patient_ID, find_cine_frame_of_reference
from MRLCinema.patient_data import find_structure_set, find_plan_from_frame_of_reference, prescription


if __name__ == "__main__":
    """
    This script processes all the cine directories in the specified root path.
    It reads the patient information, extracts the motion from the cine data,
    and creates a report for each fraction.
    The report is saved in the patient's data directory.
    """
    
    patient_data_root= f'/mnt/P/TERAPI/MRLINAC/QA/RTQADATA/PATIENT_DATA'
    cine_root_path = '/media/david/Elements/MotionManagementData'

    cine_dirs = sorted(glob.glob(os.path.join(cine_root_path, '*')))

    for cine_dir in cine_dirs:

        try: 
            print(f'START Processing {cine_dir}')
            start_time = time.time()

            #
            # Read patient information
            #
            patient_ID = read_cine_patient_ID(cine_dir)
            if patient_ID is None:
                print(f'No patient ID found in {cine_dir}')
                continue
            if patient_ID.startswith('MRL'):
                print(f'Ignore patient ID {patient_ID} found in {cine_dir}')
                continue

            frame_of_ref = find_cine_frame_of_reference(cine_dir)
            rtss = find_structure_set(patient_data_root, patient_ID, frame_of_ref)

            if rtss is None:
                print(f'No RTSS found for {patient_ID} in {cine_dir}')
                continue

            rtplan = find_plan_from_frame_of_reference(patient_data_root, patient_ID, frame_of_ref)
            if rtplan is None:
                print(f'No RT Plan found for {patient_ID} in {cine_dir}')
                continue

            prescribed_dose, number_of_fractions = prescription(rtplan)

            #
            # Read the cine data
            #
            cine_directory = os.path.join(cine_dir, 'TwoDImages')
            #start = time.time()
            cines = readcines(cine_directory, max_n=2000)

            #
            # Extract the motion
            #
            displacements, times = extract_motion(cines, rtss)

            #
            # Create the report, write to fraction directory
            # { } []
            report = create_report(patient_ID, cine_dir, rtplan.plan_name, [prescribed_dose, number_of_fractions], times, displacements)
            report_dir = os.path.join(patient_data_root, patient_ID, rtplan.plan_name)
            report_filename = os.path.join(report_dir, f'{patient_ID}_{rtplan.plan_name}_cine_motion_analysis.json')
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=4)
                print(f'Wrote report to {report_filename}')
            
            print(f'END Processing {cine_dir}: {time.time()-start_time:.2f} seconds')
    
        except Exception as e:
            print(f'Error processing {cine_dir}: {e}')
            continue