import os
import mne
import contextlib

# Directory containing the MEG data files
DATA_DIR = "/projects/digimind/arna/max-filtered/"

# Output file path
OUTPUT_FILE = os.path.join(DATA_DIR, "trigger_analysis_final.txt")

# Expected triggers and their counts
EXPECTED_TRIGGER_COUNT = 25
EXPECTED_TRIGGERS = [1, 2, 3, 4, 5]  # Happy, Contentment, Anxiety/Fear, Sad, Neutral
QUESTION_TRIGGERS = [999, 15]  # Markers for question periods

# Helper function to count the number of occurrences for each trigger
def count_triggers(events):
    trigger_counts = {}
    for event in events:
        trigger_code = event[2]
        trigger_counts[trigger_code] = trigger_counts.get(trigger_code, 0) + 1
    return trigger_counts

# Open the output file for writing results
with open(OUTPUT_FILE, "w") as output_file:
    for file_name in os.listdir(DATA_DIR):
        if file_name.endswith("_video.fif"):  # Only process files ending with "_video.fif"
            file_path = os.path.join(DATA_DIR, file_name)
            output_file.write(f"Processing {file_name}...\n")

            # Load the MEG file
            with contextlib.redirect_stdout(None), contextlib.redirect_stderr(None):
                raw = mne.io.read_raw_fif(file_path, preload=False)

            try:
                # Extract events from the raw data without using a min_duration
                with contextlib.redirect_stdout(None), contextlib.redirect_stderr(None):
                    min_duration = 1 / raw.info['sfreq']
                    events = mne.find_events(raw, min_duration=min_duration, stim_channel='STI101')
            except ValueError as e:
                output_file.write(f"Error processing {file_name}: {e}\n")
                continue

            # Count trigger events
            trigger_counts = count_triggers(events)

            # Filter for video triggers only (1-5) and count their occurrences
            video_trigger_count = sum(trigger_counts.get(trigger, 0) for trigger in EXPECTED_TRIGGERS)

            # Save results to file
            if video_trigger_count == EXPECTED_TRIGGER_COUNT:
                output_file.write(f"{file_name}: All {EXPECTED_TRIGGER_COUNT} triggers found.\n")
            else:
                output_file.write(f"{file_name}: Expected {EXPECTED_TRIGGER_COUNT} triggers, found {video_trigger_count}.\n")
                output_file.write(f"Trigger counts: {trigger_counts}\n")

    output_file.write("Analysis complete.\n")

print(f"Analysis complete. Results saved to {OUTPUT_FILE}")
