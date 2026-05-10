import urllib.request
import json
import os
import re
import time
import html
from datetime import datetime

# --- CONFIGURATION ---
# Using the UC... IDs which are now confirmed working via RSS
CHANNEL_IDS = [
    "UC_8sJPJkzoQcauUAcPf8bjA", # Thomas Dall Archive
    "UCIRR8AjVomFfuYPM4By2MwA", # Teddy Divine
    "UCb-FyxB3vYO_2L-SfFGdvtQ", # Jan Dall
    "UCHUakNT9WeUT3MPoOZFLpew", # Zombies Archive
    "UCC0WwSFnfbIhHmZLGL8eJSA", # James Smith
    "UC6rxH5XGNoeNyO7btRksH3A", # Mondo Cane
    "UCMUpFzS0VYXziYgtVt7VyZg", # Rahu
    "UCTMDW8muoabCU0cDj18ZtCg"  # Dim Tooley
]

KEYWORDS = ["thomas", "dall", "tim", "dooley", "potato", "tom", "kitty", "jan", "kota"]

DATA_FILE = "_data/videos.json"
POSTS_DIR = "_posts"

# Ensure folders exist
os.makedirs("_data", exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

def fetch_via_rss(channel_id):
    # The patterns we want to try
    patterns = [
        f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
        f"https://www.youtube.com/feeds/videos.xml?user={channel_id}"
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36'}
    
    for url in patterns:
        # --- RETRY LOGIC (The 'Refresh' Simulation) ---
        max_retries = 4
        for attempt in range(max_retries):
            try:
                # Wait longer each time we fail (Exponential Backoff)
                wait_time = (attempt + 1) * 5 
                time.sleep(wait_time)
                
                print(f"--- Requesting RSS (Attempt {attempt + 1}/{max_retries}): {channel_id} ---")
                
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as response:
                    xml_data = response.read().decode('utf-8')
                    
                    v_ids = re.findall(r'<yt:videoId>(.*?)</yt:videoId>', xml_data)
                    titles = re.findall(r'<title>(.*?)</title>', xml_data)
                    
                    if not v_ids:
                        print(f"  ℹ️ Pattern connected but returned no videos. Trying next pattern...")
                        break # Break retry loop, move to next pattern
                    
                    extracted = []
                    for i in range(len(v_ids)):
                        raw_title = titles[i+1] if (i+1) < len(titles) else "Unknown"
                        v_title = html.unescape(raw_title)
                        v_id = v_ids[i]
                        
                        if any(kw in v_title.lower() for kw in KEYWORDS):
                            print(f"  ✅ MATCH: {v_title}")
                            extracted.append({'id': v_id, 'title': v_title, 'date': datetime.now().strftime("%Y-%m-%d")})
                    
                    return extracted # SUCCESS: Return and stop everything for this channel
                    
            except Exception as e:
                print(f"  ⚠️ Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    print(f"  ❌ Failed after {max_retries} refreshes.")
                continue # Try the next 'refresh' (retry)
                
    return []

def main():
    # 1. Load existing video data so we don't duplicate
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

    # 2. Loop through every channel in our config
    for channel_id in CHANNEL_IDS:
        found_videos = fetch_via_rss(channel_id)
        
        for video in found_videos:
            # 3. Create a Jekyll markdown post for each match
            post_file = f"{POSTS_DIR}/{video['date']}-intercept-{video['id']}.md"
            
            if not os.path.exists(post_file):
                with open(post_file, 'w', encoding='utf-8') as f:
                    f.write(f"---\n")
                    f.write(f"layout: post\n")
                    f.write(f"title: \"{video['title']}\"\n")
                    f.write(f"date: {video['date']}\n")
                    f.write(f"---\n\n")
                    f.write(f"https://youtu.be/{video['id']}")
            
            # 4. Update the JSON database if it's a brand new video
            if video['id'] not in existing_ids:
                existing_videos.insert(0, video)
                existing_ids.add(video['id'])
                new_found = True

    # 5. Save the JSON database if anything new was found
    if new_found:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_videos, f, indent=2)
        print("Done. Saved matches to JSON.")
    else:
        print("No new matches found in this run.")

if __name__ == "__main__":
    main()
