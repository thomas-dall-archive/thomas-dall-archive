import subprocess
import json
import os
import sys
import time
import random
import re
import unicodedata
from datetime import datetime

# --- CONFIGURATION ---
PYTHON_ENV = "/home/meta/bot_env/bin/python3"
COOKIE_FILE = "/home/meta/youtube-cookies.txt"
# Path to your repo on the T440
REPO_PATH = "/home/meta/thomas-dall-archive" 
POSTS_DIR = os.path.join(REPO_PATH, "_posts")

# Forensic Keywords (Identity Filter)
REQUIRED_KEYWORDS = [
    "dall", "dooley", "kittystyle", "potato", "haderslev", 
    "tim", "thomas", "supersusi", "danish", "kota", "dora", "fetch"
]

CHANNELS = [
    "https://www.youtube.com/@ThomasDallArchive",
    "https://www.youtube.com/@TeddyDivine",
    "https://www.youtube.com/@jandall",
    "https://www.youtube.com/@ZombiesArchive",
    "https://www.youtube.com/@-James-Smith-",
    "https://www.youtube.com/@MondoCane-btw",
    "https://www.youtube.com/@Rahu866",
    "https://www.youtube.com/@dimtooley43",
    "https://www.youtube.com/@TacticalSquint"
]

def slugify(text):
    """Turns titles into SEO-friendly URL slugs."""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

def matches_criteria(data):
    """Filters video metadata for our specific forensic targets."""
    title = data.get("title", "").lower()
    desc = data.get("description", "").lower()
    return any(word in title or word in desc for word in REQUIRED_KEYWORDS)

def clean_transcript(vtt_text):
    """Strips timestamps and technical headers from auto-subs."""
    lines = vtt_text.split('\n')
    clean_lines = []
    for line in lines:
        if any(x in line for x in ["WEBVTT", "Kind:", "Language:", "-->"]) or not line.strip():
            continue
        # Deduplicate consecutive lines
        if not clean_lines or line.strip() != clean_lines[-1]:
            clean_lines.append(line.strip())
    return "\n".join(clean_lines)

def get_filtered_videos(channel_url):
    """Scans last 5 videos and returns all new relevant matches."""
    print(f"[*] Scanning channel: {channel_url}")
    # Temp file for sub extraction
    temp_sub_base = os.path.join(POSTS_DIR, "temp_sub")
    
    cmd = [
        PYTHON_ENV, "-m", "yt_dlp",
        "--cookies", COOKIE_FILE,
        "--impersonate", "chrome",
        "--js-runtimes", "node",
        "--dump-json",
        "--playlist-end", "5", 
        "--write-auto-subs",
        "--skip-download",
        "--sub-format", "vtt",
        "--sub-langs", "en.*",
        "-o", temp_sub_base,
        channel_url
    ]
    
    matches = []
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        for entry in result.stdout.strip().split('\n'):
            if not entry.strip(): continue
            data = json.loads(entry)
            
            if matches_criteria(data):
                v_id = data['id']
                # Check if we already have this specific Video ID in our posts
                if not any(v_id in f for f in os.listdir(POSTS_DIR)):
                    matches.append(data)
                else:
                    print(f"[~] Skipping existing archive: {v_id}")
        return matches
    except Exception as e:
        print(f"[!] Scan Error for {channel_url}: {e}")
        return []

def write_jekyll_post(data):
    """Creates a Markdown post with Embeds, SEO, and Expandable Transcript."""
    v_id = data.get("id")
    title = data.get("title")
    clean_title = title.replace('"', "'")
    slug = slugify(title)
    
    raw_date = data.get("upload_date", datetime.now().strftime("%Y%m%d"))
    f_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
    
    # Filename format: YYYY-MM-DD-seo-slug-id.md
    filename = f"{f_date}-{slug}-{v_id}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    # Transcript Retrieval
    transcript = "Transcript not available."
    sub_files = [f for f in os.listdir(POSTS_DIR) if f.startswith("temp_sub") and f.endswith(".vtt")]
    if sub_files:
        try:
            with open(os.path.join(POSTS_DIR, sub_files[0]), 'r', encoding='utf-8') as f:
                transcript = clean_transcript(f.read())
        except: pass
        # Clean up all temporary subtitle files
        for f in os.listdir(POSTS_DIR):
            if f.startswith("temp_sub"): os.remove(os.path.join(POSTS_DIR, f))

    content = f"""---
layout: post
title: "{clean_title}"
date: {f_date}
youtube_id: "{v_id}"
---

<div class="video-container" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; background: #000; border-radius: 8px; border: 1px solid #333;">
  <iframe 
    src="https://www.youtube.com/embed/{v_id}" 
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;" 
    allowfullscreen>
  </iframe>
</div>

### Video Information
**Source Link:** [Watch on YouTube](https://www.youtube.com/watch?v={v_id})

### Description
{{% raw %}}
{data.get('description', 'No description provided.')}
{{% endraw %}}

---

### Video Transcript
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
    """Syncs the new forensic evidence to the live site."""
    try:
        os.chdir(REPO_PATH)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            print("[*] New forensic data found. Syncing to GitHub...")
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Bunker Auto-Update: Filtered Video Record"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("[+] Archive Synced Successfully.")
        else:
            print("[~] No new relevant videos detected. Archive is up to date.")
    except Exception as e:
        print(f"[X] Git failure: {e}")

if __name__ == "__main__":
    print(f"--- BUNKER CRAWLER START: {datetime.now().strftime('%Y-%m-%d %H:%M')} ---")
    
    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)
    
    for i, channel in enumerate(CHANNELS):
        matches = get_filtered_videos(channel)
        
        for video_data in matches:
            fname = write_jekyll_post(video_data)
            print(f"[+] Archived: {fname}")
            
        # Rate Limiting: Human-like delay between channel scans
        if i < len(CHANNELS) - 1:
            wait = random.uniform(25, 55)
            print(f"[~] Mimicking human browsing... sleeping {wait:.1f}s")
            time.sleep(wait)
    
    push_to_github()
    print("--- BUNKER CRAWL COMPLETE ---")
