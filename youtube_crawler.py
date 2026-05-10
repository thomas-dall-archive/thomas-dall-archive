import urllib.request
import json
import os
import time
import random
from datetime import datetime

# --- CONFIGURATION ---
CHANNEL_IDS = [
    "UC_8sJPJkzoQcauUAcPf8bjA", "UCIRR8AjVomFfuYPM4By2MwA", 
    "UCb-FyxB3vYO_2L-SfFGdvtQ", "UCHUakNT9WeUT3MPoOZFLpew",
    "UCC0WwSFnfbIhHmZLGL8eJSA", "UC6rxH5XGNoeNyO7btRksH3A",
    "UCMUpFzS0VYXziYgtVt7VyZg", "UCTMDW8muoabCU0cDj18ZtCg"
]
KEYWORDS = ["thomas", "dall", "tim", "dooley", "potato", "tom", "kitty", "jan", "kota"]

DATA_FILE = "_data/videos.json"
POSTS_DIR = "_posts"

os.makedirs("_data", exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

def fetch_via_api(channel_id):
    # This hits YouTube's internal API directly, mimicking a browser's data request
    url = "https://www.youtube.com/youtubei/v1/browse?prettyPrint=false"
    
    # We need a basic 'context' block to make YouTube think we are a real browser
    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20240320.00.00"
            }
        },
        "browseId": channel_id,
        "params": "EgsVdmlkZW9z" # This is a magic code that tells YouTube "I want the Videos tab"
    }
    
    try:
        print(f"--- Intercepting via Internal API: {channel_id} ---")
        data_json = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data_json, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req, timeout=20) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            
            # This is where the video data hides in the internal response
            extracted = []
            def find_videos(obj):
                if isinstance(obj, dict):
                    if 'videoRenderer' in obj: yield obj['videoRenderer']
                    for v in obj.values(): yield from find_videos(v)
                elif isinstance(obj, list):
                    for item in obj: yield from find_videos(item)

            for v in find_videos(res_data):
                v_title = v.get('title', {}).get('runs', [{}])[0].get('text', '')
                v_id = v.get('videoId', '')
                
                if any(kw in v_title.lower() for kw in KEYWORDS):
                    print(f"  ✅ MATCH: {v_title}")
                    extracted.append({
                        'id': v_id, 
                        'title': v_title, 
                        'date': datetime.now().strftime("%Y-%m-%d")
                    })
            
            if not extracted:
                print(f"  ℹ️ Internal API scanned, but no keyword matches found.")
            return extracted
            
    except Exception as e:
        print(f"  🛑 Internal API failed: {e}")
        return []

def main():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                existing_videos = json.load(f)
            except:
                existing_videos = []
    else:
        existing_videos = []
    
    existing_ids = {v['id'] for v in existing_videos}
    new_found = False

    for channel_id in CHANNEL_IDS:
        found = fetch_via_api(channel_id)
        for video in found:
            post_file = f"{POSTS_DIR}/{video['date']}-intercept-{video['id']}.md"
            if not os.path.exists(post_file):
                with open(post_file, 'w', encoding='utf-8') as f:
                    f.write(f"---\nlayout: post\ntitle: \"Intercept: {video['title']}\"\ndate: {video['date']}\n---\n\nhttps://youtu.be/{video['id']}")
            
            if video['id'] not in existing_ids:
                existing_videos.insert(0, video)
                existing_ids.add(video['id'])
                new_found = True

    if new_found:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_videos, f, indent=2)
        print("Done. Saved matches to JSON.")
    else:
        print("No new matches found in this run.")

if __name__ == "__main__":
    main()
