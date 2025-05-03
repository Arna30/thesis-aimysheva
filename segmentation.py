import mne
import numpy as np
import os

# Define trigger mapping
trigger_mapping = {
    1: 'happy',
    2: 'cont',
    3: 'anx',
    4: 'sad',
    5: 'neut',
    10: 'break',
    999: 'questions_start_s01_04',  # For s01-s04
    15: 'questions_start_s05_onwards'  # For s05 and onwards
}

# Directory paths
input_dir = '/projects/digimind/arna/max-filtered/'
output_dir = '/projects/digimind/arna/max-filtered/segmented1/'


file_numbers = [
    '49'
]


# List all files in maxfiltered folder
for file_name in os.listdir(input_dir):
    if file_name.endswith('video.fif'):
        file_number = file_name.split('_')[-2].lstrip('s')
        if file_number in file_numbers:
            file_path = os.path.join(input_dir, file_name)

            # Load raw data
            raw = mne.io.read_raw_fif(file_path, preload=True)

            # Create events from annotations (trigger codes) in data
            events = mne.find_events(raw, stim_channel='STI101')

            # Print unique event codes to check for validity
            print(f"Unique event codes in {file_name}:", np.unique(events[:, 2]))

            # Define the event ids for each video category
            video_event_ids = [1, 2, 3, 4, 5]  # Happy, Cont, Anx, Sad, Neut
            epochs_dict = {}

            # Extract the base file name (without '.video' part)
            base_file_name = file_name.replace('_video.fif', '')  

            # Iterate through events to create segments
            for video_trigger in video_event_ids:
                # Find all video trigger events
                video_events = events[events[:, 2] == video_trigger]

                # For each video event, find the next question event (999 or 15)
                for video_event in video_events:
                    video_time = video_event[0] / raw.info['sfreq']  # Convert sample number to time (in seconds)
                    
                    # Find the next question trigger (999 or 15) after the current video trigger
                    next_question_event = None
                    for next_event in events:
                        if next_event[2] in [999, 15] and next_event[0] > video_event[0]:
                            next_question_event = next_event
                            break
                    
                    # Debug: Print information for each video and question event
                    print(f"Video trigger {video_trigger} at {video_time}s")
                    print(f"Next question trigger: {next_question_event}")

                    if next_question_event is not None:
                        question_time = next_question_event[0] / raw.info['sfreq']  # Convert sample number to time (in seconds)
                        print(f"Question trigger at {question_time}s")

                        # Define the epoch start (video trigger time) and end (question trigger time)
                        tmin = video_time
                        tmax = question_time
                        print(f"Epoch duration: {tmax - tmin}s")

                        # Define the event for the current video
                        event_id = video_trigger

                        # Create epochs for this segment
                        epochs = mne.Epochs(
                            raw, events, event_id=event_id, tmin=0, tmax=(tmax - tmin),
                            baseline=None, reject_by_annotation=True, preload=True
                        )

                        # Store the epochs in the dictionary, categorizing by video type
                        if trigger_mapping[video_trigger] not in epochs_dict:
                            epochs_dict[trigger_mapping[video_trigger]] = []
                        epochs_dict[trigger_mapping[video_trigger]].append(epochs)
                    else:
                        print(f"Warning: No question trigger found after video trigger {video_trigger}.")

            # Check if epochs were created and save them
            if epochs_dict:
                for video_category, epochs_list in epochs_dict.items():
                    for idx, epochs in enumerate(epochs_list):
                        # Include the base file name (excluding '.video' part)
                        file_name_save = f'{base_file_name}_{video_category}_{idx + 1}_epochs-epo.fif'
                        file_path_save = os.path.join(output_dir, file_name_save)
                        epochs.save(file_path_save, overwrite=True)
                        print(f'Saved: {file_path_save}')
            else:
                print(f"No epochs created for {file_name}.")

print('Epochs creation and saving is complete.')
