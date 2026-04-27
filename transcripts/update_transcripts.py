import os
import json
import subprocess
import re
from datetime import datetime

# Configuration: Target the primary channel only
CHANNEL_URL = "https://www.youtube.com/@ThePotatoofLife/videos"
OUTPUT_FILE = "primary_transcripts.json"

def clean_vtt(vtt_text):
    """Parses VTT to extract text and start times."""
    lines = vtt_text.splitlines()
    entries = []
    
    # Regex to find timestamps (00:00:00.000)
    timestamp_re = re.compile(r'(\d{2}:\d{2}:\d{2})\.\d{3} -->')
    
    current_text = []
    current_time = "00:00:00"
    
    for line in lines:
        if "-->" in line:
            # If we have collected text for a previous timestamp, save it
            if current_text:
                text_content = " ".join(current_text).strip()
                if text_content:
                    # Convert "00:01:23" to total seconds for the URL link
                    h, m, s = map(int, current_time.split(':'))
                    total_seconds = h * 3600 + m * 60 + s
                    entries.append({
                        "time": current_time,
                        "seconds": total_seconds,
                        "text": text_content
                    })
                current_text = []
            
            # Update current timestamp
            match = timestamp_re.search(line)
            if match:
                current_time = match.group(1)
        
        elif not any(x in line for x in ["WEBVTT", "Kind:", "Language:"]) and line.strip():
            # Clean out auto-sub HTML tags like <c>
            clean_line = re.sub(r'<[^>]*>', '', line)
            if clean_line.strip():
                current_text.append(clean_line.strip())
                
    return entries

def run_sync():
    print(f"--- Starting Primary Transcript Sync: {datetime.now()} ---")
    
    # 1. Fetch metadata and subtitles for the latest 5 videos
    # We limit to 5 to keep the GitHub Action fast and avoid rate limits
    subprocess.run([
        'yt-dlp', 
        '--write-auto-subs', 
        '--skip-download', 
        '--sub-format', 'vtt', 
        '--playlist-end', '5',
        '--output', 'temp_sub_%(id)s.%(ext)s', 
        CHANNEL_URL
    ])

    all_transcripts = []

    # 2. Process the downloaded .vtt files
    for file in os.listdir('.'):
        if file.startswith("temp_sub_") and file.endswith(".vtt"):
            video_id = file.replace("temp_sub_", "").split('.')[0]
            
            # Fetch video title using yt-dlp
            title_process = subprocess.run(
                ['yt-dlp', '--get-title', f'https://youtu.be/{video_id}'],
                capture_output=True, text=True
            )
            video_title = title_process.stdout.strip()

            print(f"Processing: {video_title} ({video_id})")
            
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
                
                lines_data = clean_vtt(raw_content)
                
                all_transcripts.append({
                    "id": video_id,
                    "title": video_title,
