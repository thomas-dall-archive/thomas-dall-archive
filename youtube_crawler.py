import urllib.request
import json
import os
import time
import random
from datetime import datetime
import re

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
    # Using Piped API instances which are generally more stable for scrapers
    instances = ["https://pipedapi.kavin.rocks", "https://pipedapi.drgns.space", "https://pipedapi.astreapp.ca"]
    random.shuffle(instances)
    
    for instance in instances:
        url = f"{instance}/channels/{channel_id}"
        try:
            print(f"--- Intercepting via {instance}: {channel_id} ---")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Piped returns a dictionary with a 'relatedStreams' list
                videos = data.get('relatedStreams', [])
                
                extracted = []
                for v in videos:
                    v_title = v.get('title', '')
                    v_id = v.get('url', '').split('=')[-1] # Extracts ID from /watch?v=ID
                    
                    if any(kw in v_title.lower() for kw in KEYWORDS):
                        print(f"  ✅ MATCH: {v_title}")
                        extracted.append({
                            'id': v_id, 
                            'title': v_title, 
                            'date': datetime.now().strftime("%Y-%m-%d")
                        })
                
                if videos: # If the instance gave us a list of videos, it's a success
                    return extracted
        except Exception as e:
            print(f"  ⚠️ Instance {instance} failed: {e}")
            continue
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
        found = fetch_via_invidious(channel_id)
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
        print("Done. Saved matches to JSON file.")
    else:
        print("No new matches found in this run.")

if __name__ == "__main__":
    main()
