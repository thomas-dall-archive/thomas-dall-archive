import json
import subprocess
import os

# Load existing data or start fresh
if os.path.exists('archive.json'):
    with open('archive.json', 'r') as f:
        archive_data = json.load(f)
else:
    archive_data = []

# Get URLs from channels.txt
with open('/automation/channels.txt', 'r') as f:
    channels = [line.strip() for line in f if line.strip()]

existing_ids = {item['id'] for item in archive_data}

for url in channels:
    print(f"Checking {url}...")
    # Get the last 5 videos from each channel
    cmd = ['yt-dlp', '--get-title', '--get-id', '--get-thumbnail', '--playlist-end', '5', url]
    result = subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines()

    # yt-dlp returns: Title, ID, Thumbnail URL in repeating order
    for i in range(0, len(result), 3):
        try:
            video_title = result[i]
            video_id = result[i+1]
            thumb_url = result[i+2]
            
            if video_id not in existing_ids:
                archive_data.append({
                    "id": video_id,
                    "title": video_title,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "thumbnail": thumb_url
                })
                print(f"Added: {video_title}")
        except IndexError:
            break

# Save updated list
with open('archive.json', 'w') as f:
    json.dump(archive_data, f, indent=2)
