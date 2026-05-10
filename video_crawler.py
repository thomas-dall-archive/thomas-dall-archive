import urllib.request
import xml.etree.ElementTree as ET
import os
import yaml
from datetime import datetime

# --- CONFIGURATION ---
CHANNEL_IDS = [
    "UC_8sJPJkzoQcauUAcPf8bjA",
    "UCIRR8AjVomFfuYPM4By2MwA", 
    "UCb-FyxB3vYO_2L-SfFGdvtQ",
    "UCHUakNT9WeUT3MPoOZFLpew",
    "UCC0WwSFnfbIhHmZLGL8eJSA",
    "UC6rxH5XGNoeNyO7btRksH3A",
    "UCMUpFzS0VYXziYgtVt7VyZg"
]
# Add more generic keywords if the titles are vague
KEYWORDS = ["thomas", "dall", "tim", "dooley", "potato"]
DATA_FILE = "_data/videos.yml"
POSTS_DIR = "_posts"

os.makedirs("_data", exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

def fetch_latest_videos():
    new_entries = []
    
    # Load existing to avoid duplicates
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            existing_videos = yaml.safe_load(f) or []
    else:
        existing_videos = []
    
    existing_ids = {v['id'] for v in existing_videos}

    for channel_id in CHANNEL_IDS:
        print(f"--- Checking Channel: {channel_id} ---")
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                xml_str = response.read()
                root = ET.fromstring(xml_str)
                
                # Use wildcard namespace to avoid the common 'Namespace Miss'
                for entry in root.findall('{*}entry'):
                    v_id = entry.find('{*}id').text.replace('yt:video:', '')
                    v_title = entry.find('{*}title').text
                    v_date = entry.find('{*}published').text
                    
                    print(f"Found Video: {v_title}")

                    # Keyword Check
                    if any(kw in v_title.lower() for kw in KEYWORDS):
                        if v_id not in existing_ids:
                            clean_date = datetime.strptime(v_date, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
                            new_entries.append({'id': v_id, 'title': v_title, 'date': clean_date})
                            print(f"  ✅ MATCHED & ADDED")
                        else:
                            print(f"  ⚠️ Already in database.")
                    else:
                        print(f"  ❌ Skipped (No keywords found in title)")

        except Exception as e:
            print(f"  🛑 Error fetching {channel_id}: {e}")

    if new_entries:
        # Save combined list
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(new_entries + existing_videos, f, default_flow_style=False, sort_keys=False)
        print(f"Successfully saved {len(new_entries)} new videos to {DATA_FILE}")
    else:
        print("No new videos matched the criteria.")

if __name__ == "__main__":
    fetch_latest_videos()
