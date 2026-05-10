import urllib.request
import os
import re
import json
from datetime import datetime

# --- CONFIGURATION ---
# We MUST use Channel IDs here (the ones starting with UC)
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

def fetch_via_rss(channel_id):
    # This is the official, raw XML feed for a YouTube channel
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"--- Requesting Raw RSS Feed: {channel_id} ---")
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=20) as response:
            xml_data = response.read().decode('utf-8')
            
            # Use RegEx to extract titles and IDs from the XML tags
            # <title>Video Title</title>
            # <yt:videoId>v_id</yt:videoId>
            titles = re.findall(r'<title>(.*?)</title>', xml_data)
            v_ids = re.findall(r'<yt:videoId>(.*?)</yt:videoId>', xml_data)
            
            # The first title in the XML is usually the Channel Name, so we skip it
            # We pair them up:
            extracted = []
            for i in range(len(v_ids)):
                # Adjust index because titles[0] is channel name
                v_title = titles[i+1] if (i+1) < len(titles) else "Unknown Title"
                v_id = v_ids[i]
                
                print(f"  🔍 Found: {v_title[:50]} (ID: {v_id})")

                if any(kw in v_title.lower() for kw in KEYWORDS):
                    print(f"  ✅ MATCH: {v_title}")
                    extracted.append({
                        'id': v_id, 
                        'title': v_title, 
                        'date': datetime.now().strftime("%Y-%m-%d")
                    })
            
            if not v_ids:
                print(f"  ⚠️ RSS feed returned empty or was blocked.")
            return extracted
            
    except Exception as e:
        print(f"  🛑 RSS Fetch failed: {e}")
        return []

def main():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try: existing_videos = json.load(f)
            except: existing_videos = []
    else:
        existing_videos = []
    
    existing_ids = {v['id'] for v in existing_videos}
    new_found = False

    for cid in CHANNEL_IDS:
        found = fetch_via_rss(cid)
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
        print("Done. Saved matches.")
    else:
        print("No new matches found in this run.")

if __name__ == "__main__":
    main()
