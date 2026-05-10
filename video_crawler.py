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

# The Identity Trap Keywords
KEYWORDS = ["thomas", "dall", "tim", "dooley", "potato", "Placeholder1", "Placeholder2"]

DATA_FILE = "_data/videos.yml"
POSTS_DIR = "_posts"

# Ensure directories exist
os.makedirs("_data", exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

def fetch_via_html(channel_id):
    """
    Bypasses the 404-prone RSS feed by scraping the channel's /videos page directly.
    """
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        print(f"--- Intercepting: {channel_id} ---")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
            # Find the JSON blob containing video data
            json_match = re.search(r'var ytInitialData = ({.*?});', html)
            if not json_match:
                print(f"  🛑 Could not find ytInitialData for {channel_id}")
                return []
                
            data = json.loads(json_match.group(1))
            
            # Navigate the JSON structure to find the video list
            # Note: The structure can vary slightly, so we use a safe get approach
            try:
                tabs = data['contents']['twoColumnBrowseResultsRenderer']['tabs']
                # Usually the second tab (index 1) is 'Videos'
                video_tab = next(tab for tab in tabs if 'tabRenderer' in tab and tab['tabRenderer'].get('title') in ['Videos', 'Uploads'])
                items = video_tab['tabRenderer']['content']['richGridRenderer']['contents']
            except (KeyError, StopIteration):
                print(f"  ⚠️ Navigation failed for {channel_id}. Structure might have changed.")
                return []

            extracted = []
            for item in items:
                if 'richItemRenderer' in item:
                    video_renderer = item['richItemRenderer']['content'].get('videoRenderer')
                    if not video_renderer: continue
                    
                    v_id = video_renderer['videoId']
                    v_title = video_renderer['title']['runs'][0]['text']
                    
                    # Apply keyword filter
                    if any(kw in v_title.lower() for kw in KEYWORDS):
                        print(f"  ✅ MATCHED: {v_title}")
                        extracted.append({
                            'id': v_id,
                            'title': v_title,
                            'date': datetime.now().strftime("%Y-%m-%d")
                        })
                    else:
                        # Log filtered titles for debugging in GitHub Actions
                        print(f"  ❌ Filtered: {v_title[:40]}...")
            return extracted
            
    except Exception as e:
        print(f"  🛑 Scraper failed for {channel_id}: {e}")
        return []

def create_forensic_post(video_id, title, date_str):
    """
    Generates a Markdown file for the _posts folder to trigger the RSS blast.
    """
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
**Source:** YouTube Broadcast (Anti-404 Scraper)
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
    # Load existing videos to avoid duplicates in the gallery
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            existing_videos = yaml.safe_load(f) or []
    else:
        existing_videos = []
    
    existing_ids = {v['id'] for v in existing_videos}
    new_found = []

    for cid in CHANNEL_IDS:
        found_videos = fetch_via_html(cid)
        for v in found_videos:
            # Generate the RSS Post
            create_forensic_post(v['id'], v['title'], v['date'])
            
            # Update the Gallery list if new
            if v['id'] not in existing_ids:
                new_found.append(v)
                existing_ids.add(v['id'])

    if new_found:
        # Prepend new videos so they show up at the top
        updated_list = new_found + existing_videos
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(updated_list, f, default_flow_style=False, sort_keys=False)
        print(f"\nSUCCESS: Logged {len(new_found)} new videos.")
    else:
        print("\nCOMPLETE: No new matches found today.")

if __name__ == "__main__":
    main()
