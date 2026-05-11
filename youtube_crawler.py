import subprocess
import json
import os
import time
import random
import re
import unicodedata
from datetime import datetime

# --- CONFIGURATION (Smart Privacy Edition) ---
# This finds the folder the script is currently sitting in
REPO_PATH = os.path.dirname(os.path.abspath(__file__)) 
POSTS_DIR = os.path.join(REPO_PATH, "_posts")

# Automatically find Python in your home folder without naming 'meta'
HOME = os.path.expanduser("~")
PYTHON_ENV = os.path.join(HOME, "bot_env/bin/python3")

# SMART COOKIE LOOKUP: Looks for cookies in the same folder as this script
COOKIE_FILE = os.path.join(REPO_PATH, "youtube-cookies.txt")

# --- MASTER CONTROLS ---
SCAN_DEPTH = 999

REQUIRED_KEYWORDS = [
    "dall", "dooley", "kittystyle", "potato", "haderslev", 
    "tim", "thomas", "supersusi", "susi", "jan", "danish", 
    "kota", "kitty", "archive", "reupload", "denmark"
]

CHANNELS = [
    {"name": "Thomas Dall Archive", "url": "https://www.youtube.com/channel/UC_8sJPJkzoQcauUAcPf8bjA/videos"},
    {"name": "Teddy Divine",        "url": "https://www.youtube.com/channel/UCIRR8AjVomFfuYPM4By2MwA/videos"},
    {"name": "Jan Dall",            "url": "https://www.youtube.com/channel/UCb-FyxB3vYO_2L-SfFGdvtQ/videos"},
    {"name": "Zombies Archive",     "url": "https://www.youtube.com/channel/UCHUakNT9WeUT3MPoOZFLpew/videos"},
    {"name": "James Smith",         "url": "https://www.youtube.com/channel/UCC0WwSFnfbIhHmZLGL8eJSA/videos"},
    {"name": "Mondo Cane",          "url": "https://www.youtube.com/channel/UC6rxH5XGNoeNyO7btRksH3A/videos"},
    {"name": "Rahu",                "url": "https://www.youtube.com/channel/UCMUpFzS0VYXziYgtVt7VyZg/videos"},
    {"name": "Dim Tooley",          "url": "https://www.youtube.com/channel/UCTMDW8muoabCU0cDj18ZtCg/videos"},
    {"name": "Tactical Squint",     "url": "https://www.youtube.com/channel/UCjPxf9pmgHrOf5JAKKaXp3w/videos"}
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

def get_filtered_videos(channel_info):
    label = channel_info["name"]
    url = channel_info["url"]
    print(f"[*] Scrutinizing: {label}")
    
    cmd_list = [
        PYTHON_ENV, "-m", "yt_dlp",
        "--cookies", COOKIE_FILE,
        "--dump-json",
        "--playlist-end", str(SCAN_DEPTH), 
        "--flat-playlist", 
        url
    ]
    
    matches = []
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
        for entry in result.stdout.strip().split('\n'):
            if not entry.strip(): continue
            summary_data = json.loads(entry)
            v_id = summary_data.get('id')
            
            if any(v_id in f for f in os.listdir(POSTS_DIR)):
                continue

            wait = random.uniform(30, 60)
            print(f"    [~] Video {v_id} found. Pausing {wait:.1f}s for stealth...")
            time.sleep(wait)

            cmd_video = [
                PYTHON_ENV, "-m", "yt_dlp",
                "--cookies", COOKIE_FILE,
                "-j",
                "--no-simulate",      
                "--no-abort-on-error",
                "--write-auto-subs", 
                "--skip-download",
                "--sub-format", "vtt",
                "--sub-langs", "en.*,en,en-orig",
                "--extractor-args", "youtube:player-client=ios,web",
                "-P", POSTS_DIR,
                "-o", f"temp_{v_id}",
                f"https://www.youtube.com/watch?v={v_id}"
            ]
            
            video_result = subprocess.run(cmd_video, capture_output=True, text=True)
            
            if video_result.returncode != 0:
                print(f"    [!] yt-dlp SKIP (Age Gate/Error) for {v_id}")
            else:
                print(f"    [!] Data Captured for {v_id}")
                full_data = json.loads(video_result.stdout.split('\n')[0])
                if matches_criteria(full_data):
                    matches.append(full_data)
        return matches
    except Exception as e:
        print(f"[!] Critical Error: {e}")
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

    transcript = "English transcript not available."
    all_vtt_files = [f for f in os.listdir(POSTS_DIR) if v_id in f and f.endswith(".vtt")]
    
    if all_vtt_files:
        target_file = all_vtt_files[0]
        try:
            with open(os.path.join(POSTS_DIR, target_file), 'r', encoding='utf-8') as f:
                transcript = clean_transcript(f.read())
        except: pass
        
        for f in all_vtt_files:
            try: os.remove(os.path.join(POSTS_DIR, f))
            except: pass

    for f in os.listdir(POSTS_DIR):
        if f"temp_{v_id}" in f:
            try: os.remove(os.path.join(POSTS_DIR, f))
            except: pass

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
**Source Link:** [Watch on YouTube](https://www.youtube.com/watch?v={v_id})

### Description
{{% raw %}}
{data.get('description', 'No description provided.')}
{{% endraw %}}

---

### English Transcript (Auto-Generated)
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
        subprocess.run(["git", "pull", "origin", "main", "--rebase"], check=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Bunker Auto-Update: Smart Pathing Sync"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("[+] Archive Sync Complete.")
    except Exception as e: print(f"[X] Git failure: {e}")

if __name__ == "__main__":
    print(f"--- BUNKER CRAWLER 4.8: SMART PRIVACY EDITION ---")
    if not os.path.exists(POSTS_DIR): os.makedirs(POSTS_DIR)
    
    # Forensic Check: Does the cookie file exist?
    if not os.path.exists(COOKIE_FILE):
        print(f"[!] WARNING: Cookie file NOT found at {COOKIE_FILE}")
        print(f"    Please place your youtube-cookies.txt inside the thomas-dall-archive folder.")
    
    for i, channel_info in enumerate(CHANNELS):
        matches = get_filtered_videos(channel_info)
        for video_data in matches:
            print(f"    [+] Created: {write_jekyll_post(video_data)}")
        if i < len(CHANNELS) - 1:
            wait = random.uniform(180, 300)
            print(f"[~] Channel set complete. Resting {wait/60:.1f}m for stealth...")
            time.sleep(wait)
    push_to_github()
