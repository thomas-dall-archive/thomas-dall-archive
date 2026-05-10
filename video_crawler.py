import urllib.request
import xml.etree.ElementTree as ET
import os
import yaml
from datetime import datetime

# --- CONFIGURATION ---
CHANNEL_IDS = [
    "UC_8sJPJkzoQcauUAcPf8bjA",
    "UCTMDW8muoabCU0cDj18ZtCg", 
    "UCb-FyxB3vYO_2L-SfFGdvtQ",
    "UCHUakNT9WeUT3MPoOZFLpew",
    "UCC0WwSFnfbIhHmZLGL8eJSA",
    "UCqXtNsJhRGFDcEWd4ziMlsw",
    "UC6rxH5XGNoeNyO7btRksH3A"
]
KEYWORDS = ["thomas", "dall", "tim", "dooley", "potato", "kittystyle"]
DATA_FILE = "_data/videos.yml"
POSTS_DIR = "_posts"

os.makedirs("_data", exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

def load_existing_videos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or []
    return []

def create_forensic_post(video_id, title, date_str):
    # This creates the RSS 'Blast' and the individual URL
    filename = f"{POSTS_DIR}/{date_str}-broadcast-{video_id}.md"
    if os.path.exists(filename):
        return

    content = f"""---
layout: post
title: "Broadcast Intercept: {title.replace('"', '')}"
date: {date_str} 12:00:00 -0000
categories: [automated-intercept]
tags: [Tim Dooley, Thomas Dall, The Potato of Life]
---
### 📡 Automated Identity Trace
**Source:** YouTube Broadcast  
**Status:** Logged to Forensic Archive

<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border: 1px solid #444;">
  <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
          src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>
</div>

---
*Machine-readable log for entity tracking: Thomas Dall / Tim Dooley.*
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

def fetch_latest_videos():
    existing_videos = load_existing_videos()
    existing_ids = {v['id'] for v in existing_videos}
    new_entries = []

    for channel_id in CHANNEL_IDS:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                root = ET.fromstring(response.read())
                ns = {'yt': 'http://www.w3.org/2005/Atom'}
                
                for entry in root.findall('yt:entry', ns):
                    v_id = entry.find('yt:id', ns).text.replace('yt:video:', '')
                    v_title = entry.find('yt:title', ns).text
                    v_date = entry.find('yt:published', ns).text
                    
                    if any(kw in v_title.lower() for kw in KEYWORDS):
                        clean_date = datetime.strptime(v_date, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
                        
                        # 1. Forge the RSS Post
                        create_forensic_post(v_id, v_title, clean_date)
                        
                        # 2. Prep for Gallery Data
                        if v_id not in existing_ids:
                            new_entries.append({'id': v_id, 'title': v_title, 'date': clean_date})

        except Exception as e:
            print(f"Error fetching {channel_id}: {e}")

    if new_entries:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(new_entries + existing_videos, f, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    fetch_latest_videos()
