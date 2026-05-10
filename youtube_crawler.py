import urllib.request
import json
import os
import re
from datetime import datetime

# --- CONFIGURATION ---
# We use the literal channel names in quotes for the most accurate Google search
CHANNELS = [
    "Thomas Dall Archive", "Teddy Divine", "Jan Dall", 
    "Zombies Archive", "James Smith", "Mondo Cane", "Rahu866", "Dim Tooley"
]

KEYWORDS = ["thomas", "dall", "tim", "dooley", "potato", "tom", "kitty", "jan", "kota"]
DATA_FILE = "_data/videos.json"
POSTS_DIR = "_posts"

os.makedirs("_data", exist_ok=True)
os.makedirs(POSTS_DIR, exist_ok=True)

def fetch_via_google_search(channel_name):
    # Search for the channel name on YouTube via Google
    # We remove the time filter (&tbs=qdr:w) for this test to ensure we see data
    query = urllib.parse.quote(f'site:youtube.com "{channel_name}"')
    url = f"https://www.google.com/search?q={query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"--- Intercepting via Google Index: {channel_name} ---")
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=20) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # WIDE REGEX: Look for the 11-char ID anywhere it follows a 'v=' or '%3Dv%'
            # This catches raw links AND Google's encoded redirect links
            video_ids = list(set(re.findall(r'(?:v%3D|v=)([a-zA-Z0-9_-]{11})', html)))
            
            extracted = []
            for v_id in video_ids:
                # Basic title extraction from the text around the ID
                title_match = re.search(rf'{v_id}.*?<h3.*?>(.*?)</h3>', html)
                if title_match:
                    v_title = re.sub(r'<[^>]+>', '', title_match.group(1)).replace('&amp;', '&')
                else:
                    v_title = f"Intercepted: {v_id}"

                print(f"  🔍 Found: {v_title[:50]} (ID: {v_id})")

                if any(kw in v_title.lower() for kw in KEYWORDS):
                    print(f"  ✅ MATCH: {v_title}")
                    extracted.append({
                        'id': v_id, 
                        'title': v_title, 
                        'date': datetime.now().strftime("%Y-%m-%d")
                    })
            
            if not video_ids:
                print(f"  ℹ️ Zero IDs found. Google might be showing a CAPTCHA to the GitHub IP.")
            return extracted
            
    except Exception as e:
        print(f"  ⚠️ Search failed: {e}")
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

    for name in CHANNELS:
        found = fetch_via_google_search(name)
        for video in found:
            post_file = f"{POSTS_DIR}/{video['date']}-intercept-{video['id']}.md"
            if not os.path.exists(post_file):
                with open(post_file, 'w', encoding='utf-8') as f:
                    f.write(f"---\nlayout: post\ntitle: \"{video['title']}\"\ndate: {video['date']}\n---\n\nhttps://youtu.be/{video['id']}")
            
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
