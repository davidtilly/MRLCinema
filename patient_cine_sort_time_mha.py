import csv
import os
import glob
from pathlib import PureWindowsPath, PurePosixPath, Path
import time
import json
import numpy as np
from datetime import datetime, timedelta

from MRLCinema.readcine.readcines import read_single_cine
from MRLCinema.patient_data import read_cine_patient_ID, find_cine_frame_of_reference
from MRLCinema.patient_data import find_plan_from_frame_of_reference

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
    
    # HT (protobin)
    cine_dirs_ht = ['1.3.46.670589.11.79101.5.0.12792.2025112008441088002', '1.3.46.670589.11.79101.5.0.14876.2025111709111275004', '1.3.46.670589.11.79101.5.0.16128.2025111211230798004', '1.3.46.670589.11.79101.5.0.16128.2025111308524675016', '1.3.46.670589.11.79101.5.0.16756.2025111408533447002', '1.3.46.670589.11.79101.5.0.16944.2025112408451109002', '1.3.46.670589.11.79101.5.0.16944.2025112508440237014', '1.3.46.670589.11.79101.5.0.16944.2025112509514101016', '1.3.46.670589.11.79101.5.0.16944.2025112512480610020', '1.3.46.670589.11.79101.5.0.4044.2025111808465379002', '1.3.46.670589.11.79101.5.0.4044.2025111809591830004', '1.3.46.670589.11.79101.5.0.8136.2025112108440220002']
    #cine_dirs_ht = ['1.3.46.670589.11.79101.5.0.16128.2025111211230798004']
    
    cine_mha_path = '/mnt/P/TERAPI/FYSIKER/David_Tilly/cine_conversion/HT'
    cine_root_path = '/mnt/Q'

    cine_dirs = cine_dirs_ht

    
    for cine_dir in cine_dirs:

        try: 
            print(f'START Processing {cine_dir}')
            start_time = time.time()

            #
            # Read patient information
            #
            patient_ID = read_cine_patient_ID(os.path.join(cine_root_path, cine_dir))
            if patient_ID is None:
                print(f'No patient ID found in {cine_dir}')
                continue
            if patient_ID.startswith('MRL'):
                print(f'Ignore patient ID {patient_ID} found in {cine_dir}')
                continue

            frame_of_ref = find_cine_frame_of_reference(os.path.join(cine_root_path, cine_dir))
            patient_path = find_patient_path(patient_ID, [patient_data_root, patient_data_root_archive])
            if patient_path is None:
                print(f'Patient {patient_ID} not found in data roots for {[patient_data_root, patient_data_root_archive]}')
                continue

            rtplan = find_plan_from_frame_of_reference(patient_path, frame_of_ref)
            if rtplan is None:
                print(f'No RT Plan found for {patient_ID} in {cine_dir}')
                continue


            #
            # Read the conversion file and store the filename with their timestamps
            #
            cine_mha_path_dir = os.path.join(cine_mha_path, cine_dir,'TwoDImages')
            cine_conversion_filename = os.path.join(cine_mha_path_dir, 'BinFileDump.txt')

            cine_filename_times = {}
            
            with open(cine_conversion_filename, newline='') as csvfile:

                reader = csv.reader(csvfile, delimiter=',', quotechar='|')
                headings = next(reader)

                for row in reader:

                    # Decipher timestamp
                    time_stamp_str = row[-3]
                    time_stamp_str = time_stamp_str.lstrip()
                    time_str = time_stamp_str[:19]
                    time_obj = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S')
                    
                    parts_s = time_stamp_str[20:-2]
                    delta_ms = timedelta(microseconds=int(parts_s))
                    time_obj += delta_ms

                    if time_obj.year < 2018:
                        continue
                    
                    proton_bin_filename = PureWindowsPath(','.join(row[-2:]))
                    win_parts = proton_bin_filename.parts
                    linux_filename = PurePosixPath(os.path.join(cine_mha_path, cine_dir, 'TwoDImages', *win_parts[3:]))
                    linux_filename_mha = str(linux_filename).replace('.protobin', '.mha')
                    cine_filename_times[linux_filename_mha] = time_obj
                
                cine_filename_times = dict(sorted(cine_filename_times.items(), key=lambda item: item[1])) 
                

                # fill in relative time stambs (seconds from first image) and filenames
                t_start = list(cine_filename_times.values())[0]
                for k, v in cine_filename_times.items():
                    cine_filename_times[k] = {'cine_timestamp': v, 'relative_cine_time': (v - t_start) / timedelta(microseconds=1) / 1e6}

                #
                # output dictionary with timestamps and filenames
                #
                report_filename = os.path.join(cine_report_path, f'{patient_ID}_{rtplan.plan_name}_cine_times_filenames.json')
                with open(report_filename, 'w') as f:
                    json.dump({k:{"cine_timestamp": str(v['cine_timestamp']), "relative_cine_time": v['relative_cine_time']} for k,v in cine_filename_times.items()}, f, indent=4)
                    print(f'Wrote report to {report_filename}')
                print(f'END Processing {cine_dir}: {time.time()-start_time:.2f} seconds')
    
        except Exception as e:
            print(f'Error processing {cine_dir}: {e}')
            continue