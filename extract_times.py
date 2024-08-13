from datetime import datetime, timedelta
import visualisation

# Function to convert time string to seconds since start of the day
def time_to_seconds(time_str):
    t = datetime.strptime(time_str, '%H:%M:%S')
    return t.hour * 3600 + t.minute * 60 + t.second

# Function to convert seconds since start of the day to time string
def seconds_to_time(seconds):
    return str(timedelta(seconds=seconds))

# Provided log details for log1
log1_start_time = visualisation.f1_starting_time
log1_duration = visualisation.total_duration_seconds  # in seconds
log1_start_seconds = time_to_seconds(log1_start_time)
log1_end_seconds = log1_start_seconds + log1_duration

# Provided log details for log2
bdf_start_time = visualisation.raw.info['meas_date'].time().strftime("%H:%M:%S")
bdf_duration = visualisation.raw.times[-1]  # in seconds
bdf_start_seconds = time_to_seconds(bdf_start_time)
bdf_end_seconds = bdf_start_seconds + bdf_duration

# Initialize variables to hold the synchronized times
sync_start_seconds = 0
sync_end_seconds = 0
cut_from_start = 0
cut_from_end = 0

# Determine the appropriate case and adjust times accordingly
if bdf_start_seconds <= log1_start_seconds:
    if bdf_end_seconds <= log1_end_seconds:
        # log2 starts before or at the same time and ends before or at the same time
        sync_start_seconds = log1_start_seconds
        sync_end_seconds = log1_end_seconds
        cut_from_start = log1_start_seconds - bdf_start_seconds
        cut_from_end = bdf_end_seconds - log1_end_seconds
    else:
        # log2 starts before or at the same time and ends after log1
        sync_start_seconds = log1_start_seconds
        sync_end_seconds = log1_end_seconds
        cut_from_start = log1_start_seconds - bdf_start_seconds
        cut_from_end = bdf_end_seconds - log1_end_seconds
else:
    if bdf_end_seconds >= log1_end_seconds:
        # log2 starts after or at the same time and ends after or at the same time
        sync_start_seconds = bdf_start_seconds
        sync_end_seconds = bdf_start_seconds + log1_duration
        cut_from_end = bdf_end_seconds - sync_end_seconds
    else:
        # log2 starts after or at the same time and ends before log1
        sync_start_seconds = bdf_start_seconds
        sync_end_seconds = bdf_start_seconds + log1_duration
        cut_from_end = bdf_end_seconds - sync_end_seconds

# Convert synchronized times back to time strings
sync_start_time = seconds_to_time(sync_start_seconds)
sync_end_time = seconds_to_time(sync_end_seconds)

print(f"Synchronized start time: {sync_start_time}")
print(f"Synchronized end time: {sync_end_time}")
print(f"Cut {cut_from_start} seconds from the start of the second log.")
print(f"Cut {cut_from_end} seconds from the end of the second log.")

