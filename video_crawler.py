import urllib.request
import re
import json
import os
import yaml
from datetime import datetime

# --- CONFIGURATION ---
CHANNEL_IDS = [
    "UC_8sJPJkzoQcauUAcPf8bjA", # Thomas Dall Archive
    "UCIRR8AjVomFfuYPM4By2MwA", # Teddy Divine
    "UCb-FyxB3vYO_2L-SfFGdvtQ", # Jan Dall
    "UCHUakNT9WeUT3MPoOZFLpew", # Zombies Archive and Friends
    "UCC0WwSFnfbIhHmZLGL8eJSA", # James Smith
    "UC6rxH5XGNoeNyO7btRksH3A", # Mondo Cane
    "UCMUpFzS0VYXziYgtVt7VyZg", # Rahu
    "UCTMDW8muoabCU0cDj18ZtCg"  # Dim Tooley
]
KEYWORDS = ["thomas", "dall", "tim", "dooley", "potato"]
DATA_FILE = "_data/videos.yml"
POSTS_DIR = "_posts"

# Ensure directories exist
os.makedirs("_data", exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

def fetch_via_html(channel_id):
    """Accesses the public /videos page to bypass broken RSS feeds."""
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        print(f"--- Intercepting Channel: {channel_id} ---")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
            # Extract the JSON data from the page source
            json_match = re.search(r'var ytInitialData = ({.*?});', html)
            if not json_match:
                return []
                
            data = json.loads(json_match.group(1))
            
            # Navigate to the video list
            # Usually: contents -> twoColumnBrowseResultsRenderer -> tabs[1] (Videos)
            tabs = data['contents']['twoColumnBrowseResultsRenderer']['tabs']
            video_tab = next(tab for tab in tabs if 'tabRenderer' in tab and tab['tabRenderer'].get('title') in ['Videos', 'Uploads'])
            items = video_tab['tabRenderer']['content']['richGridRenderer']['contents']
            
            extracted = []
            for item in items:
                if 'richItemRenderer' in item:
                    v_data = item['richItemRenderer']['content'].get('videoRenderer')
                    if not v_data: continue
                    
                    v_id = v_data['videoId']
                    v_title = v_data['title']['runs'][0]['text']
                    
                    # Keyword Match
                    if any(kw in v_title.lower() for kw in KEYWORDS):
                        print(f"  ✅ MATCH FOUND: {v_title}")
                        extracted.append({
                            'id': v_id,
                            'title': v_title,
                            'date': datetime.now().strftime("%Y-%m-%d")
                        })
                    else:
                        print(f"  ❌ Skipping: {v_title[:30]}...")
            return extracted
    except Exception as e:
        print(f"  🛑 Access Error for {channel_id}: {e}")
        return []

def create_forensic_post(video_id, title, date_str):
    """Creates a Markdown file to trigger an RSS alert for new findings."""
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
**Source:** YouTube (Front-Door Scraper)  
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

def main():
    # 1. Load current gallery data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            existing_videos = yaml.safe_load(f) or []
    else:
        existing_videos = []
    
    existing_ids = {v['id'] for v in existing_videos}
    new_to_add = []

    # 2. Cycle through each Channel ID
    for channel_id in CHANNEL_IDS:
        found = fetch_via_html(channel_id)
        for video in found:
            # Create a post (for the RSS feed)
            create_forensic_post(video['id'], video['title'], video['date'])
            
            # Check if it needs to be added to the Gallery file
            if video['id'] not in existing_ids:
                new_to_add.append(video)
                existing_ids.add(video['id'])

    # 3. Save the updated Gallery list
    if new_to_add:
        updated_list = new_to_add + existing_videos
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(updated_list, f, default_flow_style=False, sort_keys=False)
        print(f"\nSUCCESS: Intercepted {len(new_to_add)} new target videos.")
    else:
        print("\nFINISHED: No new target matches found.")

if __name__ == "__main__":
    main()
