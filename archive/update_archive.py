import json
import subprocess
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
channels_path = os.path.join(BASE_DIR, 'channels.txt')
archive_json_path = os.path.join(BASE_DIR, 'archive.json')

with open(channels_path, 'r') as f:
    channels = [line.strip() for line in f if line.strip()]

if os.path.exists(archive_json_path):
    with open(archive_json_path, 'r') as f:
        try:
            archive_data = json.load(f)
        except:
            archive_data = []
else:
    archive_data = []

existing_ids = {v['id'] for v in archive_data}

for url in channels:
    print(f"--- Scanning: {url} ---")
    
    # Using a simple JSON output from yt-dlp is the most reliable way 2026
    cmd = [
        'yt-dlp', 
        '--quiet',
        '--playlist-end', '50',
        '--dump-json', # This outputs everything as a structured block
        '--flat-playlist',
        url
    ]
    
    result_proc = subprocess.run(cmd, capture_output=True, text=True)
    
    for line in result_proc.stdout.splitlines():
        try:
            video = json.loads(line)
            v_id = video.get('id')
            v_title = video.get('title')
            v_thumb = video.get('thumbnail') 

            # Fix for null thumbnails:
            # YouTube thumbnails follow a predictable pattern based on ID
            if not v_thumb and v_id:
                v_thumb = f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"

            if v_id and v_id not in existing_ids:
                archive_data.append({
                    "id": v_id,
                    "title": v_title,
                    "url": f"https://youtu.be/{v_id}",
                    "thumbnail": v_thumb
                })
                print(f"ADDED: {v_title}")
                existing_ids.add(v_id)
        except:
            continue

with open(archive_json_path, 'w') as f:
    json.dump(archive_data, f, indent=2)

print(f"Done. Total in archive: {len(archive_data)}")
