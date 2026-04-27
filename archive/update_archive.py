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
    cmd = ['yt-dlp', '--get-title', '--get-id', '--get-thumbnail', '--playlist-end', '5', url]
    result = subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()

    for i in range(0, len(result), 3):
        try:
            v_title, v_id, v_thumb = result[i], result[i+1], result[i+2]
            if v_id not in existing_ids:
                archive_data.append({"id": v_id, "title": v_title, "url": f"https://youtu.be/{v_id}", "thumbnail": v_thumb})
        except: continue

# 4. Save the results
with open('archive.json', 'w') as f:
    json.dump(archive_data, f, indent=2)
