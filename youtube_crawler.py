import urllib.request
import json
import os
import re
from datetime import datetime

# --- CONFIGURATION ---
# Using the Channel IDs (UC...) for the most reliable RSS-Bridge results
CHANNEL_IDS = [
    "UC_8sJPJkzoQcauUAcPf8bjA", "UCIRR8AjVomFfuYPM4By2MwA", 
    "UCb-FyxB3vYO_2L-SfFGdvtQ", "UCHUakNT9WeUT3MPoOZFLpew",
    "UCC0WwSFnfbIhHmZLGL8eJSA", "UC6rxH5XGNoeNyO7btRksH3A",
    "UCMUpFzS0VYXziYgtVt7VyZg", "UCTMDW8muoabCU0cDj18ZtCg"
]

KEYWORDS = ["thomas", "dall", "tim", "dooley", "potato", "tom", "kitty", "jan", "kota"]

DATA_FILE = "_data/videos.json"
POSTS_DIR = "_posts"

# Ensure directories exist
os.makedirs("_data", exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

def fetch_via_rss_bridge(channel_id):
    # Fixed URL: context is 'By+channel+ID' and the parameter is 'c='
    bridge_url = f"https://rss-bridge.org/bridge01/?action=display&bridge=YoutubeBridge&context=By+channel+ID&c={channel_id}&format=Json"
    
    try:
        print(f"--- Intercepting via RSS-Bridge: {channel_id} ---")
        req = urllib.request.Request(bridge_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)
            items = data.get('items', [])
            
            extracted = []
            for item in items:
                v_title = item.get('title', '')
                v_url = item.get('url', '')
                
                # Extract the 11-character YouTube ID from the URL
                v_id_match = re.search(r'v=([a-zA-Z0-9_-]{11})', v_url)
                v_id = v_id_match.group(1) if v_id_match else ""

                if v_id and any(kw in v_title.lower() for kw in KEYWORDS):
                    print(f"  ✅ MATCH: {v_title}")
                    extracted.append({
                        'id': v_id, 
                        'title': v_title, 
                        'date': datetime.now().strftime("%Y-%m-%d")
                    })
            
            if items:
                print(f"  ℹ️ Bridge successfully bypassed the wall. Scanned {len(items)} videos.")
            else:
                print(f"  ⚠️ Bridge returned an empty list for this channel.")
                
            return extracted
            
    except Exception as e:
        print(f"  ⚠️ Bridge Instance rejected the request or failed: {e}")
        return []

def main():
    # Load existing data
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
        found = fetch_via_rss_bridge(channel_id)
        
        for video in found:
            # Create a Jekyll post file if it doesn't exist
            post_file = f"{POSTS_DIR}/{video['date']}-intercept-{video['id']}.md"
            if not os.path.exists(post_file):
                with open(post_file, 'w', encoding='utf-8') as f:
                    f.write(f"---\nlayout: post\ntitle: \"Intercept: {video['title']}\"\ndate: {video['date']}\n---\n\nhttps://youtu.be/{video['id']}")
            
            # Add to the JSON database if it's a new ID
            if video['id'] not in existing_ids:
                existing_videos.insert(0, video)
                existing_ids.add(video['id'])
                new_found = True

    # Save updated database
    if new_found:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_videos, f, indent=2)
        print("Done. Saved new matches to JSON.")
    else:
        print("No new keyword matches found in this run.")

if __name__ == "__main__":
    main()
