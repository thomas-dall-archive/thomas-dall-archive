import json
import subprocess
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
channels_path = os.path.join(BASE_DIR, 'channels.txt')
archive_json_path = os.path.join(BASE_DIR, 'archive.json')

# 1. Load the list of channels
with open(channels_path, 'r') as f:
    channels = [line.strip() for line in f if line.strip()]

# 2. Load existing archive data
if os.path.exists(archive_json_path):
    with open(archive_json_path, 'r') as f:
        try:
            archive_data = json.load(f)
        except:
            archive_data = []
else:
    archive_data = []

existing_ids = {v['id'] for v in archive_data}

# 3. Scan each channel
for url in channels:
    print(f"--- Scanning Channel: {url} ---")
    
    # New, more stable command for 2026
    cmd = [
        'yt-dlp', 
        '--quiet',
        '--no-warnings',
        '--playlist-end', '20',
        '--print', '%(title)s',
        '--print', '%(id)s',
        '--print', '%(thumbnail)s',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        url
    ]
    
    result_proc = subprocess.run(cmd, capture_output=True, text=True)
    result = result_proc.stdout.splitlines()
    
    result_proc = subprocess.run(cmd, capture_output=True, text=True)
    result = result_proc.stdout.splitlines()
    
    # 4. Process the results (Title, ID, Thumb)
    for i in range(0, len(result), 3):
        try:
            v_title = result[i].strip()
            v_id = result[i+1].strip()
            v_thumb = result[i+2].strip()
            
            # Safety Check: Ensure we didn't just get the ID instead of a Title
            if v_title == v_id or not v_title:
                print(f"Skipping {v_id}: Real title not found yet.")
                continue

            if v_id not in existing_ids:
                archive_data.append({
                    "id": v_id, 
                    "title": v_title, 
                    "url": f"https://youtu.be/{v_id}", 
                    "thumbnail": v_thumb
                })
                print(f"MATCH FOUND: {v_title}")
                existing_ids.add(v_id)
        except Exception as e:
            continue

# 5. Save the final list back to archive.json
with open(archive_json_path, 'w') as f:
    json.dump(archive_data, f, indent=2)

print(f"--- Finished. Total videos in archive: {len(archive_data)} ---")
