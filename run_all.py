import os
import glob
import time
import json
import zoneinfo
import numpy as np
import datetime
from datetime import datetime

from MRLCinema.readcine.readcines import readcines_bin
from readcine.readcines_mha import readcines_mha
from MRLCinema.extract_motion import motion_analysis, resample_to_identity, filter_geometry
from MRLCinema.extract_motion import sort_cines_direction, prepare_masks, extract_times
from MRLCinema.report import create_report
from MRLCinema.patient_data import read_cine_patient_ID, find_cine_frame_of_reference
from MRLCinema.patient_data import find_structure_set, find_plan_from_frame_of_reference, prescription
from MRLCinema.motion_trace import MotionTrace

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



if __name__ == "__main__":
    """
    This script processes all the cine directories in the specified root path.
    It reads the patient information, extracts the motion from the cine data,
    and creates a report for each fraction.
    The report is saved in the patient's data directory.
    """
    
    patient_data_root= f'/mnt/P/TERAPI/MRLINAC/QA/RTQADATA/PATIENT_DATA'
    patient_data_root_archive = f'/mnt/P/TERAPI/MRLINAC/QA/RTQADATA/Patient_Data_Archive'

    cine_root_path = '/mnt/Q/MotionManagementData'
    cine_report_path = f'/mnt/P/TERAPI/MRLINAC/QA/RTQADATA/MotionManagement'

    cine_dirs = sorted(glob.glob(os.path.join(cine_root_path, '*')))
    cine_dirs = ['/mnt/Q/1.3.46.670589.11.79101.5.0.4376.2025040911534537010']

    # UddChr
    cine_dirs = ['1.3.46.670589.11.79101.5.0.15332.2025091710485204008',
                 '1.3.46.670589.11.79101.5.0.16488.2025092610550813006', # ja
                 '1.3.46.670589.11.79101.5.0.18008.2025092211221445006', # no rtplan found
                 '1.3.46.670589.11.79101.5.0.18008.2025092211453461008', # ja partially
                 '1.3.46.670589.11.79101.5.0.19204.2025091911473815008', # ja, men bara partially
                 '1.3.46.670589.11.79101.5.0.8980.2025092410150118006'] # ja
    
    
    # HT
    cine_dirs_ht = ['1.3.46.670589.11.79101.5.0.12792.2025112008441088002', 
                    '1.3.46.670589.11.79101.5.0.14876.2025111709111275004', 
                    '1.3.46.670589.11.79101.5.0.16128.2025111211230798004', 
                    '1.3.46.670589.11.79101.5.0.16128.2025111308524675016', 
                    '1.3.46.670589.11.79101.5.0.16756.2025111408533447002', 
                    '1.3.46.670589.11.79101.5.0.16944.2025112408451109002', 
                    '1.3.46.670589.11.79101.5.0.16944.2025112508440237014', 
                    '1.3.46.670589.11.79101.5.0.16944.2025112509514101016', 
                    '1.3.46.670589.11.79101.5.0.16944.2025112512480610020', 
                    '1.3.46.670589.11.79101.5.0.4044.2025111808465379002', 
                    '1.3.46.670589.11.79101.5.0.4044.2025111809591830004', 
                    '1.3.46.670589.11.79101.5.0.8136.2025112108440220002']

    # AR
    cine_dirs_ar = ['1.3.46.670589.11.79101.5.0.4376.2025040911534537010', '1.3.46.670589.11.79101.5.0.7672.2025041110262222004', '1.3.46.670589.11.79101.5.0.7672.2025041410391959012']

    cine_root_path = '/mnt/P/TERAPI/FYSIKER/David_Tilly/cine_conversion/HT'
    cine_dirs = cine_dirs_ht

    for cine_dir in cine_dirs:

        try: 
            print(f'START Processing {cine_dir}')
            start_time = time.time()

            #
            # Read patient information
            #
            patient_ID = read_cine_patient_ID(os.path.join('/mnt/Q/', cine_dir))
            if patient_ID is None:
                print(f'No patient ID found in {cine_dir}')
                continue
            if patient_ID.startswith('MRL'):
                print(f'Ignore patient ID {patient_ID} found in {cine_dir}')
                continue

            frame_of_ref = find_cine_frame_of_reference(os.path.join('/mnt/Q/', cine_dir))

            patient_path = find_patient_path(patient_ID, [patient_data_root, patient_data_root_archive])
            if patient_path is None:
                print(f'Patient {patient_ID} not found in data roots for {[patient_data_root, patient_data_root_archive]}')
                continue

            rtplan = find_plan_from_frame_of_reference(patient_path, frame_of_ref)
            if rtplan is None:
                print(f'No RT Plan found for {patient_ID} in {cine_dir}')
                continue

            prescribed_dose, number_of_fractions = prescription(rtplan)

            #
            # Read dictionary with sorted cine times and cine filenames
            #
            cine_filename_times_filename = os.path.join(cine_report_path, f'{patient_ID}_{rtplan.plan_name}_cine_times_filenames.json')
            cine_filename_times = {}
            if os.path.exists(cine_filename_times_filename):
                with open(cine_filename_times_filename, 'r') as f:
                    cine_filename_times = json.load(f)
            else:
                print(f'No cine filenames dictionary found for {patient_ID} in {cine_dir}, skipping.')
                continue

            #
            # Check if motion data was processed already. If so, go to next
            #
            report_filename = os.path.join(cine_report_path, f'{patient_ID}_{rtplan.plan_name}_cine_motion_analysis.json')
            #if os.path.exists(report_filename):
            #    print(f'Report already exists for {patient_ID} in {cine_dir}, skipping.')
            #    continue
            
            #
            # Read the structure set to setup masks
            #
            rtss = find_structure_set(patient_path, frame_of_ref)
            if rtss is None:
                print(f'No RTSS found for {patient_ID} in {cine_dir}')
                continue


            #
            # Read the cine data, handle them one batch at the time and stitch them together
            #
            masks, crop_boxes = None, None
            transversals_ref = [] 
            coronals_ref = [] 
            sagittals_ref = [] 
            num_tot_cines = len(cine_filename_times.keys())
            num_cines_analysed = 0
            num_images_per_batch = 500
            #times = cine_filename_times.keys()
            start = 0
            stop = min(start + num_images_per_batch, num_tot_cines)
            motion_trace = MotionTrace()

            while start < stop:

                #start = time.time()
                #cines = readcines(cine_directory, max_n=2000)
                current_cine_filenames = list(cine_filename_times.keys())[start:stop]
                current_cines = { filename: cine_filename_times[filename] for filename in current_cine_filenames } 
                #cines = readcines_bin(current_cines)
                cines = readcines_mha(current_cines)

                #
                # sort cines in directions
                #
                transversals, coronals, sagittals = sort_cines_direction(cines)

                #
                # preprocess images, filter out those with wrong geometry
                #
                transversals = filter_geometry(transversals, transversals_ref[0] if len(transversals_ref) > 0 else None)
                coronals = filter_geometry(coronals, coronals_ref[0] if len(coronals_ref) > 0 else None)
                sagittals = filter_geometry(sagittals, sagittals_ref[0] if len(sagittals_ref) > 0 else None)

                if len(transversals) == 0 or len(coronals) == 0 or len(sagittals) == 0:
                    print(f'No cines with matching geometry found in batch {start}-{stop} for {cine_dir}, skipping batch.')
                    start += num_images_per_batch
                    stop = min(start + num_images_per_batch, num_tot_cines)
                    continue

                #
                # Save the times
                #
                times_transversal = [cine.relative_time for cine in transversals]
                times_coronal = [cine.relative_time for cine in coronals]
                times_sagittal = [cine.relative_time for cine in sagittals]

                # append reference images to the current batch at the start 
                transversals = transversals_ref + transversals
                coronals = coronals_ref + coronals
                sagittals = sagittals_ref + sagittals
                
                # convert to indentity direction cosines and work only wit them from now on in this inner loop
                transversals_identity, coronals_identity, sagittals_identity = resample_to_identity(transversals, coronals, sagittals)

                #
                # create crop box and masks
                #
                if masks is None:
                   masks, crop_boxes = prepare_masks(transversals_identity[0], coronals_identity[0], sagittals_identity[0], rtss)
                
                #
                # Extract the motion
                #
                displacements = motion_analysis(transversals_identity, coronals_identity, sagittals_identity, masks[0], masks[1], masks[2], crop_boxes)
                motion_trace.add([times_transversal, times_coronal, times_sagittal], displacements)
                
                num_cines_analysed += len(cines)
                print(start, stop, num_cines_analysed, num_tot_cines)

                start += len(cines)
                stop = min(start + num_images_per_batch, num_tot_cines)

                if len(transversals_ref) == 0:
                    transversals_ref = transversals[0:10]
                if len(coronals_ref) == 0:
                   coronals_ref = coronals[0:10]
                if len(sagittals_ref) == 0:
                   sagittals_ref = sagittals[0:10]
                

            #
            # Create the report, write to fraction directory
            # { } []
            report = create_report(patient_ID, cine_dir, rtplan.plan_name, [prescribed_dose, number_of_fractions],
                                   motion_trace)
            
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=4)
                print(f'Wrote report to {report_filename}')
            
            print(f'END Processing {cine_dir}: {time.time()-start_time:.2f} seconds')
    
        except Exception as e:
            print(f'Error processing {cine_dir}: {e}')
            continue