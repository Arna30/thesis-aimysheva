import os
import mne

# Define paths
input_folder = "/projects/digimind/arna/max-filtered/segmented1"
output_folder = "/projects/digimind/arna/max-filtered/20sec"
os.makedirs(output_folder, exist_ok=True)

# Process each .fif file in the folder
for file in os.listdir(input_folder):
    if file.endswith("-epo.fif"):  # Check for epochs files
        file_path = os.path.join(input_folder, file)
        epochs = mne.read_epochs(file_path, preload=True)

        # Get total number of epochs
        n_epochs = len(epochs)

        if n_epochs < 3:
            print(f"Skipping {file}, less than 3 epochs available.")
            continue  # Skip files with too few epochs

        # Split into 3 equal parts
        split_sizes = [n_epochs // 3] * 3  # Base split
        for i in range(n_epochs % 3):  # Distribute remainder
            split_sizes[i] += 1

        start = 0
        for i, size in enumerate(split_sizes):
            epochs_segment = epochs[start : start + size]
            start += size

            # Save the new epochs file
            output_filename = file.replace("-epo.fif", f"_part{i+1}-epo.fif")
            output_path = os.path.join(output_folder, output_filename)
            epochs_segment.save(output_path, overwrite=True)
            print(f"Saved: {output_path}")
