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
KEYWORDS = [
    "thomas", "dall", "tim", "dooley", "potato", 
    "kittystyle"
]
DATA_FILE = "_data/videos.yml"
POSTS_DIR = "_posts"

# Ensure directories exist
os.makedirs("_data", exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

def fetch_via_html(channel_id):
    # Try the main channel page first if /videos is being blocked
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Cache-Control': 'no-cache'
    }
    
    try:
        print(f"--- Attempting Intercept: {channel_id} ---")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
            # Extract JSON data
            json_match = re.search(r'var ytInitialData = ({.*?});', html)
            if not json_match:
                print(f"  ⚠️ Warning: No data block found for {channel_id}")
                return []
                
            data = json.loads(json_match.group(1))
            
            # YouTube changes the path occasionally. This 'recursive search' finds videos anywhere in the JSON
            def find_videos(obj):
                if isinstance(obj, dict):
                    if 'videoRenderer' in obj:
                        yield obj['videoRenderer']
                    for v in obj.values():
                        yield from find_videos(v)
                elif isinstance(obj, list):
                    for item in obj:
                        yield from find_videos(item)

            extracted = []
            for v_data in find_videos(data):
                v_id = v_data.get('videoId')
                # Navigate the title structure safely
                try:
                    v_title = v_data['title']['runs'][0]['text']
                except (KeyError, IndexError):
                    continue
                
                # Check keywords
                if any(kw in v_title.lower() for kw in KEYWORDS):
                    print(f"  ✅ MATCHED: {v_title}")
                    extracted.append({
                        'id': v_id,
                        'title': v_title,
                        'date': datetime.now().strftime("%Y-%m-%d")
                    })
                else:
                    # Debugging: see what we are missing
                    print(f"  ❌ Filtered: {v_title[:40]}...")
            
            return extracted
            
    except Exception as e:
        print(f"  🛑 Connection Failed for {channel_id}: {e}")
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
            try:
                existing_videos = yaml.safe_load(f) or []
            except Exception:
                existing_videos = []
    else:
        existing_videos = []
    
    existing_ids = {v['id'] for v in existing_videos}
    
    # Track if we actually changed anything
    changes_made = False

    # 2. Cycle through each Channel ID
    for channel_id in CHANNEL_IDS:
        found = fetch_via_html(channel_id)
        for video in found:
            # ALWAYS create/update the post
            create_forensic_post(video['id'], video['title'], video['date'])
            
            # Check if it needs to be added to the Gallery file
            if video['id'] not in existing_ids:
                print(f"  💾 ARCHIVING TO YAML: {video['title']}")
                existing_videos.insert(0, video) # Add to the top
                existing_ids.add(video['id'])
                changes_made = True

        # 3. Save IMMEDIATELY after each channel (Atomic Save)
        if changes_made:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(existing_videos, f, default_flow_style=False, sort_keys=False)
            print(f"  ✅ Database synced for {channel_id}")
            changes_made = False # Reset for next channel

    print("\n--- Intercept Cycle Complete ---")
