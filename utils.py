from datetime import datetime, timedelta
import re
import os
import pywt
import numpy as np

def extract_flag_intervals(log_file):
    with open(log_file, 'r') as file:
        lines = file.readlines()

    flag_intervals = []
    current_flag = None
    start_time = None
    f1_base_time = None
    last_event_time = None

    flag_mapping = {
        "Key.f1": "F1",
        "Key.f3": "F3",
        "Key.f4": "F4",
        "Key.f6": "F6",
        "Key.f7": "F7",
        "Key.f8": "F8"
    }

    time_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
    flag_pattern = re.compile(r'CRITICAL - Pressed (\w+\.\w+)')

    def time_to_seconds(time_str):
        time_format = "%Y-%m-%d %H:%M:%S"
        dt = datetime.strptime(time_str, time_format)
        if f1_base_time is None:
            return 0
        delta = dt - f1_base_time
        return delta.total_seconds()

    for line in lines:
        time_match = time_pattern.search(line)
        flag_match = flag_pattern.search(line)

        if time_match and flag_match:
            timestamp = time_match.group(1)
            flag_key = flag_match.group(1)

            if flag_key in flag_mapping:
                dt_timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

                if flag_mapping[flag_key] == "F1" and f1_base_time is None:
                    f1_base_time = dt_timestamp

                if current_flag is None:
                    current_flag = flag_mapping[flag_key]
                    start_time = timestamp
                else:
                    end_flag = flag_mapping[flag_key]
                    if not ((current_flag == "F3" and end_flag == "F4") or 
                            (current_flag == "F7" and end_flag == "F8")):
                        flag_intervals.append((time_to_seconds(start_time), time_to_seconds(timestamp), current_flag, end_flag))
                    current_flag = flag_mapping[flag_key]
                    start_time = timestamp

                last_event_time = dt_timestamp

    total_duration_seconds = None
    if f1_base_time and last_event_time:
        total_duration_seconds = int((last_event_time - f1_base_time).total_seconds())

    return flag_intervals, f1_base_time, total_duration_seconds


# Function to convert time string to seconds since start of the day
def time_to_seconds(time_str):
    t = datetime.strptime(time_str, '%H:%M:%S')
    return t.hour * 3600 + t.minute * 60 + t.second

# Function to convert seconds since start of the day to time string
def seconds_to_time(seconds):
    return str(timedelta(seconds=seconds))

def search_files(folder_path):
    log_file = None
    bdf_file = None
    
    # Search in folder
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.log') and log_file is None:
                log_file = os.path.join(root, file)
            elif file.endswith('.bdf') and bdf_file is None:
                bdf_file = os.path.join(root, file)
            
            # Stopping search when files are found
            if log_file and bdf_file:
                break
        if log_file and bdf_file:
            break
    
    return log_file, bdf_file

def wavelet_denoising(data, wavelet='sym4', adaptive_threshold=True, level=5, threshold=None):
    # Perform wavelet decomposition
    coeffs = pywt.wavedec(data, wavelet, level=level)
    
    # Apply thresholding
    if adaptive_threshold:
        threshold = np.median(np.abs(coeffs[-1])) / 0.6745  # Example: using median absolute deviation (MAD) for threshold
    if threshold is not None:
        coeffs[1:] = [pywt.threshold(i, value=threshold, mode='soft') for i in coeffs[1:]]
    
    # Reconstruct the signal
    reconstructed_data = pywt.waverec(coeffs, wavelet)
    
    return reconstructed_data