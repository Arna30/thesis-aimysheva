import os
import re
import subprocess
import numpy as np
import mne
from mne.preprocessing import ICA, create_ecg_epochs, create_eog_epochs

# Define paths and constants
base_dir = "/projects/digimind/orig/MEG/"
output_file = "/projects/digimind/arna/median_videos.fif"

path_to_processed_files = '/projects/digimind/arna/max-filtered/'
path_to_bads = '/projects/digimind/arna/max-filtered/bads/'
path_to_ICA = '/projects/digimind/arna/max-filtered/ICA/'
ctc = '/neuro/databases/ctc/ct_sparse.fif'
cal = '/neuro/databases/sss/sss_cal.dat'

subject_folder = [
  #  's_01/240519/', 's_02/240607/', 's_03/240617/',
   # 's_04/240617/',  's_05/240629/', 's_06/240629/', 
    #'s_07/240709/',  's_08/240812/', 
    #'s_09/240815/', 's_10/240810/', 's_11/240829/', 
    #'s_12/240830/', 's_13/240901/', 's_14/240913/', 's_15/240920/',
    #'s_16/240920/', 's_17/240923/', 's_18/240923/', 's_19/241001/',
    #'s_20/241004/', 's_21/241015/', 's_22/241017/', 's_23/241018/',
    #'s_24/241018/', 's_25/241029/', 's_26/241101/', 's_27/241101/',
    #'s_28/241106/', 's_29/241106/', 's_30/241112/', 's_31/241116/',
   # 's_32/241122/', 's_33/241122/', 's_34/241129/', 's_35/241129/',
   # 's_36/241205/', 
   # 's_37/241205/', 's_38/241212/', 's_39/241212/', 
   # 's_40/241213/', 's_41/241213/', 's_42/241216/', 's_43/241216/',
   # 's_44/241217/', 's_45/241217/', 's_46/250109/', 's_47/250109/'
   '/s_48/250113/', 's_49/250113/', 's_50/250117/', 's_51/250117/'
]


def valid_file(file_path):
    # Extract filename from the full path
    filename = os.path.basename(file_path)
    
    # Regex pattern to match valid filenames (files starting with "s_" followed by digits and ending with ".fif")
    pattern = re.compile(r"^s\d+.*\.fif$")
    
    # Exclusion patterns for files that should be excluded
    excluded_patterns = [
        r"_emptyroom.*",  # Exclude files with _emptyroom
        r"_eo.*",          # Exclude files with _eo
        r"_ec.*",  
        r"_game.*",        # Exclude files with _game
        r"_pre_TSST.*",    # Exclude files with _pre_TSST
        r"_TSST_control_task.*",  # Exclude specific TSST tasks
        r"_TSST_panel.*",  # Exclude specific TSST panels
        r"_TSST_speechPrep.*"  # Exclude specific TSST speech preparation tasks
    ]
    
    # Check if the filename matches the required pattern (must start with "s_" and end with ".fif")
    if not pattern.match(filename):
        return False
    
    # Check if the filename matches any of the exclusion patterns
    for excl in excluded_patterns:
        if re.search(excl, filename):
            return False
    
    # If it passes both checks, it's valid
    return True

# Get list of files, only including those that pass the valid_file function
file_list = [
    os.path.join(dirpath, filename)
    for dirpath, _, filenames in os.walk(base_dir)
    for filename in filenames if valid_file(os.path.join(dirpath, filename))
]

print('Files found')


def get_head_position(file_path):
    try:
        result = subprocess.run(
            ["/neuro/bin/util/show_fiff", "-vt222", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,  # Use 'universal_newlines' instead of 'text'
        )
        last_line = result.stdout.strip().splitlines()[-1]
        x, y, z = map(float, last_line.split()[:3])
        return int(x * 100), int(y * 100), int(z * 100)
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None, None, None

# Extract coordinates and calculate median
coordinates = [get_head_position(file) for file in file_list]
coordinates = [coord for coord in coordinates if coord != (None, None, None)]

if coordinates:
    coordinates = np.array(coordinates)
    median_position = np.median(coordinates, axis=0)
    distances = np.linalg.norm(coordinates - median_position, axis=1)
    median_index = np.argmin(distances)
    median_file = file_list[median_index]

    # Use median file as the destination for Maxwell filtering
    info = mne.io.read_info(median_file)
    destination = info['dev_head_t']
else:
    print("No valid coordinates found.")

# For each subject
for s in subject_folder:
    dl = os.listdir(base_dir + s)
    for f in dl:
        if f.endswith('_video.fif') or f.endswith('video-1.fif') or f.endswith('video-2.fif'):
            raw_name = base_dir + s + f
            ica_name = path_to_ICA + f.split('.')[0] + '_ICA.fif'
            out_file1 = path_to_processed_files + 'OTP_TSSS_' + f.split('.')[0] + '.fif'
            out_file2 = path_to_processed_files + 'OTP_TSSS_ICA_' + f.split('.')[0] + '.fif'

            if os.path.exists(out_file2):
                continue

            # Prepare bad channels
            bad_chan_name = path_to_bads + f.split('.')[0] + '.txt'
            raw = mne.io.read_raw_fif(raw_name, preload=True)
            if os.path.exists(bad_chan_name):
                with open(bad_chan_name, "r") as bad_chan_file:
                    bad_chans = ['MEG' + ch.strip() for ch in bad_chan_file.read().split(',')]
                    raw.info['bads'] = bad_chans
                    print(f"Bad channels for {f}: {bad_chans}")

            raw.interpolate_bads(reset_bads=False)

            # OTP and Maxwell filtering
            otp = mne.preprocessing.oversampled_temporal_projection(raw, duration=10.0)
            mne.channels.fix_mag_coil_types(otp.info)
            filtered = mne.preprocessing.maxwell_filter(
                otp, cross_talk=ctc, calibration=cal, st_duration=10,
                st_correlation=0.98, destination=destination
            )
            filtered.save(out_file1, overwrite=True)

            # ICA processing
            filtered.info['bads'] = []
            ica = ICA(n_components=0.95, method='fastica', random_state=0, max_iter=100)
            picks = mne.pick_types(filtered.info, meg=True, eeg=False, eog=False, stim=False, exclude='bads')
            ica.fit(filtered)

            ecg_epochs = create_ecg_epochs(filtered, tmin=-.3, tmax=.3)
            ecg_inds, _ = ica.find_bads_ecg(ecg_epochs, method='ctps')
            print(f"Found {len(ecg_inds)} ECG components")
            ica.exclude += ecg_inds[:3]

            eog_epochs = create_eog_epochs(filtered, tmin=-.5, tmax=.5)
            eog_inds, _ = ica.find_bads_eog(eog_epochs)
            print(f"Found {len(eog_inds)} EOG components")
            ica.exclude += eog_inds[:3]

            ica.save(ica_name)
            ica_data = ica.apply(filtered)
            ica_data.save(out_file2, overwrite=True)
