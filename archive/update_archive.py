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
        archive_data = json.load(f)
else:
    archive_data = []

existing_ids = {v['id'] for v in archive_data}

for url in channels:
    print(f"--- Scanning Channel: {url} ---")
    
    # We add a 'user-agent' to avoid being blocked as a bot
    cmd = [
        'yt-dlp', 
        '--get-title', '--get-id', '--get-thumbnail', 
        '--playlist-end', '20', 
        '--flat-playlist',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        url
    ]
    
    result_proc = subprocess.run(cmd, capture_output=True, text=True)
    result = result_proc.stdout.splitlines()
    
    if not result:
        print(f"Warning: No data returned for {url}. Error log: {result_proc.stderr}")

    for i in range(0, len(result), 3):
        try:
            v_title, v_id, v_thumb = result[i], result[i+1], result[i+2]
            if v_id not in existing_ids:
                archive_data.append({
                    "id": v_id, 
                    "title": v_title, 
                    "url": f"https://youtu.be/{v_id}", 
                    "thumbnail": v_thumb
                })
                print(f"NEW VIDEO FOUND: {v_title}")
                existing_ids.add(v_id) # Prevent duplicates in same run
        except Exception as e:
            print(f"Error parsing line {i}: {e}")

with open(archive_json_path, 'w') as f:
    json.dump(archive_data, f, indent=2)
print(f"--- Finished. Total videos in archive: {len(archive_data)} ---")
