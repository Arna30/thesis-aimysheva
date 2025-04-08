import mne
import numpy as np
import os
import pandas as pd

# Define frequency bands
bands = {
    'Delta': (0.5, 4), 'Theta': (4, 8), 'Alpha': (8, 12), 
    'Beta': (12, 30), 'Gamma': (30, 100)
}

# File paths
input_dir = "/projects/digimind/arna/max-filtered/20sec"
output_file = "band_powers_files_FULL_grad.xlsx"

# Get all .fif files
fif_files = [f for f in os.listdir(input_dir) if f.endswith('.fif')]

# Store results
data_list = []

for fif_file in fif_files:
    file_path = os.path.join(input_dir, fif_file)
    print(f"Processing {fif_file}...")
    
    # Load epochs
    epochs = mne.read_epochs(file_path, preload=True, verbose=False)
    
    # Select magnetometer channels
    meg_mags = epochs.copy().pick_types(meg='grad')

    # Compute PSD using Welch's method
    psds, freqs = mne.time_frequency.psd_welch(
        meg_mags, fmin=0.5, fmax=100, n_fft=2048, n_overlap=512, n_per_seg=1024, verbose=False
    )

    # Average over epochs
    psds = psds.mean(axis=0)  # Shape becomes (n_channels, n_freqs)

    # Debug: Print shapes
    print(f"After averaging epochs, psds shape: {psds.shape}, freqs shape: {freqs.shape}")

    # Compute band power
    row_data = [fif_file]
    for band_name, (fmin, fmax) in bands.items():
        band_mask = np.logical_and(freqs >= fmin, freqs <= fmax)

        print(f"{band_name} band_mask shape: {band_mask.shape}, expected psds.shape[1]: {psds.shape[1]}")

        if band_mask.sum() == 0:
            print(f"Warning: No frequencies found in range {fmin}-{fmax} Hz")
            band_power = np.zeros(psds.shape[0])  # Avoid errors
        else:
            band_power = psds[:, band_mask].mean(axis=1)  # Mean power per channel

        row_data.extend(band_power)

    data_list.append(row_data)

# Create column names
sensor_names = meg_mags.ch_names
column_names = ["File Name"] + [f"{band} {sensor}" for band in bands for sensor in sensor_names]

# Convert to DataFrame and save
band_power_df = pd.DataFrame(data_list, columns=column_names)
band_power_df.to_excel(output_file, index=False)

print(f"Band power values successfully saved to {output_file}")
