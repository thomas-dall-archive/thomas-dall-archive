import os
import json
import subprocess
import re
from datetime import datetime

# Configuration: Targeting the LIVE streams tab specifically
CHANNEL_URL = "https://www.youtube.com/@PotatoofLife/streams"
OUTPUT_FILE = "primary_transcripts.json"

def clean_vtt(vtt_text):
    """Parses VTT to extract text and start times."""
    lines = vtt_text.splitlines()
    entries = []
    timestamp_re = re.compile(r'(\d{2}:\d{2}:\d{2})\.\d{3} -->')
    current_text = []
    current_time = "00:00:00"
    
    for line in lines:
        if "-->" in line:
            if current_text:
                text_content = " ".join(current_text).strip()
                if text_content:
                    h, m, s = map(int, current_time.split(':'))
                    total_seconds = h * 3600 + m * 60 + s
                    entries.append({
                        "time": current_time,
                        "seconds": total_seconds,
                        "text": text_content
                    })
                current_text = []
            match = timestamp_re.search(line)
            if match:
                current_time = match.group(1)
        elif not any(x in line for x in ["WEBVTT", "Kind:", "Language:"]) and line.strip():
            clean_line = re.sub(r'<[^>]*>', '', line)
            if clean_line.strip():
                current_text.append(clean_line.strip())
    return entries

def run_sync():
    print(f"--- Starting Primary Transcript Sync: {datetime.now()} ---")
    
    # 1. Fetch metadata and subtitles for the latest 5 LIVE streams
    # Added user-agent and player-client to look more like a browser
    subprocess.run([
        'yt-dlp', 
        '--write-auto-subs', 
        '--skip-download', 
        '--sub-format', 'vtt', 
        '--playlist-end', '5',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        '--extractor-args', 'youtube:player_client=web',
        '--output', 'temp_sub_%(id)s.%(ext)s', 
        CHANNEL_URL
    ])

    all_transcripts = []

    # 2. Process the downloaded .vtt files
    for file in os.listdir('.'):
        if file.startswith("temp_sub_") and file.endswith(".vtt"):
            video_id = file.replace("temp_sub_", "").split('.')[0]
            
            # Fetch video title
            title_process = subprocess.run(
                ['yt-dlp', '--get-title', f'https://youtu.be/{video_id}'],
                capture_output=True, text=True
            )
            video_title = title_process.stdout.strip()

            print(f"Processing Live Stream: {video_title} ({video_id})")
            
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
                lines_data = clean_vtt(raw_content)
                all_transcripts.append({
                    "id": video_id,
                    "title": video_title,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "lines": lines_data
                })
            except Exception as e:
                print(f"Error processing {file}: {e}")
            os.remove(file)

    # 3. Save the results
    if all_transcripts:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_transcripts, f, indent=2)
        print(f"Success: {OUTPUT_FILE} updated with data from LIVE tab.")
    else:
        print("No new transcripts found. Note: YouTube takes ~24hrs to generate auto-subs for lives.")

if __name__ == "__main__":
    run_sync()
