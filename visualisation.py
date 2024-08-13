import mne
import os
import utils

# ---------------- Main function to execute the script ----------------
if __name__ == "__main__":
    # Search for log file and bdf file in given driectory (only one file of each type should be present)
    log_file, bdf_file_path = utils.search_files('C:/Users/Adrian/Desktop/Magisterka/Badania/16.07.2024/2024-07-16_11-37-00_EJ74')
    # log_file = 'C:/Users/Adrian/Desktop/Magisterka/Badania/22.05.2024/EL/2024-05-22_12-39-16.log'
    flag_intervals, f1_base_time, total_duration_seconds = utils.extract_flag_intervals(log_file)
    
    for interval in flag_intervals:
        print(interval)
    
    if f1_base_time:
        f1_starting_time = f1_base_time.strftime('%H:%M:%S')
        print(f"F1 flag starting time: {f1_starting_time}")
    
    if total_duration_seconds is not None:
        print(f"Total duration from F1 start to last event: {total_duration_seconds} seconds")


# Load EEG data from a file (.bdf)
# bdf_file_path = 'C:/Users/Adrian/Desktop/Magisterka/Badania/22.05.2024/EL/Testdata.bdf' # Bdf file path
raw = mne.io.read_raw_bdf(bdf_file_path, preload=True)
raw.load_data()

# ---------------- Extracting times --------------

# Provided log details for log1
log1_start_time = f1_starting_time
log1_duration = total_duration_seconds  # in seconds
log1_start_seconds = utils.time_to_seconds(log1_start_time)
log1_end_seconds = log1_start_seconds + log1_duration

# Provided log details for log2
bdf_start_time = raw.info['meas_date'].time().strftime("%H:%M:%S")
bdf_duration = raw.times[-1]  # in seconds
bdf_start_seconds = utils.time_to_seconds(bdf_start_time)
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
sync_start_time = utils.seconds_to_time(sync_start_seconds)
sync_end_time = utils.seconds_to_time(sync_end_seconds)

# ------------------------------------------------

raw.crop(tmin=cut_from_start, tmax=(bdf_duration - cut_from_end))
raw.filter(0., 105., fir_design='firwin')
# Create needed directories
directory_path = os.path.dirname(bdf_file_path)
os.makedirs(f'{directory_path}/Images', exist_ok=True)

# Describe data
raw.describe()

# Pick only 16 channels
raw.pick_channels(['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16'])

# Channel names dict to match predefined layout
channels_dict = {'A1' : 'Fp1',
                 'A2' : 'Fp2',
                 'A3' : 'F4',
                 'A4' : 'Fz',
                 'A5' : 'F3',
                 'A6' : 'T7',
                 'A7' : 'C3',
                 'A8' : 'Cz',
                 'A9' : 'C4',
                 'A10' : 'T8',
                 'A11' : 'P4',
                 'A12' : 'Pz',
                 'A13' : 'P3',
                 'A14' : 'O1',
                 'A15' : 'Oz',
                 'A16' : 'O2',
                 }

# Rename channels
raw.rename_channels(mapping=channels_dict) 
raw.set_montage('biosemi16')  
raw.info['ch_names']

# Save images in found time intervals
for interval in flag_intervals:
    tmin = interval[0]
    tmax = interval[1]
    raw_copy = raw.copy()
    przedzial = raw_copy
    przedzial = przedzial.crop(tmin=tmin, tmax=tmax)
    przedzial_spectrum = przedzial.compute_psd()

    plot_psd = przedzial.plot_psd(fmin=0.01, fmax=101, show=False, picks=['Fp1', 'Fp2', 'F3', 'Fz', 'F4', 'C3', 'Cz', 'C4'])
    plot_psd.savefig(f'{directory_path}/Images/part_{tmin}_{tmax}_{interval[2]}_PSD1.png', dpi=200)

    plot_psd = przedzial.plot_psd(fmin=0.01, fmax=101, show=False, picks=['T7', 'T8', 'P3', 'Pz', 'P4', 'O1', 'Oz', 'O2'])
    plot_psd.savefig(f'{directory_path}/Images/part_{tmin}_{tmax}_{interval[2]}_PSD2.png', dpi=200)
    #stare
#   fig = przedzial_spectrum.plot_topomap(cmap=('jet','True'), show_names=True, show=False)
#nowe
    fig = przedzial_spectrum.plot_topomap(bands={'Delta (0.1-3.9 Hz)': (0.1, 3.9), 'Theta (4-7.9 Hz)': (4, 7.9),
                                                 'Alpha (8-12.9 Hz)': (8, 12.9), 'Beta (13-29.9 Hz)': (13, 29.9),
                                                 'Low Gamma (30-59,9 Hz)': (30, 59.9), 'High Gamma (60-100 Hz)':(60, 100)}, 
                                                 cmap=('jet','True'), show_names=True, show=False)
    # to change size first set width and height to assign right proportions, then set dpi value to set amount of pixels needed for clear image
    fig.set_figwidth(25)
    fig.set_figheight(10)
    fig.savefig(f'{directory_path}/Images/part_{tmin}_{tmax}_{interval[2]}.png', dpi=300)


