import subprocess
import json
import os
import time
import random
import re
import unicodedata
from datetime import datetime

# --- CONFIGURATION ---
PYTHON_ENV = "/home/meta/bot_env/bin/python3"
COOKIE_FILE = "/home/meta/youtube-cookies.txt"
REPO_PATH = "/home/meta/thomas-dall-archive" 
POSTS_DIR = os.path.join(REPO_PATH, "_posts")

REQUIRED_KEYWORDS = [
    "dall", "dooley", "kittystyle", "potato", "haderslev", 
    "tim", "thomas", "supersusi", "danish", "kota", "dora", "fetch"
]

# PERMANENT CHANNEL IDs (Fixes the hyphen/handle errors)
CHANNELS = [
    "https://www.youtube.com/channel/UC_8sJPJkzoQcauUAcPf8bjA", # Thomas Dall Archive
    "https://www.youtube.com/channel/UCIRR8AjVomFfuYPM4By2MwA", # Teddy Divine
    "https://www.youtube.com/channel/UCb-FyxB3vYO_2L-SfFGdvtQ", # Jan Dall
    "https://www.youtube.com/channel/UCHUakNT9WeUT3MPoOZFLpew", # Zombies Archive
    "https://www.youtube.com/channel/UCC0WwSFnfbIhHmZLGL8eJSA", # James Smith
    "https://www.youtube.com/channel/UC6rxH5XGNoeNyO7btRksH3A", # Mondo Cane
    "https://www.youtube.com/channel/UCMUpFzS0VYXziYgtVt7VyZg", # Rahu
    "https://www.youtube.com/channel/UCTMDW8muoabCU0cDj18ZtCg", # Dim Tooley
    "https://www.youtube.com/channel/UCjPxf9pmgHrOf5JAKKaXp3w"  # Tactical Squint
]

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

def matches_criteria(data):
    title = data.get("title", "").lower()
    desc = data.get("description", "").lower()
    return any(word in title or word in desc for word in REQUIRED_KEYWORDS)

def clean_transcript(vtt_text):
    lines = vtt_text.split('\n')
    clean_lines = []
    for line in lines:
        if any(x in line for x in ["WEBVTT", "Kind:", "Language:", "-->"]) or not line.strip():
            continue
        if not clean_lines or line.strip() != clean_lines[-1]:
            clean_lines.append(line.strip())
    return "\n".join(clean_lines)

def get_filtered_videos(channel_url):
    """Scans channel with granular delays between each video check."""
    print(f"[*] Scanning channel: {channel_url}")
    
    # 1. Get the list of the last 5 video entries (Metadata only, no subs yet)
    cmd_list = [
        PYTHON_ENV, "-m", "yt_dlp",
        "--cookies", COOKIE_FILE,
        "--dump-json",
        "--playlist-end", "5", 
        "--flat-playlist", # Fast look at the list without deep-diving yet
        channel_url
    ]
    
    matches = []
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
        for entry in result.stdout.strip().split('\n'):
            if not entry.strip(): continue
            summary_data = json.loads(entry)
            v_id = summary_data.get('id')
            
            # Skip if we already have this ID in our posts
            if any(v_id in f for f in os.listdir(POSTS_DIR)):
                continue

            # 2. "Lethargic" Delay before deep-scanning a specific video
            wait = random.uniform(30, 60)
            print(f"    [~] New video {v_id} found. Pausing {wait:.1f}s before fetching details...")
            time.sleep(wait)

            # 3. Fetch full metadata and subtitles for THIS video only
            cmd_video = [
                PYTHON_ENV, "-m", "yt_dlp",
                "--cookies", COOKIE_FILE,
                "--dump-json",
                "--write-auto-subs",
                "--skip-download",
                "--sub-format", "vtt",
                "--sub-langs", "en.*",
                "-o", os.path.join(POSTS_DIR, "temp_sub"),
                f"https://www.youtube.com/watch?v={v_id}"
            ]
            
            video_result = subprocess.run(cmd_video, capture_output=True, text=True, check=True)
            full_data = json.loads(video_result.stdout)
            
            if matches_criteria(full_data):
                matches.append(full_data)
                
        return matches
    except Exception as e:
        print(f"[!] Error scanning {channel_url}: {e}")
        return []

def write_jekyll_post(data):
    v_id = data.get("id")
    title = data.get("title")
    clean_title = title.replace('"', "'")
    slug = slugify(title)
    raw_date = data.get("upload_date", datetime.now().strftime("%Y%m%d"))
    f_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
    
    filename = f"{f_date}-{slug}-{v_id}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    transcript = "Transcript not available."
    sub_files = [f for f in os.listdir(POSTS_DIR) if f.startswith("temp_sub") and f.endswith(".vtt")]
    if sub_files:
        try:
            with open(os.path.join(POSTS_DIR, sub_files[0]), 'r', encoding='utf-8') as f:
                transcript = clean_transcript(f.read())
        except: pass
        for f in os.listdir(POSTS_DIR):
            if f.startswith("temp_sub"): os.remove(os.path.join(POSTS_DIR, f))

    content = f"""---
layout: post
title: "{clean_title}"
date: {f_date}
youtube_id: "{v_id}"
---

<div class="video-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; background: #000; border-radius: 8px; border: 1px solid #333;">
  <iframe src="https://www.youtube.com/embed/{v_id}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" allowfullscreen></iframe>
</div>

### Video Information
**Source:** [Watch on YouTube](https://www.youtube.com/watch?v={v_id})

### Description
{{% raw %}}
{data.get('description', 'No description.')}
{{% endraw %}}

---

### Transcript
<details style="cursor: pointer; background: #1a1a1a; padding: 15px; border-radius: 6px; border: 1px solid #333;">
  <summary style="font-weight: bold; color: #ffc107;">View Searchable Transcript</summary>
  <div style="margin-top: 15px; line-height: 1.6; color: #eee; font-family: monospace; white-space: pre-wrap;">
{{% raw %}}
{transcript}
{{% endraw %}}
  </div>
</details>
"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filename

def push_to_github():
    try:
        os.chdir(REPO_PATH)
        # Fix the [rejected] error by pulling first
        print("[*] Reconciling with GitHub...")
        subprocess.run(["git", "pull", "origin", "main", "--rebase"], check=True)
        
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Bunker Auto-Update: Lethargic Sync"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("[+] Archive Synced.")
        else:
            print("[~] No new forensic data to sync.")
    except Exception as e:
        print(f"[X] Git failure: {e}")

if __name__ == "__main__":
    print(f"--- LETHARGIC CRAWLER START: {datetime.now().strftime('%Y-%m-%d %H:%M')} ---")
    if not os.path.exists(POSTS_DIR): os.makedirs(POSTS_DIR)
    
    for i, channel in enumerate(CHANNELS):
        matches = get_filtered_videos(channel)
        for video_data in matches:
            print(f"[+] Archived: {write_jekyll_post(video_data)}")
            # Short breather between file writes
            time.sleep(random.uniform(5, 10))
            
        if i < len(CHANNELS) - 1:
            # LONG PAUSE between channels (2 to 5 minutes)
            wait = random.uniform(120, 300)
            print(f"[~] Channel finished. Sleeping for {wait/60:.1f} minutes...")
            time.sleep(wait)
    
    push_to_github()
    print("--- CRAWL COMPLETE ---")
