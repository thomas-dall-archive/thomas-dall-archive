import urllib.request
import json
import os
import re
import time
import html
from datetime import datetime

# --- CONFIGURATION ---
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
    patterns = [
        f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
        f"https://www.youtube.com/feeds/videos.xml?user={channel_id}"
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36'}
    
    for url in patterns:
        max_retries = 4
        for attempt in range(max_retries):
            try:
                # Exponential backoff to simulate a human "refreshing" the page
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
                        break 
                    
                    extracted = []
                    for i in range(len(v_ids)):
                        # titles[0] is usually the channel name, titles[1+] are the videos
                        raw_title = titles[i+1] if (i+1) < len(titles) else "Unknown"
                        v_title = html.unescape(raw_title)
                        v_id = v_ids[i]
                        
                        if any(kw in v_title.lower() for kw in KEYWORDS):
                            print(f"  ✅ MATCH: {v_title}")
                            extracted.append({'id': v_id, 'title': v_title, 'date': datetime.now().strftime("%Y-%m-%d")})
                    
                    return extracted
                    
            except Exception as e:
                print(f"  ⚠️ Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    print(f"  ❌ Failed after {max_retries} refreshes.")
                continue
                
    return []

def main():
    # 1. Load existing database
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

    # 2. Process Channels
    for channel_id in CHANNEL_IDS:
        found_videos = fetch_via_rss(channel_id)
        
        for video in found_videos:
            # SANITIZE: Jekyll crashes on colons, quotes, and brackets in titles.
            clean_title = video['title'].replace('"', '').replace(':', ' -')
            clean_title = clean_title.replace('\\', '').replace('[', '(').replace(']', ')')
            clean_title = clean_title.replace('\n', ' ').strip()
            
            post_file = f"{POSTS_DIR}/{video['date']}-intercept-{video['id']}.md"
            
            # 3. Create individual Markdown Post
            if not os.path.exists(post_file):
                with open(post_file, 'w', encoding='utf-8') as f:
                    f.write("---\n")
                    f.write("layout: post\n")
                    f.write(f"title: \"{clean_title}\"\n")
                    f.write(f"date: {video['date']}\n")
                    f.write("---\n\n")
                    f.write(f"### Intercepted Log\n\n")
                    f.write(f"Evidence found at: https://youtu.be/{video['id']}\n")
            
            # 4. Update the JSON database
            if video['id'] not in existing_ids:
                existing_videos.insert(0, {
                    'id': video['id'],
                    'title': clean_title,
                    'date': video['date']
                })
                existing_ids.add(video['id'])
                new_found = True

    # 5. Save and Finish
    if new_found:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            # ensure_ascii=False keeps emojis/special chars readable for Jekyll
            json.dump(existing_videos, f, indent=2, ensure_ascii=False)
        print("Done. Saved matches to JSON.")
    else:
        print("No new matches found in this run.")

if __name__ == "__main__":
    main()
