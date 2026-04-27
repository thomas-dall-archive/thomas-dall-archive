import json
import subprocess
import os

# 1. Load the list of channels
with open('channels.txt', 'r') as f:
    channels = [line.strip() for line in f if line.strip()]

# 2. Load existing archive
if os.path.exists('archive.json'):
    with open('archive.json', 'r') as f:
        archive_data = json.load(f)
else:
    archive_data = []

existing_ids = {v['id'] for v in archive_data}

# 3. Check each channel for the latest 5 videos
for url in channels:
    print(f"Scanning {url}...")
    cmd = [
        'yt-dlp', 
        '--get-title', 
        '--get-id', 
        '--get-thumbnail', 
        '--playlist-end', '50', 
        '--flat-playlist', # This is faster and more reliable for lists
        url
    ]
# 4. Save the results
with open('archive.json', 'w') as f:
    json.dump(archive_data, f, indent=2)
