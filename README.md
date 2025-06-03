MEG

Preprocess all files: maxfilter.py

Check if .fif have all triggers - 25 triggers for video: triggeranalysis.py

Segment .fif files by start of trigger and end (question trigger) and name according to category of video, order of video and subject ID: segmentation.py

Divide each file to 3 more segments to get more samples, saved according to name and order of video 1/2/3: div.py

Use each file separately to get band powers, output saved in .xlsx fils: band.py


RATINGS

From log file to excel following all rules: logtoexcel.py

Collects all data of subject to one excel file: allexcel.py


MEG+RATINGS

Change ratings to labels: ratings-label.ipynb

Combines band power excel with target: bandpower-target.ipynb

MACHINE LEARNING
Machine learning, 2 models for arousal and valence: ML.ipynb

