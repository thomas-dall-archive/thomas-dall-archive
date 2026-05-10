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

def fetch_via_html(channel_id):
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.37 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            # Scrape the JSON data hidden in the page source
            json_data = re.search(r'var ytInitialData = ({.*?});', html).group(1)
            data = json.loads(json_data)
            
            # Navigate the complex YouTube JSON tree to find videos
            videos = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][1]['tabRenderer']['content']['richGridRenderer']['contents']
            
            extracted = []
            for v in videos:
                if 'richItemRenderer' in v:
                    video_data = v['richItemRenderer']['content']['videoRenderer']
                    v_id = video_data['videoId']
                    v_title = video_data['title']['runs'][0]['text']
                    
                    if any(kw in v_title.lower() for kw in KEYWORDS):
                        extracted.append({
                            'id': v_id,
                            'title': v_title,
                            'date': datetime.now().strftime("%Y-%m-%d") # HTML doesn't give exact dates easily
                        })
            return extracted
    except Exception as e:
        print(f"🛑 Scraper failed for {channel_id}: {e}")
        return []

# ... (Insert the rest of your log_to_yaml and create_posts logic here) ...
