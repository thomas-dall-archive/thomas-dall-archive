import urllib.request
import xml.etree.ElementTree as ET
import os
import datetime

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

# Only index videos containing these words (Case-Insensitive)
KEYWORDS = ["thomas", "dall", "tim", "dooley", "potato", "potato69", "kota", "kittystyle", "kittystyles"]

POSTS_DIR = "_posts"
os.makedirs(POSTS_DIR, exist_ok=True)

def fetch_latest_videos(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            ns = {'yt': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('yt:entry', ns):
                video_id = entry.find('yt:id', ns).text.replace('yt:video:', '')
                title = entry.find('yt:title', ns).text
                date_published = entry.find('yt:published', ns).text
                
                # --- KEYWORD FILTER GATE ---
                title_lower = title.lower()
                if any(word in title_lower for word in KEYWORDS):
                    create_jekyll_post(video_id, title, date_published)
                else:
                    print(f"Skipping: '{title}' (Does not match keywords)")
                    
    except Exception as e:
        print(f"Failed to fetch channel {channel_id}: {e}")

def create_jekyll_post(video_id, title, date_published):
    dt = datetime.datetime.strptime(date_published, "%Y-%m-%dT%H:%M:%S%z")
    jekyll_date = dt.strftime("%Y-%m-%d %H:%M:%S %z")
    file_date = dt.strftime("%Y-%m-%d")
    
    filename = f"{POSTS_DIR}/{file_date}-broadcast-{video_id}.md"
    
    if os.path.exists(filename):
        return
        
    print(f"🚨 TARGET BROADCAST DETECTED: {title}")
    
    post_content = f"""---
layout: post
title: "Archived Broadcast: {title.replace('"', '')}"
date: {jekyll_date}
categories: [broadcast-archive, video-evidence]
tags: [Tim Dooley, Thomas Dall, The Potato of Life, Evidence Intercept]
---

### 📡 Automated Broadcast Intercept
**Status:** Logged into Forensic Archive  

<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; margin-top: 20px; border: 2px solid #444;">
  <iframe style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
          src="https://www.youtube.com/embed/{video_id}" 
          frameborder="0" allowfullscreen>
  </iframe>
</div>

---
*Note: This specific broadcast was flagged by the keyword filter for identity-relevant content.*
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(post_content)

for cid in CHANNEL_IDS:
    fetch_latest_videos(cid)
