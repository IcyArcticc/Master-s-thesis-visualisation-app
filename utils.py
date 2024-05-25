from datetime import datetime
import re

def extract_flag_intervals(log_file):
    with open(log_file, 'r') as file:
        lines = file.readlines()

    flag_intervals = []
    current_flag = None
    start_time = None
    f1_base_time = None

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
                if flag_mapping[flag_key] == "F1" and f1_base_time is None:
                    f1_base_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

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

    return flag_intervals