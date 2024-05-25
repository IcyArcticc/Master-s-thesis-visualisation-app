import mne
import os
import utils

# Main function to execute the script
if __name__ == "__main__":
    log_file = 'C:/Users/Adrian/Desktop/Magisterka/Badania/22.05.2024/MM/2024-05-22_11-19-40.log'  # Log file path
    flag_intervals = utils.extract_flag_intervals(log_file)
    for interval in flag_intervals:
        print(interval)


# Load EEG data from a file (.bdf)
bdf_file_path = 'C:/Users/Adrian/Desktop/Magisterka/Badania/22.05.2024/MM/Testdata(poprawione).bdf' # Bdf file path
raw = mne.io.read_raw_bdf(bdf_file_path, preload=True)
raw.load_data()

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
# raw.info['dig']  
raw.info['ch_names']
# raw.plot_sensors(show_names=True)

# Save images in found time intervals
for interval in flag_intervals:
    tmin = interval[0]
    tmax = interval[1]
    raw_copy = raw.copy()
    przedzial = raw_copy
    przedzial = przedzial.crop(tmin=tmin, tmax=tmax)
    przedzial_spectrum = przedzial.compute_psd()
    fig = przedzial_spectrum.plot_topomap(cmap=('jet','True'), show_names=True, show=False)
    # to change size first set width and height to assign right proportions, then set dpi value to set amount of pixels needed for clear image
    fig.set_figwidth(25)
    fig.set_figheight(10)
    fig.savefig(f'{directory_path}/Images/part_{tmin}_{tmax}_{interval[2]}.png', dpi=300)

