import urllib.request
import re
import json
import os
import yaml
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
DATA_FILE = "_data/videos.yml"
POSTS_DIR = "_posts"

os.makedirs("_data", exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

def fetch_via_html(channel_id):
    # Rotating user agents to look like different browsers
    agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    headers = {
        'User-Agent': random.choice(agents),
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }

    # Add a random delay so we don't hit YouTube too fast
    time.sleep(random.uniform(2, 5))
    
    try:
        print(f"--- Intercepting: {channel_id} ---")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            json_match = re.search(r'var ytInitialData = ({.*?});', html)
            if not json_match: return []
            data = json.loads(json_match.group(1))

            # Recursive search for video IDs and Titles
            def find_videos(obj):
                if isinstance(obj, dict):
                    if 'videoRenderer' in obj: yield obj['videoRenderer']
                    for v in obj.values(): yield from find_videos(v)
                elif isinstance(obj, list):
                    for item in obj: yield from find_videos(item)

            extracted = []
            for v_data in find_videos(data):
                try:
                    v_id = v_data['videoId']
                    v_title = v_data['title']['runs'][0]['text']
                    if any(kw in v_title.lower() for kw in KEYWORDS):
                        print(f"  ✅ MATCH: {v_title}")
                        extracted.append({'id': v_id, 'title': v_title, 'date': datetime.now().strftime("%Y-%m-%d")})
                    else:
                        print(f"  ❌ Skip: {v_title[:30]}...")
                except: continue
            return extracted
    except Exception as e:
        print(f"  🛑 Blocked: {e}")
        return []

def main():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            existing_videos = yaml.safe_load(f) or []
    else:
        existing_videos = []
    
    existing_ids = {v['id'] for v in existing_videos}
    new_found = False

    for channel_id in CHANNEL_IDS:
        found = fetch_via_html(channel_id)
        for video in found:
            # Create post
            post_file = f"{POSTS_DIR}/{video['date']}-intercept-{video['id']}.md"
            if not os.path.exists(post_file):
                with open(post_file, 'w', encoding='utf-8') as f:
                    f.write(f"---\nlayout: post\ntitle: \"Intercept: {video['title']}\"\ndate: {video['date']}\n---\n\nhttps://youtu.be/{video['id']}")
            
            # Update Gallery list
            if video['id'] not in existing_ids:
                existing_videos.insert(0, video)
                existing_ids.add(video['id'])
                new_found = True

    if new_found:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(existing_videos, f, default_flow_style=False, sort_keys=False)
        print("Done. Saved matches to data file.")

if __name__ == "__main__":
    main()
