import sys
import os
import numpy as np
import mne
from mne.preprocessing import ICA
import utils
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QInputDialog, QMessageBox, QTextEdit, QLineEdit
)
from PyQt5.QtCore import Qt
import edfio

class EEGProcessingApp(QWidget):
    def __init__(self):
        super().__init__()

        self.raw = None
        self.flag_intervals = None
        self.directory_path = None
        self.cut_raw = None  # Variable to store the cut portion of the signal

        self.initUI()

    def initUI(self):
        # Main layout
        main_layout = QHBoxLayout()

        # Left panel layout for buttons
        button_layout = QVBoxLayout()

        # Title Label
        self.label = QLabel('EEG Signal Processing', self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 18px; font-weight: bold;")
        button_layout.addWidget(self.label)

        # Load Data Button
        self.load_button = QPushButton('Load Data', self)
        self.load_button.clicked.connect(self.load_data)
        button_layout.addWidget(self.load_button)

        # FIR Filter Button
        self.fir_button = QPushButton('Apply FIR Filter', self)
        self.fir_button.setDisabled(True)
        self.fir_button.clicked.connect(self.apply_fir_filter)
        button_layout.addWidget(self.fir_button)

        # Notch Filter Button
        self.notch_button = QPushButton('Apply Notch Filter', self)
        self.notch_button.setDisabled(True)
        self.notch_button.clicked.connect(self.apply_notch_filter)
        button_layout.addWidget(self.notch_button)

        # Wavelet Denoising Button
        self.wavelet_button = QPushButton('Apply Wavelet Denoising', self)
        self.wavelet_button.setDisabled(True)
        self.wavelet_button.clicked.connect(self.apply_wavelet_denoising)
        button_layout.addWidget(self.wavelet_button)

        # ICA Button
        self.ica_button = QPushButton('Apply ICA', self)
        self.ica_button.setDisabled(True)
        self.ica_button.clicked.connect(self.apply_ica)
        button_layout.addWidget(self.ica_button)

        # Topomap Generation Button
        self.topomap_button = QPushButton('Generate Topomap Plots', self)
        self.topomap_button.setDisabled(True)
        self.topomap_button.clicked.connect(self.generate_topomap)
        button_layout.addWidget(self.topomap_button)

        # Cut Signal Button
        self.cut_button = QPushButton('Cut Signal', self)
        self.cut_button.setDisabled(True)
        self.cut_button.clicked.connect(self.cut_signal)
        button_layout.addWidget(self.cut_button)

        # Save Signal Button
        self.save_button = QPushButton('Save Signal', self)
        self.save_button.setDisabled(True)
        self.save_button.clicked.connect(self.save_signal)
        button_layout.addWidget(self.save_button)

        # Remove Noise Button
        self.remove_noise_button = QPushButton('Remove Noise', self)
        self.remove_noise_button.setDisabled(True)
        self.remove_noise_button.clicked.connect(self.remove_noise)
        button_layout.addWidget(self.remove_noise_button)

        # Plot Data Button
        self.plot_button = QPushButton('Plot Data', self)
        self.plot_button.setDisabled(True)
        self.plot_button.clicked.connect(self.plot_data)
        button_layout.addWidget(self.plot_button)

        # Exit Button
        self.exit_button = QPushButton('Exit', self)
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button)

        # Stretch to push buttons to the top
        button_layout.addStretch()

        # Right panel layout for action log
        log_layout = QVBoxLayout()
        log_label = QLabel('Action Log', self)
        log_label.setAlignment(Qt.AlignCenter)
        log_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        log_layout.addWidget(log_label)

        # Action Log Text Edit
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #F0F0F0;")
        log_layout.addWidget(self.log_text)

        # Combine layouts
        main_layout.addLayout(button_layout, 1)
        main_layout.addLayout(log_layout, 2)

        self.setLayout(main_layout)
        self.setWindowTitle('EEG Signal Processing')
        self.setGeometry(300, 300, 800, 400)
        self.show()

    def log_action(self, message):
        """
        Logs a message to the action log with a timestamp.
        """
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.append(f"[{timestamp}] {message}")

    def remove_noise(self):
        if self.raw is None:
            QMessageBox.warning(self, "Warning", "Please load data first!")
            return

        threshold, ok1 = QInputDialog.getDouble(self, "Remove Noise", "Enter amplitude threshold (µV):", 100.0, 0.1, 1000.0, 1)
        min_duration, ok2 = QInputDialog.getDouble(self, "Remove Noise", "Enter minimum duration of noise (seconds):", 1.0, 0.1, 10.0, 1)
        if ok1 and ok2:
            try:
                # Convert threshold to volts as the raw data is in volts
                threshold *= 1e-6

                # Calculate amplitude and detect noisy segments
                amplitude = np.abs(self.raw._data)
                noisy_segments = np.any(amplitude > threshold, axis=0)

                # Find continuous noisy segments
                sfreq = self.raw.info['sfreq']
                min_samples = int(min_duration * sfreq)
                noisy_segments = np.convolve(noisy_segments, np.ones(min_samples, dtype=int), 'same') >= min_samples

                # Find the start and end of noisy segments
                onsets = np.where(np.diff(noisy_segments.astype(int)) == 1)[0] / sfreq
                offsets = np.where(np.diff(noisy_segments.astype(int)) == -1)[0] / sfreq
                durations = offsets - onsets

                if len(onsets) == 0 or len(offsets) == 0:
                    QMessageBox.information(self, "Info", "No noisy segments found with the given threshold and duration.")
                    self.log_action("No noisy segments detected.")
                    return

                # Mark these segments as bad
                annotations = mne.Annotations(onset=onsets, duration=durations, description=['bad_noise'] * len(onsets))
                self.raw.set_annotations(annotations)

                # Remove these segments by retaining only good parts of the data
                self.raw = self.raw.copy().interpolate_bads(reset_bads=True)
                cleaned_raw = self.raw.copy().crop(tmin=0, tmax=None)

                QMessageBox.information(self, "Success", f"Noise removed with threshold {threshold*1e6} µV and minimum duration {min_duration} seconds.")
                self.log_action(f"Removed noisy segments with threshold={threshold*1e6} µV and min_duration={min_duration} seconds.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while removing noise:\n{e}")
                self.log_action(f"Error removing noise: {e}")


    def load_data(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select EEG Data Directory")
        if not folder_path:
            QMessageBox.critical(self, "Error", "Please select a valid directory!")
            return
        
        log_file, bdf_file_path = utils.search_files(folder_path)
        
        if not log_file or not bdf_file_path:
            QMessageBox.critical(self, "Error", "Could not find the required .log or .bdf file in the selected directory.")
            return
        
        try:
            self.flag_intervals, f1_base_time, total_duration_seconds = utils.extract_flag_intervals(log_file)
            self.raw = mne.io.read_raw_bdf(bdf_file_path, preload=True)
            self.raw.load_data()

            # Create needed directories
            self.directory_path = os.path.dirname(bdf_file_path)
            os.makedirs(os.path.join(self.directory_path, 'Images'), exist_ok=True)

            # Describe data
            self.raw.describe()

            #Pick only 16 channels
            channels = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8',
                        'A9', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16']
            self.raw.pick_channels(channels)

            # Channel names dict to match predefined layout
            channels_dict = {
                'A1': 'Fp1',
                'A2': 'Fp2',
                'A3': 'F4',
                'A4': 'Fz',
                'A5': 'F3',
                'A6': 'T7',
                'A7': 'C3',
                'A8': 'Cz',
                'A9': 'C4',
                'A10': 'T8',
                'A11': 'P4',
                'A12': 'Pz',
                'A13': 'P3',
                'A14': 'O1',
                'A15': 'Oz',
                'A16': 'O2'
            }

            # Rename channels
            self.raw.rename_channels(mapping=channels_dict)
            self.raw.set_montage('biosemi16')

            # Crop the data based on the calculated intervals
            log1_start_seconds = utils.time_to_seconds(f1_base_time.strftime('%H:%M:%S'))
            bdf_start_seconds = utils.time_to_seconds(self.raw.info['meas_date'].time().strftime("%H:%M:%S"))
            bdf_duration = self.raw.times[-1]  # in seconds

            #Compute crop boundaries based on start and end times
            if bdf_start_seconds <= log1_start_seconds:
                cut_from_start = log1_start_seconds - bdf_start_seconds
                cut_from_end = bdf_duration - total_duration_seconds - cut_from_start
            else:
                cut_from_start = 0
                cut_from_end = bdf_duration - total_duration_seconds

            # Apply crop
            self.raw.crop(tmin=cut_from_start, tmax=(bdf_duration - cut_from_end))

            QMessageBox.information(self, "Success", "Data loaded and cropped successfully!")
            self.log_text.clear()
            self.log_action("Loaded and preprocessed data successfully.")

            # Enable all processing buttons
            self.fir_button.setEnabled(True)
            self.notch_button.setEnabled(True)
            self.wavelet_button.setEnabled(True)
            self.ica_button.setEnabled(True)
            self.topomap_button.setEnabled(True)
            self.plot_button.setEnabled(True)
            self.cut_button.setEnabled(True)
            self.remove_noise_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while loading data:\n{e}")
            self.log_action(f"Error loading data: {e}")

    def apply_fir_filter(self):
        if self.raw is None:
            QMessageBox.warning(self, "Warning", "Please load data first!")
            return

        l_freq, ok1 = QInputDialog.getDouble(self, "FIR Filter", "Enter low frequency (Hz):", 0.1, 0, 1000, 1)
        h_freq, ok2 = QInputDialog.getDouble(self, "FIR Filter", "Enter high frequency (Hz):", 45, 0, 1000, 1)
        if ok1 and ok2:
            try:
                self.raw.filter(l_freq, h_freq, fir_design='firwin')
                QMessageBox.information(self, "Success", f"FIR filter applied: {l_freq}-{h_freq} Hz")
                self.log_action(f"Applied FIR filter with low_freq={l_freq} Hz and high_freq={h_freq} Hz.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while applying FIR filter:\n{e}")
                self.log_action(f"Error applying FIR filter: {e}")

    def apply_notch_filter(self):
        if self.raw is None:
            QMessageBox.warning(self, "Warning", "Please load data first!")
            return

        freqs_str, ok = QInputDialog.getText(self, "Notch Filter", "Enter frequencies (Hz, comma separated):", text="50, 60, 100, 120")
        if ok and freqs_str:
            try:
                freqs_list = [float(freq.strip()) for freq in freqs_str.split(',')]
                self.raw.notch_filter(freqs=freqs_list, fir_design='firwin')
                QMessageBox.information(self, "Success", f"Notch filter applied at frequencies: {freqs_list} Hz")
                self.log_action(f"Applied Notch filter at frequencies: {freqs_list} Hz.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while applying Notch filter:\n{e}")
                self.log_action(f"Error applying Notch filter: {e}")

    def apply_wavelet_denoising(self):
        if self.raw is None:
            QMessageBox.warning(self, "Warning", "Please load data first!")
            return

        # Wavelet type selection
        wavelet, ok_wavelet = QInputDialog.getText(self, "Wavelet Denoising", "Enter wavelet type:", text="sym4")
        if not ok_wavelet:
            return
        
        # Adaptive thresholding selection
        adaptive_threshold = QMessageBox.question(self, "Wavelet Denoising", "Use adaptive threshold?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes
        
        # Level selection
        level, ok_level = QInputDialog.getInt(self, "Wavelet Denoising", "Enter wavelet decomposition level:", value=1, min=1, max=10)
        if not ok_level:
            return

        # Threshold selection
        if not adaptive_threshold:
            threshold, ok_threshold = QInputDialog.getDouble(self, "Wavelet Denoising", "Enter threshold value:", value=0.2, min=0.0, max=10.0, decimals=2)
            if not ok_threshold:
                return
        else:
            threshold = None

        try:
            denoised_data = np.apply_along_axis(
                utils.wavelet_denoising, 1, self.raw.get_data(),
                wavelet=wavelet, adaptive_threshold=adaptive_threshold, level=level, threshold=threshold
            )
            self.raw = mne.io.RawArray(denoised_data, self.raw.info)
            if adaptive_threshold:
                QMessageBox.information(self, "Success", f"Wavelet denoising applied using {wavelet} wavelet with level {level} and adaptive thresholding.")
                self.log_action(f"Applied Wavelet Denoising with wavelet='{wavelet}', level={level}, and adaptive thresholding.")
            else:
                QMessageBox.information(self, "Success", f"Wavelet denoising applied using {wavelet} wavelet with level {level} and manual threshold of {threshold}.")
                self.log_action(f"Applied Wavelet Denoising with wavelet='{wavelet}', level={level}, and manual threshold={threshold}.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while applying Wavelet Denoising:\n{e}")
            self.log_action(f"Error applying Wavelet Denoising: {e}")



    def apply_ica(self):
        if self.raw is None:
            QMessageBox.warning(self, "Warning", "Please load data first!")
            return

        n_components, ok = QInputDialog.getInt(self, "ICA", "Enter number of components:", 15, 1, 100, 1)
        if ok:
            try:
                ica = ICA(n_components=n_components, random_state=97, max_iter=800)
                ica.fit(self.raw)
                eog_indices, _ = ica.find_bads_eog(self.raw, ch_name=['Fp1', 'Fp2'])
                ica.exclude = eog_indices
                self.raw = ica.apply(self.raw.copy())
                QMessageBox.information(self, "Success", f"ICA applied with {n_components} components.")
                self.log_action(f"Applied ICA with n_components={n_components}. Excluded components: {eog_indices}.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while applying ICA:\n{e}")
                self.log_action(f"Error applying ICA: {e}")

    def generate_topomap(self):
        if self.raw is None or self.flag_intervals is None:
            QMessageBox.warning(self, "Warning", "Please load data first!")
            return

        try:
            for interval in self.flag_intervals:
                tmin = interval[0]
                tmax = interval[1]
                label = interval[2]
                raw_copy = self.raw.copy().crop(tmin=tmin, tmax=tmax).compute_psd()
                fig = raw_copy.plot_topomap(
                    bands={
                        'Delta (0.1-3.9 Hz)': (0.1, 3.9), 
                        'Theta (4-7.9 Hz)': (4, 7.9),
                        'Alpha (8-12.9 Hz)': (8, 12.9), 
                        'Beta (13-29.9 Hz)': (13, 29.9),
                        'Low Gamma (30-59.9 Hz)': (30, 59.9), 
                        'High Gamma (60-100 Hz)': (60, 100)
                    },
                    ch_type='eeg',
                    cmap='jet',
                    show=False
                )
                fig.set_size_inches(25, 10)
                filename = f'part_{tmin}_{tmax}_{label}.png'
                save_path = os.path.join(self.directory_path, 'Images', filename)
                fig.savefig(save_path, dpi=300)
                self.log_action(f"Generated Topomap for interval {tmin}-{tmax} seconds labeled '{label}'. Saved as '{filename}'.")
            QMessageBox.information(self, "Success", "Topomap plots generated successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while generating Topomap plots:\n{e}")
            self.log_action(f"Error generating Topomap plots: {e}")

    def cut_signal(self):
        if self.raw is None:
            QMessageBox.warning(self, "Warning", "Please load data first!")
            return
        
        tmin, ok1 = QInputDialog.getDouble(self, "Cut Signal", "Enter start time (seconds):", 0.0, 0.0, self.raw.times[-1])
        tmax, ok2 = QInputDialog.getDouble(self, "Cut Signal", "Enter end time (seconds):", self.raw.times[-1], 0.0, self.raw.times[-1])

        if ok1 and ok2 and tmin < tmax:
            try:
                self.cut_raw = self.raw.copy().crop(tmin=tmin, tmax=tmax)
                QMessageBox.information(self, "Success", f"Signal cut from {tmin} to {tmax} seconds.")
                self.log_action(f"Cut signal from {tmin} to {tmax} seconds.")
                self.save_button.setEnabled(True)  # Enable the save button after a cut is made
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while cutting the signal:\n{e}")
                self.log_action(f"Error cutting signal: {e}")
        else:
            QMessageBox.warning(self, "Warning", "Invalid cut range specified!")

    def save_signal(self):
        if self.cut_raw is None:
            QMessageBox.warning(self, "Warning", "Please cut the signal first!")
            return

        save_folder = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if not save_folder:
            QMessageBox.warning(self, "Warning", "Please select a valid save directory!")
            return

        save_name, ok = QInputDialog.getText(self, "Save Signal", "Enter the filename (without extension):")
        if ok and save_name:
            try:
                save_path = os.path.join(save_folder, f"{save_name}.edf")
                mne.export.export_raw(save_path, self.cut_raw, fmt='auto')
                QMessageBox.information(self, "Success", f"Signal saved as '{save_path}'.")
                self.log_action(f"Saved signal as '{save_path}'.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while saving the signal:\n{e}")
                self.log_action(f"Error saving signal: {e}")

    def plot_data(self):
        if self.raw is None:
            QMessageBox.warning(self, "Warning", "Please load data first!")
            return
        try:
            self.raw.plot(block=True)
            self.log_action("Plotted current EEG data.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while plotting data:\n{e}")
            self.log_action(f"Error plotting data: {e}")

def main():
    app = QApplication(sys.argv)
    ex = EEGProcessingApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
