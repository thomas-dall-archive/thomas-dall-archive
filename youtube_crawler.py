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
    url = "https://www.youtube.com/youtubei/v1/browse?prettyPrint=false"
    
    # EgsVdmlkZW9z = Videos Tab | EgsGc3RyZWFtcw%3D%3D = Live Tab
    tabs_to_check = [
        {"name": "Videos", "param": "EgsVdmlkZW9z"},
        {"name": "Live", "param": "EgsGc3RyZWFtcw%3D%3D"}
    ]
    
    extracted = []
    
    for tab in tabs_to_check:
        payload = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20240320.00.00"
                }
            },
            "browseId": channel_id,
            "params": tab["param"]
        }
        
        try:
            print(f"--- Intercepting {channel_id} ({tab['name']} Tab) ---")
            data_json = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data_json, headers={'Content-Type': 'application/json'})
            
            with urllib.request.urlopen(req, timeout=20) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                
                def find_videos(obj):
                    if isinstance(obj, dict):
                        if 'videoRenderer' in obj: yield obj['videoRenderer']
                        for v in obj.values(): yield from find_videos(v)
                    elif isinstance(obj, list):
                        for item in obj: yield from find_videos(item)

                found_on_this_tab = 0
                for v in find_videos(res_data):
                    v_title = v.get('title', {}).get('runs', [{}])[0].get('text', '')
                    v_id = v.get('videoId', '')
                    
                    if not v_title: continue
                    found_on_this_tab += 1
                    
                    # This tells us exactly what the bot is seeing
                    print(f"  🔍 Found: {v_title[:50]}") 

                    if any(kw in v_title.lower() for kw in KEYWORDS):
                        print(f"  ✅ MATCH: {v_title}")
                        extracted.append({
                            'id': v_id, 
                            'title': v_title, 
                            'date': datetime.now().strftime("%Y-%m-%d")
                        })
                
                if found_on_this_tab > 0:
                    print(f"  ℹ️ Scanned {found_on_this_tab} items on {tab['name']} tab.")
                    # If we found videos on this tab, don't bother checking the next one
                    break 
                    
        except Exception as e:
            print(f"  🛑 Tab {tab['name']} failed: {e}")
            continue
            
    return extracted

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
