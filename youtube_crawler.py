import urllib.request
import json
import os
import time
import random
from datetime import datetime

# --- CONFIGURATION ---
# Using Handles instead of IDs
CHANNEL_HANDLES = [
    "@ThomasDallArchive", 
    "@TeddyDivine", 
    "@jandall", 
    "@ZombiesArchive", 
    "@-James-Smith-", 
    "@MondoCane-btw", 
    "@Rahu866", 
    "@dimtooley43"
]

KEYWORDS = ["thomas", "dall", "tim", "dooley", "potato", "tom", "kitty", "jan", "kota"]

DATA_FILE = "_data/videos.json"
POSTS_DIR = "_posts"

os.makedirs("_data", exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

def fetch_via_handle(handle):
    # The 'human' URL for the Videos tab
    # We use this to scrape the initial HTML which often contains the first batch of videos
    url = f"https://www.youtube.com/{(handle)}/videos"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        print(f"--- Intercepting Handle: {handle} ---")
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=20) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Since we are humoring the 'Human URL', we look for the video data 
            # embedded in the page source (ytInitialData)
            import re
            json_match = re.search(r'var ytInitialData = ({.*?});', html)
            if not json_match:
                print(f"  ⚠️ Could not find data block on the handle page for {handle}")
                return []

            res_data = json.loads(json_match.group(1))
            
            extracted = []
            def find_videos(obj):
                if isinstance(obj, dict):
                    if 'videoRenderer' in obj: yield obj['videoRenderer']
                    if 'richItemRenderer' in obj:
                        content = obj['richItemRenderer'].get('content', {})
                        if 'videoRenderer' in content: yield content['videoRenderer']
                    for v in obj.values(): yield from find_videos(v)
                elif isinstance(obj, list):
                    for item in obj: yield from find_videos(item)

            found_count = 0
            for v in find_videos(res_data):
                v_title = v.get('title', {}).get('runs', [{}])[0].get('text', '')
                v_id = v.get('videoId', '')
                if not v_title: continue
                
                found_count += 1
                print(f"  🔍 Found: {v_title[:50]}") 

                if any(kw in v_title.lower() for kw in KEYWORDS):
                    print(f"  ✅ MATCH: {v_title}")
                    extracted.append({
                        'id': v_id, 
                        'title': v_title, 
                        'date': datetime.now().strftime("%Y-%m-%d")
                    })
            
            if found_count == 0:
                print(f"  ℹ️ Scanned {handle} but found no video elements.")
            return extracted
            
    except Exception as e:
        print(f"  🛑 Handle Intercept failed: {e}")
        return []

def main():
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

    for handle in CHANNEL_HANDLES:
        # Note: We now pass the handle string
        found = fetch_via_handle(handle)
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
        print("Done. Saved matches to JSON.")
    else:
        print("No new matches found in this run.")

if __name__ == "__main__":
    main()
